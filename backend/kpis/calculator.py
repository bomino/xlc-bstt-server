"""
KPI Calculator for BSTT Compliance Dashboard.
Ported from the Streamlit version.
"""
from datetime import date, timedelta
from decimal import Decimal
from django.db.models import QuerySet, Sum, Count, Avg, F, Case, When, IntegerField, Max, Value
from django.db.models.functions import Concat
from django.conf import settings


def get_week_display_date(week_year: int, week_number: int) -> date:
    """
    Get Sunday date for a given ISO week (for display purposes).

    Args:
        week_year: ISO year
        week_number: ISO week number (1-53)

    Returns:
        date object representing Sunday of that week
    """
    # ISO week starts Monday (day 1), Sunday is day 7
    # January 4th is always in week 1
    jan4 = date(week_year, 1, 4)
    iso_year_start = jan4 - timedelta(days=jan4.isoweekday() - 1)  # Monday of week 1
    return iso_year_start + timedelta(weeks=week_number - 1, days=6)  # Sunday of that week


class KPICalculator:
    """Calculate all compliance KPIs from a TimeEntry queryset."""

    def __init__(self, queryset: QuerySet):
        self.qs = queryset
        self._cache = {}

    def calculate_all(self) -> dict:
        """Calculate all KPIs and return as dictionary."""
        return {
            **self.compliance_kpis(),
            **self.volume_kpis(),
            **self.efficiency_kpis(),
        }

    def compliance_kpis(self) -> dict:
        """Calculate compliance-related KPIs."""
        total = self.qs.count()

        if total == 0:
            return {
                'finger_rate': 0.0,
                'provisional_rate': 0.0,
                'write_in_rate': 0.0,
                'missing_co_rate': 0.0,
                'manual_rate': 0.0,
                'biometric_compliance': 0.0,
                'auto_clock_rate': 0.0,
                'exception_rate': 0.0,
            }

        # Count by entry type
        entry_counts = dict(
            self.qs.values('entry_type')
            .annotate(count=Count('id'))
            .values_list('entry_type', 'count')
        )

        finger = entry_counts.get('Finger', 0)
        provisional = entry_counts.get('Provisional Entry', 0)
        write_in = entry_counts.get('Write-In', 0)
        missing_co = entry_counts.get('Missing c/o', 0)
        manual = provisional + write_in + missing_co

        # Rates as percentages
        finger_rate = round(finger / total * 100, 1)
        provisional_rate = round(provisional / total * 100, 2)
        write_in_rate = round(write_in / total * 100, 2)
        missing_co_rate = round(missing_co / total * 100, 2)
        manual_rate = round(manual / total * 100, 1)

        # Biometric compliance = finger rate
        biometric_compliance = finger_rate

        # Auto clock rate (entries with method = 'Finger' for both in/out)
        auto_clocks = self.qs.filter(
            clock_in_method='Finger',
            clock_out_method='Finger'
        ).count()
        auto_clock_rate = round(auto_clocks / total * 100, 1) if total > 0 else 0.0

        # Exception rate = non-finger entries
        exception_rate = round((total - finger) / total * 100, 1)

        return {
            'finger_rate': finger_rate,
            'provisional_rate': provisional_rate,
            'write_in_rate': write_in_rate,
            'missing_co_rate': missing_co_rate,
            'manual_rate': manual_rate,
            'biometric_compliance': biometric_compliance,
            'auto_clock_rate': auto_clock_rate,
            'exception_rate': exception_rate,
        }

    def volume_kpis(self) -> dict:
        """Calculate volume-related KPIs."""
        agg = self.qs.aggregate(
            total_entries=Count('id'),
            total_hours=Sum('total_hours'),
            total_reg_hours=Sum('reg_hours'),
            total_ot_hours=Sum('ot_hours'),
            total_dt_hours=Sum('dt_hours'),
            total_hol_hours=Sum('hol_wrk_hours'),
            unique_employees=Count('applicant_id', distinct=True),
            unique_offices=Count('xlc_operation', distinct=True),
            # Count distinct ISO weeks (week_year + week_number) to properly
            # align Martinsburg Saturday endings with other offices' Sunday endings
            unique_weeks=Count(
                Concat('week_year', Value('-'), 'week_number'),
                distinct=True
            ),
        )

        total_hours = float(agg['total_hours'] or 0)
        total_entries = agg['total_entries'] or 0
        unique_employees = agg['unique_employees'] or 0
        unique_weeks = agg['unique_weeks'] or 1

        # Average hours per entry
        avg_hours_per_entry = round(total_hours / total_entries, 2) if total_entries > 0 else 0.0

        # Average hours per employee per week
        avg_hours_per_emp_week = round(
            total_hours / unique_employees / unique_weeks, 1
        ) if unique_employees > 0 and unique_weeks > 0 else 0.0

        # Entries per employee
        entries_per_employee = round(
            total_entries / unique_employees, 1
        ) if unique_employees > 0 else 0.0

        # OT percentage
        ot_percentage = round(
            float(agg['total_ot_hours'] or 0) / total_hours * 100, 1
        ) if total_hours > 0 else 0.0

        return {
            'total_entries': total_entries,
            'total_hours': round(total_hours, 1),
            'total_reg_hours': round(float(agg['total_reg_hours'] or 0), 1),
            'total_ot_hours': round(float(agg['total_ot_hours'] or 0), 1),
            'total_dt_hours': round(float(agg['total_dt_hours'] or 0), 1),
            'total_hol_hours': round(float(agg['total_hol_hours'] or 0), 1),
            'unique_employees': unique_employees,
            'unique_offices': agg['unique_offices'] or 0,
            'unique_weeks': unique_weeks,
            'avg_hours_per_entry': avg_hours_per_entry,
            'avg_hours_per_emp_week': avg_hours_per_emp_week,
            'entries_per_employee': entries_per_employee,
            'ot_percentage': ot_percentage,
        }

    def efficiency_kpis(self) -> dict:
        """Calculate efficiency-related KPIs."""
        total = self.qs.count()

        if total == 0:
            return {
                'first_try_clock_in_rate': 0.0,
                'first_try_clock_out_rate': 0.0,
                'avg_clock_in_tries': 0.0,
                'avg_clock_out_tries': 0.0,
                'multi_try_rate': 0.0,
            }

        # First try rates
        first_try_in = self.qs.filter(clock_in_tries=1).count()
        first_try_out = self.qs.filter(clock_out_tries=1).count()

        # Average tries
        agg = self.qs.aggregate(
            avg_in_tries=Avg('clock_in_tries'),
            avg_out_tries=Avg('clock_out_tries'),
        )

        # Multi-try entries (more than 1 try for either in or out)
        multi_try = self.qs.filter(clock_in_tries__gt=1).count() + \
                   self.qs.filter(clock_out_tries__gt=1).count()
        # Avoid double counting
        both_multi = self.qs.filter(clock_in_tries__gt=1, clock_out_tries__gt=1).count()
        multi_try = multi_try - both_multi

        return {
            'first_try_clock_in_rate': round(first_try_in / total * 100, 1),
            'first_try_clock_out_rate': round(first_try_out / total * 100, 1),
            'avg_clock_in_tries': round(float(agg['avg_in_tries'] or 1), 2),
            'avg_clock_out_tries': round(float(agg['avg_out_tries'] or 1), 2),
            'multi_try_rate': round(multi_try / total * 100, 1),
        }

    def by_office(self) -> list:
        """Calculate KPIs grouped by office using optimized single query."""
        from django.db.models import Case, When, IntegerField

        # Single aggregated query for all offices
        office_stats = self.qs.values('xlc_operation').annotate(
            total_entries=Count('id'),
            total_hours=Sum('total_hours'),
            total_ot_hours=Sum('ot_hours'),
            unique_employees=Count('applicant_id', distinct=True),
            # Count distinct ISO weeks (week_year + week_number) to properly
            # align Martinsburg Saturday endings with other offices' Sunday endings
            unique_weeks=Count(
                Concat('week_year', Value('-'), 'week_number'),
                distinct=True
            ),
            # Count by entry type using conditional aggregation
            finger_count=Count(Case(
                When(entry_type='Finger', then=1),
                output_field=IntegerField()
            )),
            provisional_count=Count(Case(
                When(entry_type='Provisional Entry', then=1),
                output_field=IntegerField()
            )),
            write_in_count=Count(Case(
                When(entry_type='Write-In', then=1),
                output_field=IntegerField()
            )),
            missing_co_count=Count(Case(
                When(entry_type='Missing c/o', then=1),
                output_field=IntegerField()
            )),
        ).order_by('xlc_operation')

        results = []
        for stat in office_stats:
            total = stat['total_entries'] or 0
            if total == 0:
                continue

            finger = stat['finger_count'] or 0
            provisional = stat['provisional_count'] or 0
            write_in = stat['write_in_count'] or 0
            missing_co = stat['missing_co_count'] or 0
            total_hours = float(stat['total_hours'] or 0)
            unique_employees = stat['unique_employees'] or 0
            unique_weeks = stat['unique_weeks'] or 1

            results.append({
                'office': stat['xlc_operation'],
                'finger_rate': round(finger / total * 100, 1) if total > 0 else 0.0,
                'provisional_rate': round(provisional / total * 100, 2) if total > 0 else 0.0,
                'write_in_rate': round(write_in / total * 100, 2) if total > 0 else 0.0,
                'missing_co_rate': round(missing_co / total * 100, 2) if total > 0 else 0.0,
                'total_entries': total,
                'total_hours': round(total_hours, 1),
                'unique_employees': unique_employees,
                'unique_weeks': unique_weeks,
                'ot_percentage': round(float(stat['total_ot_hours'] or 0) / total_hours * 100, 1) if total_hours > 0 else 0.0,
                'avg_hours_per_emp_week': round(total_hours / unique_employees / unique_weeks, 1) if unique_employees > 0 and unique_weeks > 0 else 0.0,
            })

        # Sort by finger rate descending
        results.sort(key=lambda x: x.get('finger_rate', 0), reverse=True)
        return results

    def by_week(self) -> list:
        """
        Calculate KPIs grouped by ISO week number.

        Uses week_number and week_year fields to align Martinsburg (Saturday endings)
        with other offices (Sunday endings) into the same weeks.
        """
        from django.db.models import Case, When, IntegerField

        # Group by ISO week (week_year + week_number) instead of raw date
        # This aligns Martinsburg Saturday endings with other Sunday endings
        week_stats = self.qs.values('week_year', 'week_number').annotate(
            total_entries=Count('id'),
            total_hours=Sum('total_hours'),
            total_ot_hours=Sum('ot_hours'),
            unique_employees=Count('applicant_id', distinct=True),
            unique_offices=Count('xlc_operation', distinct=True),
            # Count by entry type using conditional aggregation
            finger_count=Count(Case(
                When(entry_type='Finger', then=1),
                output_field=IntegerField()
            )),
            provisional_count=Count(Case(
                When(entry_type='Provisional Entry', then=1),
                output_field=IntegerField()
            )),
            write_in_count=Count(Case(
                When(entry_type='Write-In', then=1),
                output_field=IntegerField()
            )),
            missing_co_count=Count(Case(
                When(entry_type='Missing c/o', then=1),
                output_field=IntegerField()
            )),
        ).order_by('week_year', 'week_number')

        results = []
        for stat in week_stats:
            total = stat['total_entries'] or 0
            if total == 0:
                continue

            week_year = stat['week_year']
            week_number = stat['week_number']

            if week_year is None or week_number is None:
                continue

            finger = stat['finger_count'] or 0
            provisional = stat['provisional_count'] or 0
            write_in = stat['write_in_count'] or 0
            missing_co = stat['missing_co_count'] or 0
            total_hours = float(stat['total_hours'] or 0)

            # Calculate display date (Sunday of that week) for frontend
            week_display = get_week_display_date(week_year, week_number)

            results.append({
                'week': week_display.isoformat(),  # Keep 'week' for backwards compatibility
                'week_display': week_display.isoformat(),
                'week_year': week_year,
                'week_number': week_number,
                'finger_rate': round(finger / total * 100, 1) if total > 0 else 0.0,
                'provisional_rate': round(provisional / total * 100, 2) if total > 0 else 0.0,
                'write_in_rate': round(write_in / total * 100, 2) if total > 0 else 0.0,
                'missing_co_rate': round(missing_co / total * 100, 2) if total > 0 else 0.0,
                'total_entries': total,
                'total_hours': round(total_hours, 1),
                'unique_employees': stat['unique_employees'] or 0,
                'unique_offices': stat['unique_offices'] or 0,
                'ot_percentage': round(float(stat['total_ot_hours'] or 0) / total_hours * 100, 1) if total_hours > 0 else 0.0,
            })

        return results

    def by_department(self) -> list:
        """Calculate KPIs grouped by department using optimized single query."""
        from django.db.models import Case, When, IntegerField

        # Single aggregated query for all departments
        dept_stats = self.qs.values('bu_dept_name').annotate(
            total_entries=Count('id'),
            total_hours=Sum('total_hours'),
            total_ot_hours=Sum('ot_hours'),
            unique_employees=Count('applicant_id', distinct=True),
            unique_offices=Count('xlc_operation', distinct=True),
            # Count distinct ISO weeks (week_year + week_number) to properly
            # align Martinsburg Saturday endings with other offices' Sunday endings
            unique_weeks=Count(
                Concat('week_year', Value('-'), 'week_number'),
                distinct=True
            ),
            # Count by entry type using conditional aggregation
            finger_count=Count(Case(
                When(entry_type='Finger', then=1),
                output_field=IntegerField()
            )),
            provisional_count=Count(Case(
                When(entry_type='Provisional Entry', then=1),
                output_field=IntegerField()
            )),
            write_in_count=Count(Case(
                When(entry_type='Write-In', then=1),
                output_field=IntegerField()
            )),
            missing_co_count=Count(Case(
                When(entry_type='Missing c/o', then=1),
                output_field=IntegerField()
            )),
        ).order_by('bu_dept_name')

        results = []
        for stat in dept_stats:
            total = stat['total_entries'] or 0
            if total == 0:
                continue

            dept_name = stat['bu_dept_name'] or 'Unknown'
            finger = stat['finger_count'] or 0
            provisional = stat['provisional_count'] or 0
            write_in = stat['write_in_count'] or 0
            missing_co = stat['missing_co_count'] or 0
            total_hours = float(stat['total_hours'] or 0)
            unique_employees = stat['unique_employees'] or 0
            unique_weeks = stat['unique_weeks'] or 1

            results.append({
                'department': dept_name,
                'finger_rate': round(finger / total * 100, 1) if total > 0 else 0.0,
                'provisional_rate': round(provisional / total * 100, 2) if total > 0 else 0.0,
                'write_in_rate': round(write_in / total * 100, 2) if total > 0 else 0.0,
                'missing_co_rate': round(missing_co / total * 100, 2) if total > 0 else 0.0,
                'total_entries': total,
                'total_hours': round(total_hours, 1),
                'unique_employees': unique_employees,
                'unique_offices': stat['unique_offices'] or 0,
                'unique_weeks': unique_weeks,
                'ot_percentage': round(float(stat['total_ot_hours'] or 0) / total_hours * 100, 1) if total_hours > 0 else 0.0,
                'avg_hours_per_emp_week': round(total_hours / unique_employees / unique_weeks, 1) if unique_employees > 0 and unique_weeks > 0 else 0.0,
            })

        # Sort by finger rate descending
        results.sort(key=lambda x: x.get('finger_rate', 0), reverse=True)
        return results

    def by_shift(self) -> list:
        """Calculate KPIs grouped by shift using optimized single query."""
        from django.db.models import Case, When, IntegerField

        # Single aggregated query for all shifts
        shift_stats = self.qs.values('shift_number').annotate(
            total_entries=Count('id'),
            total_hours=Sum('total_hours'),
            total_ot_hours=Sum('ot_hours'),
            unique_employees=Count('applicant_id', distinct=True),
            unique_offices=Count('xlc_operation', distinct=True),
            # Count distinct ISO weeks (week_year + week_number) to properly
            # align Martinsburg Saturday endings with other offices' Sunday endings
            unique_weeks=Count(
                Concat('week_year', Value('-'), 'week_number'),
                distinct=True
            ),
            # Count by entry type using conditional aggregation
            finger_count=Count(Case(
                When(entry_type='Finger', then=1),
                output_field=IntegerField()
            )),
            provisional_count=Count(Case(
                When(entry_type='Provisional Entry', then=1),
                output_field=IntegerField()
            )),
            write_in_count=Count(Case(
                When(entry_type='Write-In', then=1),
                output_field=IntegerField()
            )),
            missing_co_count=Count(Case(
                When(entry_type='Missing c/o', then=1),
                output_field=IntegerField()
            )),
        ).order_by('shift_number')

        results = []
        for stat in shift_stats:
            total = stat['total_entries'] or 0
            if total == 0:
                continue

            shift = stat['shift_number'] or 'Unknown'
            finger = stat['finger_count'] or 0
            provisional = stat['provisional_count'] or 0
            write_in = stat['write_in_count'] or 0
            missing_co = stat['missing_co_count'] or 0
            total_hours = float(stat['total_hours'] or 0)
            unique_employees = stat['unique_employees'] or 0
            unique_weeks = stat['unique_weeks'] or 1

            results.append({
                'shift': shift,
                'finger_rate': round(finger / total * 100, 1) if total > 0 else 0.0,
                'provisional_rate': round(provisional / total * 100, 2) if total > 0 else 0.0,
                'write_in_rate': round(write_in / total * 100, 2) if total > 0 else 0.0,
                'missing_co_rate': round(missing_co / total * 100, 2) if total > 0 else 0.0,
                'total_entries': total,
                'total_hours': round(total_hours, 1),
                'unique_employees': unique_employees,
                'unique_offices': stat['unique_offices'] or 0,
                'unique_weeks': unique_weeks,
                'ot_percentage': round(float(stat['total_ot_hours'] or 0) / total_hours * 100, 1) if total_hours > 0 else 0.0,
                'avg_hours_per_emp_week': round(total_hours / unique_employees / unique_weeks, 1) if unique_employees > 0 and unique_weeks > 0 else 0.0,
            })

        # Sort by finger rate descending
        results.sort(key=lambda x: x.get('finger_rate', 0), reverse=True)
        return results

    def by_employee(self) -> list:
        """Calculate KPIs grouped by employee using optimized single query."""
        from django.db.models import Case, When, IntegerField

        # Single aggregated query for all employees
        employee_stats = self.qs.values('applicant_id', 'full_name', 'xlc_operation').annotate(
            total_entries=Count('id'),
            total_hours=Sum('total_hours'),
            # Count by entry type using conditional aggregation
            finger_count=Count(Case(
                When(entry_type='Finger', then=1),
                output_field=IntegerField()
            )),
            provisional_count=Count(Case(
                When(entry_type='Provisional Entry', then=1),
                output_field=IntegerField()
            )),
            write_in_count=Count(Case(
                When(entry_type='Write-In', then=1),
                output_field=IntegerField()
            )),
            missing_co_count=Count(Case(
                When(entry_type='Missing c/o', then=1),
                output_field=IntegerField()
            )),
        ).order_by('full_name')

        results = []
        for stat in employee_stats:
            total = stat['total_entries'] or 0
            if total == 0:
                continue

            finger = stat['finger_count'] or 0
            provisional = stat['provisional_count'] or 0
            write_in = stat['write_in_count'] or 0
            missing_co = stat['missing_co_count'] or 0
            total_hours = float(stat['total_hours'] or 0)
            non_finger = provisional + write_in + missing_co

            results.append({
                'applicant_id': stat['applicant_id'],
                'full_name': stat['full_name'] or 'Unknown',
                'office': stat['xlc_operation'],
                'finger_rate': round(finger / total * 100, 1) if total > 0 else 0.0,
                'finger_count': finger,
                'provisional_count': provisional,
                'write_in_count': write_in,
                'missing_co_count': missing_co,
                'non_finger_count': non_finger,
                'total_entries': total,
                'total_hours': round(total_hours, 1),
                'needs_enrollment': provisional >= 3,  # Flag for enrollment needed
            })

        # Sort by non_finger_count descending (worst performers first)
        results.sort(key=lambda x: x.get('non_finger_count', 0), reverse=True)
        return results

    def clock_behavior(self) -> dict:
        """Calculate detailed clock behavior analytics."""
        total = self.qs.count()

        if total == 0:
            return {
                'summary': {
                    'avg_clock_in_tries': 0.0,
                    'avg_clock_out_tries': 0.0,
                    'first_attempt_rate': 0.0,
                    'multi_try_clock_ins': 0,
                    'multi_try_clock_outs': 0,
                    'max_tries_observed': 0,
                    'total_entries': 0,
                },
                'distribution': {
                    'clock_in': [],
                    'clock_out': [],
                },
                'problem_employees': [],
            }

        # Summary metrics
        agg = self.qs.aggregate(
            avg_in_tries=Avg('clock_in_tries'),
            avg_out_tries=Avg('clock_out_tries'),
            max_in_tries=Max('clock_in_tries'),
            max_out_tries=Max('clock_out_tries'),
        )

        # First attempt success (both in and out on first try)
        first_try_both = self.qs.filter(clock_in_tries=1, clock_out_tries=1).count()
        first_attempt_rate = round(first_try_both / total * 100, 1)

        # Multi-try counts
        multi_try_in = self.qs.filter(clock_in_tries__gt=1).count()
        multi_try_out = self.qs.filter(clock_out_tries__gt=1).count()

        max_tries = max(
            int(agg['max_in_tries'] or 1),
            int(agg['max_out_tries'] or 1)
        )

        # Distribution of clock-in attempts
        clock_in_dist = list(
            self.qs.values('clock_in_tries')
            .annotate(count=Count('id'))
            .order_by('clock_in_tries')
        )

        # Distribution of clock-out attempts
        clock_out_dist = list(
            self.qs.values('clock_out_tries')
            .annotate(count=Count('id'))
            .order_by('clock_out_tries')
        )

        # Problem employees (high retry rates)
        problem_threshold = 2  # More than 2 tries on average
        problem_employees = list(
            self.qs.values('applicant_id', 'full_name', 'xlc_operation')
            .annotate(
                total_entries=Count('id'),
                avg_in_tries=Avg('clock_in_tries'),
                avg_out_tries=Avg('clock_out_tries'),
                multi_try_count=Count(
                    Case(
                        When(clock_in_tries__gt=1, then=1),
                        output_field=IntegerField()
                    )
                ) + Count(
                    Case(
                        When(clock_out_tries__gt=1, then=1),
                        output_field=IntegerField()
                    )
                ),
            )
            .filter(multi_try_count__gt=0)
            .order_by('-multi_try_count')[:50]
        )

        # Format problem employees
        formatted_problems = []
        for emp in problem_employees:
            formatted_problems.append({
                'applicant_id': emp['applicant_id'],
                'full_name': emp['full_name'] or 'Unknown',
                'office': emp['xlc_operation'],
                'total_entries': emp['total_entries'],
                'avg_clock_in_tries': round(float(emp['avg_in_tries'] or 1), 2),
                'avg_clock_out_tries': round(float(emp['avg_out_tries'] or 1), 2),
                'multi_try_count': emp['multi_try_count'],
            })

        return {
            'summary': {
                'avg_clock_in_tries': round(float(agg['avg_in_tries'] or 1), 2),
                'avg_clock_out_tries': round(float(agg['avg_out_tries'] or 1), 2),
                'first_attempt_rate': first_attempt_rate,
                'multi_try_clock_ins': multi_try_in,
                'multi_try_clock_outs': multi_try_out,
                'max_tries_observed': max_tries,
                'total_entries': total,
            },
            'distribution': {
                'clock_in': [
                    {'tries': d['clock_in_tries'], 'count': d['count'], 'percentage': round(d['count'] / total * 100, 1)}
                    for d in clock_in_dist
                ],
                'clock_out': [
                    {'tries': d['clock_out_tries'], 'count': d['count'], 'percentage': round(d['count'] / total * 100, 1)}
                    for d in clock_out_dist
                ],
            },
            'problem_employees': formatted_problems,
        }

    def trends(self) -> dict:
        """
        Calculate week-over-week trends using ISO week numbers.

        Uses week_number and week_year to align all offices to the same weeks.
        """
        # Get unique weeks ordered by most recent first
        weeks = list(
            self.qs.values('week_year', 'week_number')
            .distinct()
            .order_by('-week_year', '-week_number')[:2]
        )

        if len(weeks) < 2:
            return {'has_trends': False}

        current_week_info = weeks[0]
        prev_week_info = weeks[1]

        # Filter by week_year and week_number (aligns all offices)
        current_qs = self.qs.filter(
            week_year=current_week_info['week_year'],
            week_number=current_week_info['week_number']
        )
        prev_qs = self.qs.filter(
            week_year=prev_week_info['week_year'],
            week_number=prev_week_info['week_number']
        )

        current_kpis = KPICalculator(current_qs).calculate_all()
        prev_kpis = KPICalculator(prev_qs).calculate_all()

        # Calculate display dates for frontend
        current_display = get_week_display_date(
            current_week_info['week_year'],
            current_week_info['week_number']
        )
        prev_display = get_week_display_date(
            prev_week_info['week_year'],
            prev_week_info['week_number']
        )

        # Calculate deltas for key metrics
        deltas = {}
        for key in ['finger_rate', 'provisional_rate', 'total_entries', 'total_hours']:
            curr_val = current_kpis.get(key, 0)
            prev_val = prev_kpis.get(key, 0)
            if prev_val != 0:
                change = round((curr_val - prev_val) / prev_val * 100, 1)
            else:
                change = 0 if curr_val == 0 else 100
            deltas[f'{key}_delta'] = change
            deltas[f'{key}_prev'] = prev_val

        return {
            'has_trends': True,
            'current_week': current_display.isoformat(),
            'previous_week': prev_display.isoformat(),
            'current_week_number': current_week_info['week_number'],
            'current_week_year': current_week_info['week_year'],
            'previous_week_number': prev_week_info['week_number'],
            'previous_week_year': prev_week_info['week_year'],
            'current': current_kpis,
            'previous': prev_kpis,
            **deltas,
        }
