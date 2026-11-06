from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q

from workOrder.models import DailyEmployee


def _number(value):
    return float(value or 0)


class Command(BaseCommand):
    help = "Backfill DailyEmployee.emp_rate from payout for hourly rows without production items."

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Write the calculated emp_rate values. Without this flag the command is a dry run.",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Print every row that would be updated.",
        )

    def handle(self, *args, **options):
        apply_changes = options["apply"]
        verbose = options["verbose"]

        candidates = (
            DailyEmployee.objects.filter(
                Q(emp_rate__isnull=True) | Q(emp_rate=0),
                DailyID__dailyitem__isnull=True,
            )
            .select_related("DailyID", "EmployeeID")
            .order_by("DailyID__day", "id")
        )

        changes = []
        no_hours = []
        no_source = []

        for row in candidates.iterator():
            regular_hours = _number(row.regular_hours)
            overtime_hours = _number(row.ot_hour)
            double_time = _number(row.double_time)
            weighted_hours = regular_hours + (overtime_hours * 1.5) + (double_time * 2)

            payout = _number(row.payout)
            adjustments = _number(row.on_call) + _number(row.bonus) + _number(row.own_vehicle_pay)

            if weighted_hours <= 0:
                no_hours.append(row)
                continue

            if payout - adjustments <= 0:
                no_source.append(row)
                continue

            emp_rate = round((payout - adjustments) / weighted_hours, 2)
            if emp_rate <= 0:
                no_source.append(row)
                continue

            changes.append((row, emp_rate))

        self.stdout.write(
            "Candidates: %s | calculable: %s | no hours: %s | no payout source: %s"
            % (len(changes) + len(no_hours) + len(no_source), len(changes), len(no_hours), len(no_source))
        )

        for row in no_source:
            self.stdout.write(
                "  no source: DailyEmployee=%s Daily=%s date=%s employee=%s payout=%s"
                % (
                    row.id,
                    row.DailyID_id,
                    row.DailyID.day,
                    getattr(row.EmployeeID, "employeeID", None),
                    row.payout,
                )
            )

        if verbose:
            for row, emp_rate in changes:
                self.stdout.write(
                    "  update: DailyEmployee=%s Daily=%s date=%s employee=%s -> %s"
                    % (
                        row.id,
                        row.DailyID_id,
                        row.DailyID.day,
                        getattr(row.EmployeeID, "employeeID", None),
                        emp_rate,
                    )
                )

        if not apply_changes:
            self.stdout.write(self.style.WARNING("DRY RUN: no changes written."))
            return

        with transaction.atomic():
            for row, emp_rate in changes:
                row.emp_rate = emp_rate
                row.save(update_fields=["emp_rate"])

        self.stdout.write(self.style.SUCCESS("Updated %s DailyEmployee rows." % len(changes)))
