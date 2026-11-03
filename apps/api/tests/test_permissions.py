from datetime import date

import pytest
from django.contrib.auth import get_user_model

from apps.api.permissions import IsOwner
from apps.workouts.models import (
    Exercise,
    MuscleGroup,
    Program,
    Routine,
    RoutineExercise,
    ScheduleEntry,
    SetLog,
    WorkoutSession,
)

pytestmark = pytest.mark.django_db

User = get_user_model()


class PeticionFalsa:
    def __init__(self, user):
        self.user = user


@pytest.fixture
def ana():
    return User.objects.create_user("ana", password="Contrasena-Larga-1")


@pytest.fixture
def beto():
    return User.objects.create_user("beto", password="Contrasena-Larga-2")


@pytest.fixture
def ejercicio():
    musculo = MuscleGroup.objects.create(slug="p", name="Pectorales")
    return Exercise.objects.create(
        name="Press", slug="press", body_part="chest", equipment="barbell",
        target_muscle=musculo,
    )


def comprueba(obj, user) -> bool:
    return IsOwner().has_object_permission(PeticionFalsa(user), None, obj)


class TestDuenoDirecto:
    def test_rutina_propia(self, ana, beto):
        rutina = Routine.objects.create(user=ana, name="Empuje")

        assert comprueba(rutina, ana) is True
        assert comprueba(rutina, beto) is False

    def test_programa_propio(self, ana, beto):
        programa = Program.objects.create(user=ana, name="Volumen")

        assert comprueba(programa, ana) is True
        assert comprueba(programa, beto) is False

    def test_sesion_propia(self, ana, beto):
        sesion = WorkoutSession.objects.create(user=ana, date=date.today())

        assert comprueba(sesion, ana) is True
        assert comprueba(sesion, beto) is False


class TestDuenoPorRelacion:
    def test_serie_a_traves_de_la_sesion(self, ana, beto, ejercicio):
        sesion = WorkoutSession.objects.create(user=ana, date=date.today())
        serie = SetLog.objects.create(
            session=sesion, exercise=ejercicio, set_number=1, reps=8
        )

        assert comprueba(serie, ana) is True
        assert comprueba(serie, beto) is False

    def test_ejercicio_de_rutina_a_traves_de_la_rutina(self, ana, beto, ejercicio):
        rutina = Routine.objects.create(user=ana, name="Empuje")
        item = RoutineExercise.objects.create(routine=rutina, exercise=ejercicio, order=0)

        assert comprueba(item, ana) is True
        assert comprueba(item, beto) is False

    def test_dia_del_programa_a_traves_del_programa(self, ana, beto):
        programa = Program.objects.create(user=ana, name="Volumen")
        entrada = ScheduleEntry.objects.create(program=programa, weekday=0)

        assert comprueba(entrada, ana) is True
        assert comprueba(entrada, beto) is False


class TestSinDueno:
    def test_un_objeto_del_catalogo_no_pertenece_a_nadie(self, ana, ejercicio):
        assert comprueba(ejercicio, ana) is False
