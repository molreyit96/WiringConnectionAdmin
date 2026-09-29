import os
import re
import shutil
import tempfile
from datetime import date
from unittest import mock

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings

from mobile.models import DailyMob, DailyMobDocs
from workOrder.models import Employee, Locations, period

# 1x1 transparent PNG
PNG_BYTES = (
    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06'
    b'\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05'
    b'\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
)

TEST_MEDIA_ROOT = tempfile.mkdtemp(prefix='wc-doc-upload-')


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class BulkUploadCompressedViewTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.loc = Locations.objects.create(LocationID=1, name='Test Location')
        Employee.objects.create(
            employeeID=1, first_name='Test', last_name='User',
            Location=self.loc, user=self.user, is_superAdmin=True
        )
        self.per = period.objects.create(
            periodID=1, periodYear=2026, fromDate='2026-01-01',
            toDate='2026-12-31', payDate='2026-12-31', status=1
        )
        self.daily = DailyMob.objects.create(
            crew=43, Location=self.loc, Period=self.per, day=date(2026, 9, 26)
        )
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

    def url(self, doc_type, daily=None):
        daily = daily or self.daily
        return f'/mobile/create_daily_docs_compressed/{daily.id}/4/{doc_type}'

    def post_file(self, name, content, doc_type=1):
        return self.client.post(
            self.url(doc_type),
            {
                'DailyID': str(self.daily.id),
                'docType': str(doc_type),
                'files': SimpleUploadedFile(name, content, content_type='application/octet-stream'),
            },
        )

    # ---------- GET ----------

    def test_get_maps_page(self):
        response = self.client.get(self.url(1))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['docType'], '1')
        self.assertEqual(response.context['max_upload_mb'], 25)
        self.assertContains(response, 'Add Maps')
        self.assertContains(response, 'wc-doc-grid')
        self.assertContains(response, 'section=docs&sub=maps')

    def test_get_pictures_page(self):
        response = self.client.get(self.url(2))
        self.assertContains(response, 'Add Pictures')
        self.assertContains(response, 'section=docs&sub=pictures')

    def test_get_material_page(self):
        response = self.client.get(self.url(3))
        self.assertContains(response, 'Add Material Backup')
        self.assertContains(response, 'section=docs&sub=material')

    def test_get_does_not_use_legacy_order_list_title(self):
        response = self.client.get(self.url(1))
        self.assertNotContains(response, '<title> Order List </title>')

    def test_get_advertises_allowed_types_and_cap(self):
        response = self.client.get(self.url(1))
        self.assertContains(response, 'accept=".pdf,.docx,.xlsx,.jpeg,.jpg,.png"')
        self.assertContains(response, 'up to 25 MB each')

    # ---------- POST ----------

    def test_post_creates_document(self):
        response = self.post_file('site-map.png', PNG_BYTES, doc_type=2)
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        self.assertEqual(payload['uploaded_count'], 1)
        self.assertEqual(payload['total_files'], 1)

        doc = DailyMobDocs.objects.get()
        self.assertEqual(doc.DailyID, self.daily)
        self.assertEqual(doc.docType, 2)
        self.assertEqual(doc.docName, 'site-map')
        self.assertEqual(doc.createdBy, 'testuser')

    def test_post_uses_url_doctype_over_post_data(self):
        response = self.client.post(
            self.url(3),
            {
                'DailyID': str(self.daily.id),
                'docType': '1',
                'files': SimpleUploadedFile('photo.png', PNG_BYTES),
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(DailyMobDocs.objects.get().docType, 3)

    def test_post_without_files_is_rejected(self):
        response = self.client.post(
            self.url(1), {'DailyID': str(self.daily.id), 'docType': '1'}
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()['success'])
        self.assertEqual(DailyMobDocs.objects.count(), 0)

    def test_post_rejects_disallowed_extension(self):
        response = self.post_file('payload.exe', b'MZ\x00\x00')
        self.assertEqual(response.status_code, 400)
        payload = response.json()
        self.assertFalse(payload['success'])
        self.assertIn('not allowed', payload['errors'])
        self.assertEqual(DailyMobDocs.objects.count(), 0)

    def test_post_rejects_oversized_file(self):
        with mock.patch('mobile.views.DOC_UPLOAD_MAX_BYTES', 10):
            response = self.post_file('huge.png', b'0' * 64)
        self.assertEqual(response.status_code, 400)
        self.assertIn('larger than', response.json()['errors'])
        self.assertEqual(DailyMobDocs.objects.count(), 0)

    def test_post_rejects_bad_doctype_in_url(self):
        response = self.client.post(
            self.url('abc'),
            {
                'DailyID': str(self.daily.id),
                'docType': '1',
                'files': SimpleUploadedFile('photo.png', PNG_BYTES),
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('Invalid document type', response.json()['errors'])
        self.assertEqual(DailyMobDocs.objects.count(), 0)

    def test_post_rejects_unknown_daily(self):
        response = self.client.post(
            self.url(1),
            {
                'DailyID': '999999',
                'docType': '1',
                'files': SimpleUploadedFile('photo.png', PNG_BYTES),
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('Invalid DailyID', response.json()['errors'])
        self.assertEqual(DailyMobDocs.objects.count(), 0)

    def test_validation_helper_returns_reason_or_none(self):
        from mobile.views import DOC_UPLOAD_MAX_BYTES, validate_doc_upload

        good = SimpleUploadedFile('plan.pdf', b'%PDF-1.4')
        self.assertIsNone(validate_doc_upload(good))

        bad_ext = SimpleUploadedFile('script.sh', b'echo hi')
        self.assertIn('not allowed', validate_doc_upload(bad_ext))

        big = SimpleUploadedFile('scan.png', b'0' * (DOC_UPLOAD_MAX_BYTES + 1))
        self.assertIn('larger than', validate_doc_upload(big))


class PwaFooterClearanceTests(TestCase):
    """The fixed bottom nav must not cover the end of a scrollable page.

    Regression guard for the Home rejected-dailies card sliding under the footer:
    every PWA page container carries wc-bottom-clear, and the token that drives
    that clearance (plus the sticky action bar) is declared in tokens.css.
    """

    PAGES_WITH_CLEARANCE = (
        'mobile/home.html',
        'mobile/crew.html',
        'mobile/dashboard.html',
        'mobile/create_daily_doc_compressed.html',
        'mobile/create_daily_emp.html',
        'mobile/create_daily_item.html',
        'mobile/orders_payroll.html',
        'mobile/update_daily_emp.html',
        'mobile/update_daily_item.html',
        'mobile/update_supervisor.html',
    )

    def _source(self, template_name):
        import os

        from django.conf import settings

        path = os.path.join(settings.BASE_DIR, 'templates', template_name)
        with open(path, encoding='utf-8') as fh:
            return fh.read()

    def test_every_pwa_page_container_has_bottom_clearance(self):
        for template_name in self.PAGES_WITH_CLEARANCE:
            with self.subTest(template=template_name):
                src = self._source(template_name)
                self.assertIn('wc-bottom-clear', src)
                self.assertNotIn('container pb-5 mb-4', src)

    def test_footer_height_token_declared_in_tokens(self):
        from django.conf import settings

        with open(
            settings.STATICFILES_DIRS[0] + '/mobile/css/tokens.css', encoding='utf-8'
        ) as fh:
            tokens = fh.read()
        self.assertIn('--wc-footer-h:', tokens)
        self.assertIn('padding-bottom: calc(var(--wc-footer-h)', tokens)
        self.assertIn('bottom: var(--wc-footer-h);', tokens)

    def test_home_collapse_is_driven_by_the_chip_row(self):
        src = self._source('mobile/home.html')
        self.assertIn('id="homeFilterLocRow"', src)
        self.assertIn("document.getElementById('homeFilterLocRow')", src)
        # Old magic thresholds must be gone.
        self.assertNotIn('if (y < 80)', src)
        self.assertNotIn('else if (y > 120)', src)


class AssetVersionTests(TestCase):
    """Static assets served to the PWA must carry a version token.

    STATIC_URL is not fingerprinted and nginx serves /static/ with
    `Cache-Control: max-age=2592000`, so an unversioned URL keeps serving the
    old file for 30 days. Every `{% static %}` in the PWA shell therefore
    needs a `?v={{ ASSET_VERSION }}` suffix, and the service worker cache
    name has to move with it so stale responses are purged on activation.

    Desktop templates are intentionally out of scope: they share style.css and
    the logo, and versioning them is a separate decision.
    """

    PWA_SHELL = 'mobile/index.html'
    VERSION_SUFFIX = '?v={{ ASSET_VERSION }}'

    # Templates that must be fully versioned. employee_list.html and
    # employee_submitted_list.html are deliberately absent: they extend the
    # desktop base.html and load the shared logo.
    PWA_TEMPLATES = (
        'mobile/index.html',
        'mobile/approved_dailies.html',
        'mobile/approve_timesheet_2.html',
        'mobile/create_daily_emp.html',
        'mobile/create_daily_item.html',
        'mobile/orders_payroll.html',
        'mobile/supervisor_list.html',
        'mobile/supervisor_timesheet.html',
        'mobile/timesheet.html',
        'mobile/update_daily_emp.html',
        'mobile/update_daily_item.html',
        'mobile/update_supervisor.html',
        'mobile/crew.html',
    )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        from django.conf import settings

        cls.templates_dir = os.path.join(settings.BASE_DIR, 'templates')
        cls.static_dir = settings.STATICFILES_DIRS[0]

    def _read_template(self, name):
        with open(os.path.join(self.templates_dir, name), encoding='utf-8') as fh:
            return fh.read()

    def _strip_comments(self, src):
        return re.sub(r'{%\s*comment\s*%}.*?{%\s*endcomment\s*%}', '', src, flags=re.S)

    def _static_refs(self, src):
        """Yield (asset, snippet) for each active {% static %} in src.

        The snippet must include the trailing `?v={{ ASSET_VERSION }}` when
        present, so the pattern accepts an optional Django variable and stops
        at the first quote or tag boundary. Handling the variable explicitly
        matters: a bare [^"'>] class would stop at the '{' of {{ and silently
        miss every versioned ref.
        """
        tail = r"(?:\?v=\{\{\s*ASSET_VERSION\s*\}\})?[^\"'<>]*"
        pattern = r"{%\s*static\s+'([^']+)'\s*%}" + tail
        for match in re.finditer(pattern, src):
            yield match.group(1), match.group(0).strip()

    def test_every_pwa_static_ref_is_versioned(self):
        total = 0
        for name in self.PWA_TEMPLATES:
            src = self._strip_comments(self._read_template(name))
            for asset, snippet in self._static_refs(src):
                total += 1
                with self.subTest(template=name, asset=asset):
                    self.assertIn(
                        self.VERSION_SUFFIX,
                        snippet,
                        f'{name} loads {asset} without a version token; the '
                        f'browser would keep the cached copy for 30 days',
                    )
        self.assertGreater(total, 0, 'no static refs found; test would pass vacuously')

    def test_pwa_shell_is_itself_versioned(self):
        src = self._strip_comments(self._read_template(self.PWA_SHELL))
        refs = list(self._static_refs(src))
        self.assertGreaterEqual(len(refs), 4)
        for asset, snippet in refs:
            with self.subTest(asset=asset):
                self.assertIn(self.VERSION_SUFFIX, snippet)

    def test_no_double_versioning(self):
        for name in self.PWA_TEMPLATES:
            src = self._read_template(name)
            with self.subTest(template=name):
                self.assertNotIn('?v={{ ASSET_VERSION }}?v=', src)

    def test_service_worker_cache_name_matches_asset_version(self):
        from django.conf import settings

        with open(os.path.join(self.static_dir, 'pwa', 'sw.js'), encoding='utf-8') as fh:
            sw = fh.read()
        self.assertIn(f"'wcapp-{settings.ASSET_VERSION}'", sw)

    def test_asset_version_is_declared(self):
        from django.conf import settings

        self.assertTrue(settings.ASSET_VERSION)
        self.assertRegex(settings.ASSET_VERSION, r'^\d{4}-\d{2}-\d{2}-\d+$')

    def test_desktop_templates_stay_unversioned(self):
        """Scope guard: shared assets must not be versioned on desktop.

        If someone versioned these, the desktop UI would start busting its
        cache for style.css and the logo too, which was an explicit decision
        to leave out of this change.
        """
        for name in ('mobile/employee_list.html', 'mobile/employee_submitted_list.html'):
            src = self._read_template(name)
            with self.subTest(template=name):
                self.assertIn("{% static 'images/WC_logo.jpg'%}", src)
                self.assertNotIn(self.VERSION_SUFFIX, src)

    def test_font_subset_url_is_documented_as_manual(self):
        """The icon font is referenced from CSS, not a template.

        No test can catch a stale woff2 there, so the hazard is recorded in
        the CSS itself and asserted here so the note cannot be deleted silently.
        """
        with open(
            os.path.join(self.static_dir, 'mobile', 'css', 'fa-subset.css'),
            encoding='utf-8',
        ) as fh:
            css = fh.read()
        self.assertIn('fa-solid-subset.woff2', css)
        self.assertIn('ASSET_VERSION', css)
