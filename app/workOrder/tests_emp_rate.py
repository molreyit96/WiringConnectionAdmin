from datetime import date, datetime
from io import StringIO

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import Client, TestCase

from mobile.models import DailyMob, DailyMobEmployee, DailyMobItem
from mobile.views import update_ptp_Emp as mobile_update_ptp
from workOrder.models import (
    Daily,
    DailyAudit,
    DailyEmployee,
    DailyItem,
    Employee,
    Locations,
    logInAudit,
    item,
    itemPrice,
    period,
    workOrder,
)
from workOrder.views import _payroll_close_issues
from workOrder.views import update_ptp_Emp as web_update_ptp


class EmpRateSnapshotBase(TestCase):
    """Shared fixture for payroll snapshot tests."""

    def setUp(self):
        self.user = User.objects.create_user(username="emp_rate_user", password="testpass123")
        self.loc = Locations.objects.create(LocationID=1, name="Gardena")
        self.emp = Employee.objects.create(
            employeeID=1001,
            first_name="Rate",
            last_name="Snapshot",
            hourly_rate="25.00",
            Location=self.loc,
            user=self.user,
        )
        self.per = period.objects.create(
            periodID=1,
            periodYear=2026,
            fromDate=date(2026, 1, 1),
            toDate=date(2026, 1, 14),
            payDate=date(2026, 1, 16),
            weekRange="W01-02",
            status=1,
        )
        self.wo = workOrder.objects.create(
            prismID="PRISM-1",
            workOrderId="WO-1",
            PO="PO-1",
            JobAddress="100 Main St",
            created_date=datetime(2026, 1, 1),
        )
        self.daily = Daily.objects.create(
            crew=1,
            Location=self.loc,
            Period=self.per,
            day=date(2026, 1, 5),
            woID=self.wo,
        )

    def add_item(self, daily=None, payout="5.00"):
        daily = daily or self.daily
        catalog_item = item.objects.create(
            itemID="ITEM-%s" % daily.id,
            name="Test item",
            created_date=date(2026, 1, 1),
        )
        price = itemPrice.objects.create(
            item=catalog_item,
            location=self.loc,
            price="10.00",
            emp_payout=payout,
        )
        DailyItem.objects.create(
            DailyID=daily,
            itemID=price,
            quantity=2,
            price=10.0,
            total=10.0,
            emp_payout=float(payout),
        )
        return price

    def add_mobile_item(self, daily_mob, payout="5.00"):
        price = self.add_item(payout=payout)
        DailyMobItem.objects.create(
            DailyID=daily_mob,
            itemID=price,
            quantity=2,
            price=10.0,
            total=10.0,
            emp_payout=float(payout),
        )


class WebPayrollSnapshotTests(EmpRateSnapshotBase):
    def test_update_ptp_uses_snapshot_instead_of_live_hourly_rate(self):
        daily_emp = DailyEmployee.objects.create(
            DailyID=self.daily,
            EmployeeID=self.emp,
            per_to_pay=100,
            regular_hours=8,
            ot_hour=2,
            double_time=1,
            emp_rate=18.57,
        )

        web_update_ptp(self.daily.id, False)

        daily_emp.refresh_from_db()
        self.assertAlmostEqual(daily_emp.rt_pay, 148.56, places=2)
        self.assertAlmostEqual(daily_emp.ot_pay, 55.71, places=2)
        self.assertAlmostEqual(daily_emp.dt_pay, 37.14, places=2)
        self.assertAlmostEqual(daily_emp.payout, 241.41, places=2)
        self.assertAlmostEqual(daily_emp.emp_rate, 18.57, places=2)

    def test_changing_live_rate_does_not_change_existing_payroll(self):
        daily_emp = DailyEmployee.objects.create(
            DailyID=self.daily,
            EmployeeID=self.emp,
            per_to_pay=100,
            regular_hours=8,
            ot_hour=0,
            double_time=0,
            emp_rate=18.57,
        )

        self.emp.hourly_rate = "30.00"
        self.emp.save(update_fields=["hourly_rate"])

        web_update_ptp(self.daily.id, False)

        daily_emp.refresh_from_db()
        self.assertAlmostEqual(daily_emp.rt_pay, 148.56, places=2)
        self.assertAlmostEqual(daily_emp.payout, 148.56, places=2)
        self.assertAlmostEqual(daily_emp.emp_rate, 18.57, places=2)

    def test_item_daily_must_not_overwrite_snapshot_with_zero(self):
        daily_emp = DailyEmployee.objects.create(
            DailyID=self.daily,
            EmployeeID=self.emp,
            per_to_pay=100,
            regular_hours=8,
            ot_hour=0,
            double_time=0,
            emp_rate=18.57,
        )
        self.add_item(self.daily)

        web_update_ptp(self.daily.id, False)

        daily_emp.refresh_from_db()
        self.assertAlmostEqual(daily_emp.emp_rate, 18.57, places=2)

    def test_new_item_daily_then_item_deleted_must_still_pay_snapshot(self):
        daily_emp = DailyEmployee.objects.create(
            DailyID=self.daily,
            EmployeeID=self.emp,
            per_to_pay=100,
            regular_hours=8,
            ot_hour=0,
            double_time=0,
            emp_rate=18.57,
        )
        self.add_item(self.daily)
        web_update_ptp(self.daily.id, False)

        DailyItem.objects.filter(DailyID=self.daily).delete()
        web_update_ptp(self.daily.id, False)

        daily_emp.refresh_from_db()
        self.assertAlmostEqual(daily_emp.payout, 148.56, places=2)

    def test_missing_snapshot_falls_back_to_live_rate(self):
        daily_emp = DailyEmployee.objects.create(
            DailyID=self.daily,
            EmployeeID=self.emp,
            per_to_pay=100,
            regular_hours=8,
            ot_hour=0,
            double_time=0,
            emp_rate=None,
        )

        web_update_ptp(self.daily.id, False)

        daily_emp.refresh_from_db()
        self.assertAlmostEqual(daily_emp.emp_rate, 25.00, places=2)


class PayrollCloseValidationTests(EmpRateSnapshotBase):
    def test_close_issues_detect_missing_rate_with_hours(self):
        daily_emp = DailyEmployee.objects.create(
            DailyID=self.daily,
            EmployeeID=self.emp,
            regular_hours=8,
            emp_rate=None,
        )

        self.assertTrue(_payroll_close_issues(self.per))

        daily_emp.emp_rate = 25.00
        daily_emp.save(update_fields=["emp_rate"])

        self.assertFalse(_payroll_close_issues(self.per))

    def test_close_issues_detect_missing_rate_with_items_only(self):
        daily_emp = DailyEmployee.objects.create(
            DailyID=self.daily,
            EmployeeID=self.emp,
            emp_rate=0,
        )
        self.add_item(self.daily)

        self.assertTrue(_payroll_close_issues(self.per))

        daily_emp.emp_rate = 25.00
        daily_emp.save(update_fields=["emp_rate"])

        self.assertFalse(_payroll_close_issues(self.per))


class MobilePayrollSnapshotTests(EmpRateSnapshotBase):
    def setUp(self):
        super().setUp()
        self.daily_mob = DailyMob.objects.create(
            crew=1,
            Location=self.loc,
            Period=self.per,
            day=date(2026, 1, 5),
            woID=self.wo,
        )

    def test_mobile_update_ptp_uses_snapshot_instead_of_live_hourly_rate(self):
        daily_emp = DailyMobEmployee.objects.create(
            DailyID=self.daily_mob,
            EmployeeID=self.emp,
            per_to_pay=100,
            regular_hours=8,
            ot_hour=2,
            double_time=1,
            emp_rate=18.57,
        )

        mobile_update_ptp(self.daily_mob.id, False)

        daily_emp.refresh_from_db()
        self.assertAlmostEqual(daily_emp.rt_pay, 148.56, places=2)
        self.assertAlmostEqual(daily_emp.ot_pay, 55.71, places=2)
        self.assertAlmostEqual(daily_emp.dt_pay, 37.14, places=2)
        self.assertAlmostEqual(daily_emp.payout, 241.41, places=2)
        self.assertAlmostEqual(daily_emp.emp_rate, 18.57, places=2)

    def test_mobile_new_item_daily_then_item_deleted_must_still_pay_snapshot(self):
        daily_emp = DailyMobEmployee.objects.create(
            DailyID=self.daily_mob,
            EmployeeID=self.emp,
            per_to_pay=100,
            regular_hours=8,
            ot_hour=0,
            double_time=0,
            emp_rate=18.57,
        )
        self.add_mobile_item(self.daily_mob)
        mobile_update_ptp(self.daily_mob.id, False)

        DailyMobItem.objects.filter(DailyID=self.daily_mob).delete()
        mobile_update_ptp(self.daily_mob.id, False)

        daily_emp.refresh_from_db()
        self.assertAlmostEqual(daily_emp.payout, 148.56, places=2)

    def test_mobile_item_daily_must_not_overwrite_snapshot_with_zero(self):
        daily_emp = DailyMobEmployee.objects.create(
            DailyID=self.daily_mob,
            EmployeeID=self.emp,
            per_to_pay=100,
            regular_hours=8,
            ot_hour=0,
            double_time=0,
            emp_rate=18.57,
        )
        self.add_mobile_item(self.daily_mob)

        mobile_update_ptp(self.daily_mob.id, False)

        daily_emp.refresh_from_db()
        self.assertAlmostEqual(daily_emp.emp_rate, 18.57, places=2)


class CreateDailyEmployeeSnapshotTests(EmpRateSnapshotBase):
    def setUp(self):
        super().setUp()
        self.client = Client()
        self.client.login(username="emp_rate_user", password="testpass123")
        self.rate_employee = Employee.objects.create(
            employeeID=2002,
            first_name="New",
            last_name="Hire",
            hourly_rate="18.57",
            Location=self.loc,
        )

    def _form_payload(self):
        return {
            "EmployeeID": self.rate_employee.employeeID,
            "per_to_pay": "100",
            "on_call": "0",
            "bonus": "0",
            "start_time": "800",
            "start_lunch_time": "1200",
            "end_lunch_time": "1230",
            "end_time": "1700",
            "total_hours": "0",
            "own_vehicle_pay": "0",
        }

    def test_web_create_daily_emp_snapshots_hourly_rate(self):
        payload = self._form_payload()
        payload["DailyID"] = self.daily.id

        response = self.client.post(
            "/create_daily_emp/%s/%s" % (self.daily.id, self.loc.LocationID),
            payload,
        )

        self.assertEqual(response.status_code, 302)
        created = DailyEmployee.objects.get(DailyID=self.daily, EmployeeID=self.rate_employee)
        self.assertAlmostEqual(created.emp_rate, 18.57, places=2)

    def test_mobile_create_daily_emp_snapshots_hourly_rate(self):
        daily_mob = DailyMob.objects.create(
            crew=1,
            Location=self.loc,
            Period=self.per,
            day=date(2026, 1, 5),
            woID=self.wo,
        )
        payload = self._form_payload()
        payload["DailyID"] = daily_mob.id

        response = self.client.post(
            "/mobile/create_daily_emp/%s/%s" % (daily_mob.id, self.loc.LocationID),
            payload,
        )

        self.assertEqual(response.status_code, 302)
        created = DailyMobEmployee.objects.get(DailyID=daily_mob, EmployeeID=self.rate_employee)
        self.assertAlmostEqual(created.emp_rate, 18.57, places=2)

    def test_mobile_create_daily_emp_sup_must_snapshot_hourly_rate(self):
        daily_mob = DailyMob.objects.create(
            crew=1,
            Location=self.loc,
            Period=self.per,
            day=date(2026, 1, 5),
            woID=self.wo,
        )
        payload = self._form_payload()
        payload["DailyID"] = daily_mob.id

        response = self.client.post(
            "/mobile/create_daily_emp_sup/%s/%s" % (daily_mob.id, self.loc.LocationID),
            payload,
        )

        self.assertEqual(response.status_code, 302)
        created = DailyMobEmployee.objects.get(DailyID=daily_mob, EmployeeID=self.rate_employee)
        self.assertAlmostEqual(created.emp_rate, 18.57, places=2)

    def test_mobile_update_daily_emp_must_refresh_snapshot_on_employee_change(self):
        daily_mob = DailyMob.objects.create(
            crew=1,
            Location=self.loc,
            Period=self.per,
            day=date(2026, 1, 5),
            woID=self.wo,
        )
        daily_emp = DailyMobEmployee.objects.create(
            DailyID=daily_mob,
            EmployeeID=self.emp,
            per_to_pay=100,
            emp_rate=25.00,
        )
        payload = self._form_payload()
        payload["DailyID"] = daily_mob.id

        response = self.client.post(
            "/mobile/update_daily_emp/%s/%s" % (daily_emp.id, self.loc.LocationID),
            payload,
        )

        self.assertEqual(response.status_code, 302)
        daily_emp.refresh_from_db()
        self.assertAlmostEqual(daily_emp.emp_rate, 18.57, places=2)

    def test_web_update_daily_emp_refreshes_snapshot_on_employee_change(self):
        new_employee = Employee.objects.create(
            employeeID=3003,
            first_name="Changed",
            last_name="Employee",
            hourly_rate="30.00",
            Location=self.loc,
        )
        daily_emp = DailyEmployee.objects.create(
            DailyID=self.daily,
            EmployeeID=self.emp,
            per_to_pay=100,
            emp_rate=18.57,
        )
        payload = self._form_payload()
        payload["DailyID"] = self.daily.id
        payload["EmployeeID"] = new_employee.employeeID

        response = self.client.post(
            "/update_daily_emp/%s/%s" % (daily_emp.id, self.loc.LocationID),
            payload,
        )

        self.assertEqual(response.status_code, 302)
        daily_emp.refresh_from_db()
        self.assertEqual(daily_emp.EmployeeID_id, new_employee.employeeID)
        self.assertAlmostEqual(daily_emp.emp_rate, 30.00, places=2)

    def test_web_create_daily_emp_rejects_employee_without_hourly_rate(self):
        no_rate_employee = Employee.objects.create(
            employeeID=4004,
            first_name="No",
            last_name="Rate",
            Location=self.loc,
        )
        payload = self._form_payload()
        payload["DailyID"] = self.daily.id
        payload["EmployeeID"] = no_rate_employee.employeeID

        response = self.client.post(
            "/create_daily_emp/%s/%s" % (self.daily.id, self.loc.LocationID),
            payload,
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            DailyEmployee.objects.filter(DailyID=self.daily, EmployeeID=no_rate_employee).exists()
        )

    def test_web_closed_period_blocks_employee_update_and_audits(self):
        daily_emp = DailyEmployee.objects.create(
            DailyID=self.daily,
            EmployeeID=self.rate_employee,
            per_to_pay=100,
            emp_rate=18.57,
        )
        self.per.status = 3
        self.per.save(update_fields=["status"])
        payload = self._form_payload()
        payload["DailyID"] = self.daily.id

        response = self.client.post(
            "/update_daily_emp/%s/%s" % (daily_emp.id, self.loc.LocationID),
            payload,
        )

        self.assertEqual(response.status_code, 403)
        self.assertTrue(
            DailyAudit.objects.filter(
                DailyID=self.daily, operationType="Blocked-ClosedPeriod"
            ).exists()
        )

    def test_mobile_closed_period_blocks_employee_update_and_audits(self):
        daily_mob = DailyMob.objects.create(
            crew=1,
            Location=self.loc,
            Period=self.per,
            day=date(2026, 1, 5),
            woID=self.wo,
        )
        daily_emp = DailyMobEmployee.objects.create(
            DailyID=daily_mob,
            EmployeeID=self.rate_employee,
            per_to_pay=100,
            emp_rate=18.57,
        )
        self.per.status = 3
        self.per.save(update_fields=["status"])
        payload = self._form_payload()
        payload["DailyID"] = daily_mob.id

        response = self.client.post(
            "/mobile/update_daily_emp/%s/%s" % (daily_emp.id, self.loc.LocationID),
            payload,
        )

        self.assertEqual(response.status_code, 403)
        self.assertTrue(
            logInAudit.objects.filter(
                Period=self.per, operationType="Blocked-ClosedPeriod"
            ).exists()
        )

    def test_web_close_payroll_blocks_missing_rate(self):
        DailyEmployee.objects.create(
            DailyID=self.daily,
            EmployeeID=self.rate_employee,
            regular_hours=8,
            emp_rate=None,
        )

        response = self.client.post("/close_payroll/%s" % self.per.id)

        self.assertEqual(response.status_code, 302)
        self.per.refresh_from_db()
        self.assertEqual(self.per.status, 1)

    def test_web_open_period_audits_reopen(self):
        self.per.status = 3
        self.per.save(update_fields=["status"])

        response = self.client.get("/open_period/%s" % self.per.id)

        self.assertEqual(response.status_code, 302)
        self.per.refresh_from_db()
        self.assertEqual(self.per.status, 1)
        self.assertTrue(
            logInAudit.objects.filter(
                Period=self.per, operationType="Reopen Period"
            ).exists()
        )

class FixEmpRateCommandTests(EmpRateSnapshotBase):
    def test_dry_run_does_not_write_and_apply_backfills_from_payout(self):
        daily_emp = DailyEmployee.objects.create(
            DailyID=self.daily,
            EmployeeID=self.emp,
            regular_hours=8,
            payout=148.56,
            emp_rate=None,
        )

        call_command("fix_emp_rate", stdout=StringIO())
        daily_emp.refresh_from_db()
        self.assertIsNone(daily_emp.emp_rate)

        call_command("fix_emp_rate", "--apply", stdout=StringIO())
        daily_emp.refresh_from_db()
        self.assertAlmostEqual(daily_emp.emp_rate, 18.57, places=2)

    def test_rows_with_items_are_not_touched(self):
        daily_emp = DailyEmployee.objects.create(
            DailyID=self.daily,
            EmployeeID=self.emp,
            regular_hours=8,
            payout=148.56,
            emp_rate=0,
        )
        self.add_item(self.daily)

        call_command("fix_emp_rate", "--apply", stdout=StringIO())

        daily_emp.refresh_from_db()
        self.assertEqual(daily_emp.emp_rate, 0)

    def test_rows_without_hours_or_payout_source_remain_unchanged(self):
        second_emp = Employee.objects.create(
            employeeID=5005,
            first_name="Second",
            last_name="Employee",
            hourly_rate="20.00",
            Location=self.loc,
        )
        no_hours = DailyEmployee.objects.create(
            DailyID=self.daily,
            EmployeeID=self.emp,
            regular_hours=0,
            payout=100,
            emp_rate=None,
        )
        no_source = DailyEmployee.objects.create(
            DailyID=self.daily,
            EmployeeID=second_emp,
            regular_hours=8,
            payout=0,
            emp_rate=None,
        )

        call_command("fix_emp_rate", "--apply", stdout=StringIO())

        no_hours.refresh_from_db()
        no_source.refresh_from_db()
        self.assertIsNone(no_hours.emp_rate)
        self.assertIsNone(no_source.emp_rate)
