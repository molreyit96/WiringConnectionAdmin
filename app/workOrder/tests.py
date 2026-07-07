from django.test import TestCase, Client
from django.contrib.auth.models import User
from workOrder.models import logInAudit, Employee, Locations, period
from datetime import datetime, timedelta


class LoginAuditFilterTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.loc = Locations.objects.create(LocationID=1, name='Test Location')
        self.emp = Employee.objects.create(
            employeeID=1, first_name='Test', last_name='User',
            Location=self.loc, user=self.user, is_superAdmin=True
        )
        period.objects.create(periodID=1, periodYear=2026, fromDate='2026-01-01',
                              toDate='2026-12-31', payDate='2026-12-31', status=1)
        self.now = datetime.now()
        logInAudit.objects.create(operationDetail='D1', operationType='Login', created_date=self.now - timedelta(days=10), createdBy='admin', is_staff=True, is_supervisor=False, is_admin=True, is_superAdmin=True)
        logInAudit.objects.create(operationDetail='D2', operationType='Upload Orders', created_date=self.now - timedelta(days=5), createdBy='supervisor1', is_staff=False, is_supervisor=True, is_admin=False, is_superAdmin=False)
        logInAudit.objects.create(operationDetail='D3', operationType='Approve Payroll', created_date=self.now - timedelta(days=2), createdBy='staff1', is_staff=True, is_supervisor=False, is_admin=False, is_superAdmin=False)
        logInAudit.objects.create(operationDetail='D4', operationType='Reports', created_date=self.now - timedelta(hours=12), createdBy='admin', is_staff=True, is_supervisor=True, is_admin=True, is_superAdmin=True)
        logInAudit.objects.create(operationDetail='D5', operationType='Upload Payroll', created_date=self.now - timedelta(hours=6), createdBy='supervisor1', is_staff=False, is_supervisor=True, is_admin=False, is_superAdmin=False)
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

    def test_get_no_filters_returns_no_data(self):
        response = self.client.get('/login_audit/')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['applied'])
        self.assertEqual(response.context['log'].count(), 0)

    def test_filter_by_createdBy(self):
        response = self.client.post('/login_audit/', {'createdBy': 'admin'})
        self.assertEqual(response.context['log'].count(), 2)

    def test_filter_by_operationType(self):
        response = self.client.post('/login_audit/', {'operationType': 'Upload Orders'})
        self.assertEqual(response.context['log'].count(), 1)

    def test_filter_by_date_range(self):
        date_from = (self.now - timedelta(days=7)).strftime('%Y-%m-%d')
        date_to = self.now.strftime('%Y-%m-%d')
        response = self.client.post('/login_audit/', {'date_from': date_from, 'date_to': date_to})
        self.assertEqual(response.context['log'].count(), 4)

    def test_filter_by_is_supervisor(self):
        response = self.client.post('/login_audit/', {'is_supervisor': '1'})
        self.assertEqual(response.context['log'].count(), 3)

    def test_filter_by_is_admin(self):
        response = self.client.post('/login_audit/', {'is_admin': '1'})
        self.assertEqual(response.context['log'].count(), 2)

    def test_filter_by_is_staff(self):
        response = self.client.post('/login_audit/', {'is_staff': '1'})
        self.assertEqual(response.context['log'].count(), 3)

    def test_filter_by_is_superAdmin(self):
        response = self.client.post('/login_audit/', {'is_superAdmin': '1'})
        self.assertEqual(response.context['log'].count(), 2)

    def test_combined_filters(self):
        response = self.client.post('/login_audit/', {'createdBy': 'admin', 'is_superAdmin': '1'})
        self.assertEqual(response.context['log'].count(), 2)

    def test_combined_date_and_operation(self):
        date_from = (self.now - timedelta(days=3)).strftime('%Y-%m-%d')
        response = self.client.post('/login_audit/', {'date_from': date_from, 'operationType': 'Approve Payroll'})
        self.assertEqual(response.context['log'].count(), 1)

    def test_filter_no_results(self):
        response = self.client.post('/login_audit/', {'createdBy': 'ghost'})
        self.assertEqual(response.context['log'].count(), 0)

    def test_selects_context_populated(self):
        response = self.client.get('/login_audit/')
        self.assertIsNotNone(response.context.get('operationTypes'))
        self.assertIsNotNone(response.context.get('createdByList'))

    def test_selected_values_persist(self):
        response = self.client.post('/login_audit/', {'operationType': 'Reports', 'createdBy': 'admin'})
        self.assertEqual(response.context['selectOperationType'], 'Reports')
        self.assertEqual(response.context['selectCreatedBy'], 'admin')

    def test_filter_with_date_to_only(self):
        date_to = (self.now - timedelta(days=3)).strftime('%Y-%m-%d')
        response = self.client.post('/login_audit/', {'date_to': date_to})
        self.assertEqual(response.context['log'].count(), 2)

    def test_filter_with_date_from_only(self):
        date_from = (self.now - timedelta(days=3)).strftime('%Y-%m-%d')
        response = self.client.post('/login_audit/', {'date_from': date_from})
        self.assertEqual(response.context['log'].count(), 3)
