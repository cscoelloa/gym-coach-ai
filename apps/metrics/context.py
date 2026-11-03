from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from functools import cached_property

from django.utils import timezone

from apps.bodyweight.models import BodyWeightEntry
from apps.workouts.models import Program, SetLog, WorkoutSession

DEFAULT_WEEKS = 12


@dataclass
class MetricContext:
    user: object
    weeks: int = DEFAULT_WEEKS

    @cached_property
    def today(self) -> date:
        return timezone.localdate()

    @cached_property
    def since(self) -> date:
        return self.today - timedelta(weeks=self.weeks)

    @cached_property
    def sets(self) -> list[SetLog]:
        return list(
            SetLog.objects.filter(
                session__user=self.user,
                session__date__gte=self.since,
            )
            .select_related("exercise", "exercise__target_muscle", "session")
            .prefetch_related("exercise__secondary_muscles")
            .order_by("session__date", "id")
        )

    @cached_property
    def sessions(self) -> list[WorkoutSession]:
        return list(
            WorkoutSession.objects.filter(user=self.user, date__gte=self.since).order_by("date")
        )

    @cached_property
    def weights(self) -> list[BodyWeightEntry]:
        return list(
            BodyWeightEntry.objects.filter(user=self.user, date__gte=self.since).order_by("date")
        )

    @cached_property
    def latest_bodyweight(self) -> Decimal | None:
        entry = (
            BodyWeightEntry.objects.filter(user=self.user, date__lte=self.today)
            .order_by("-date")
            .first()
        )
        return entry.weight_kg if entry else None

    @cached_property
    def active_program(self) -> Program | None:
        return (
            Program.objects.filter(user=self.user, is_active=True)
            .prefetch_related("schedule")
            .order_by("-created_at")
            .first()
        )

    @cached_property
    def planned_days_per_week(self) -> int:
        if not self.active_program:
            return 0
        return sum(
            1 for entrada in self.active_program.schedule.all() if entrada.routine_id is not None
        )


    @cached_property
    def working_sets(self) -> list[SetLog]:
        from .loads import is_working_set

        return [s for s in self.sets if is_working_set(s)]

    @cached_property
    def muscle_names(self) -> dict[str, str]:
        from .loads import muscle_names

        names: dict[str, str] = {}
        for set_log in self.working_sets:
            names.update(muscle_names(set_log.exercise))
        return names

    @cached_property
    def weeks_in_window(self) -> int:
        from .formulas import week_key

        return len({week_key(s.date) for s in self.sessions}) or 1
