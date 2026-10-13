from datetime import date, datetime

from django.contrib.auth.models import User
from django.test import TestCase

from workOrder.models import Locations, period
from .models import DailyMob, DailyMobStatusAudit


class SendPayrollStatusGuardTests(TestCase):
    """send_payroll must only (re)send Draft (1) or Rejected (5) dailies."""

    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='x')
        self.client.force_login(self.user)

        self.location = Locations.objects.create(LocationID=1, name='Loc 1')
        self.period = period.objects.create(
            periodID=1,
            periodYear=2026,
            fromDate=date(2026, 8, 24),
            toDate=date(2026, 9, 6),
            payDate=date(2026, 9, 11),
            status=1,
        )

    def _make_daily(self, status, crew):
        return DailyMob.objects.create(
            crew=crew,
            Location=self.location,
            Period=self.period,
            day=date(2026, 8, 27),
            Status=status,
            created_by='tester',
            created_date=datetime.now(),
        )

    def test_approved_daily_is_not_reverted_to_sent(self):
        daily = self._make_daily(status=4, crew=1)
        daily.approved_by = 'sup'
        daily.approved_date = datetime.now()
        daily.save()

        self.client.get('/mobile/send_payroll/{}/1'.format(daily.id))

        daily.refresh_from_db()
        self.assertEqual(daily.Status, 4)
        self.assertEqual(daily.approved_by, 'sup')

    def test_rejected_daily_can_be_resent(self):
        daily = self._make_daily(status=5, crew=2)
        self.client.get('/mobile/send_payroll/{}/1'.format(daily.id))
        daily.refresh_from_db()
        self.assertEqual(daily.Status, 2)

    def test_draft_daily_can_be_sent(self):
        daily = self._make_daily(status=1, crew=3)
        self.client.get('/mobile/send_payroll/{}/1'.format(daily.id))
        daily.refresh_from_db()
        self.assertEqual(daily.Status, 2)

    def test_deleted_and_pending_are_blocked(self):
        for status, crew in ((6, 4), (3, 5)):
            daily = self._make_daily(status=status, crew=crew)
            self.client.get('/mobile/send_payroll/{}/1'.format(daily.id))
            daily.refresh_from_db()
            self.assertEqual(daily.Status, status)


class DailyMobStatusAuditTests(TestCase):
    """The DB trigger records every status transition, with the app user when known."""

    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='x')
        self.client.force_login(self.user)

        self.location = Locations.objects.create(LocationID=1, name='Loc 1')
        self.period = period.objects.create(
            periodID=1,
            periodYear=2026,
            fromDate=date(2026, 8, 24),
            toDate=date(2026, 9, 6),
            payDate=date(2026, 9, 11),
            status=1,
        )

    def _make_daily(self, status, crew):
        return DailyMob.objects.create(
            crew=crew,
            Location=self.location,
            Period=self.period,
            day=date(2026, 8, 27),
            Status=status,
            created_by='tester',
            created_date=datetime.now(),
        )

    def test_insert_and_app_status_change_are_audited_with_app_user(self):
        daily = self._make_daily(status=1, crew=1)

        self.client.get('/mobile/send_payroll/{}/1'.format(daily.id))

        rows = list(
            DailyMobStatusAudit.objects.filter(dailymob_id=daily.id).order_by('id')
        )
        self.assertGreaterEqual(len(rows), 2)

        insert_row = rows[0]
        self.assertEqual(insert_row.operation, 'INSERT')
        self.assertEqual(insert_row.new_status, 1)

        change_row = rows[-1]
        self.assertEqual(change_row.operation, 'UPDATE')
        self.assertEqual(change_row.old_status, 1)
        self.assertEqual(change_row.new_status, 2)
        self.assertEqual(change_row.app_user, 'tester')

    def test_direct_orm_change_has_no_app_user(self):
        daily = self._make_daily(status=1, crew=2)

        daily.Status = 4
        daily.save()

        row = DailyMobStatusAudit.objects.filter(
            dailymob_id=daily.id, new_status=4
        ).order_by('-id').first()
        self.assertIsNotNone(row)
        self.assertEqual(row.old_status, 1)
        self.assertIsNone(row.app_user)
        self.assertIsNotNone(row.db_user)
