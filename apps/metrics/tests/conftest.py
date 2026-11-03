from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from apps.bodyweight.models import BodyWeightEntry
from apps.workouts.models import Exercise, MuscleGroup, SetLog, WorkoutSession

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user("atleta", password="Contrasena-Larga-1")


@pytest.fixture
def muscles(db):
    return {
        slug: MuscleGroup.objects.create(slug=slug, name=name)
        for slug, name in [
            ("pectorals", "Pectorales"),
            ("triceps", "Tríceps"),
            ("delts", "Deltoides"),
            ("lats", "Dorsales"),
            ("quads", "Cuádriceps"),
        ]
    }


@pytest.fixture
def make_exercise(db, muscles):
    def _make(name, *, target="pectorals", secondary=(), **flags):
        exercise = Exercise.objects.create(
            name=name,
            slug=name.lower().replace(" ", "-"),
            body_part=flags.pop("body_part", "chest"),
            equipment=flags.pop("equipment", "barbell"),
            target_muscle=muscles[target] if target else None,
            **flags,
        )
        if secondary:
            exercise.secondary_muscles.set([muscles[slug] for slug in secondary])
        return exercise

    return _make


@pytest.fixture
def bench(make_exercise):
    return make_exercise("Press de banca", target="pectorals", secondary=("triceps", "delts"))


@pytest.fixture
def pullup(make_exercise):
    return make_exercise(
        "Dominada", target="lats", equipment="body weight", is_bodyweight=True, body_part="back"
    )


@pytest.fixture
def treadmill(make_exercise):
    return make_exercise(
        "Cinta", target=None, equipment="stationary bike", is_cardio=True, body_part="cardio"
    )


@pytest.fixture
def log_set(db, user):
    def _log(
        exercise, *, days_ago=0, on_date=None, weight=100, reps=8,
        rpe=None, warmup=False, completed=True,
    ):
        day = on_date or (date.today() - timedelta(days=days_ago))
        session, _ = WorkoutSession.objects.get_or_create(user=user, date=day)
        return SetLog.objects.create(
            session=session,
            exercise=exercise,
            set_number=session.sets.filter(exercise=exercise).count() + 1,
            weight_kg=Decimal(str(weight)) if weight is not None else None,
            reps=reps,
            rpe=Decimal(str(rpe)) if rpe is not None else None,
            is_warmup=warmup,
            completed=completed,
        )

    return _log


@pytest.fixture
def log_weight(db, user):
    def _log(kg, *, days_ago=0):
        return BodyWeightEntry.objects.create(
            user=user,
            date=date.today() - timedelta(days=days_ago),
            weight_kg=Decimal(str(kg)),
        )

    return _log
