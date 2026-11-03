import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from apps.workouts.models import (
    Exercise,
    MuscleGroup,
    Program,
    Routine,
    RoutineExercise,
    ScheduleEntry,
)

pytestmark = pytest.mark.django_db

User = get_user_model()


@pytest.fixture
def ana():
    return User.objects.create_user("ana", password="Contrasena-Larga-1")


@pytest.fixture
def cliente(client, ana):
    client.force_login(ana)
    return client


@pytest.fixture
def press():
    musculo = MuscleGroup.objects.create(slug="pectorals", name="Pectorales")
    return Exercise.objects.create(
        external_id="0001", name="Press de banca", slug="press", body_part="chest",
        equipment="barbell", target_muscle=musculo, is_global=True,
    )


@pytest.fixture
def empuje(ana, press):
    rutina = Routine.objects.create(user=ana, name="Empuje")
    RoutineExercise.objects.create(
        routine=rutina, exercise=press, order=0, target_sets=4,
        target_reps_min=6, target_reps_max=8,
    )
    return rutina


@pytest.fixture
def programa(ana):
    p = Program.objects.create(user=ana, name="Volumen", is_active=True)
    ScheduleEntry.objects.bulk_create([
        ScheduleEntry(program=p, weekday=weekday) for weekday in range(7)
    ])
    return p


class TestLaMismaRutinaEnVariosDias:
    def test_editarla_en_un_sitio_cambia_los_dos_dias(self, empuje, programa):
        programa.schedule.filter(weekday__in=[0, 3]).update(routine=empuje)

        item = empuje.exercises.first()
        item.target_sets = 6
        item.save(update_fields=["target_sets"])

        lunes = programa.schedule.get(weekday=0).routine
        jueves = programa.schedule.get(weekday=3).routine

        assert lunes == jueves == empuje
        assert lunes.exercises.first().target_sets == 6
        assert jueves.exercises.first().target_sets == 6

    def test_no_se_duplican_los_ejercicios(self, empuje, programa):
        programa.schedule.filter(weekday__in=[0, 3]).update(routine=empuje)

        assert RoutineExercise.objects.filter(routine__user=empuje.user).count() == 1


class TestLaFormaDeLaSemana:
    def test_un_dia_solo_puede_tener_una_fila_por_programa(self, programa):
        with pytest.raises(IntegrityError):
            ScheduleEntry.objects.create(program=programa, weekday=0)

    def test_borrar_una_rutina_deja_sus_dias_en_descanso(self, empuje, programa):
        programa.schedule.filter(weekday=0).update(routine=empuje)

        empuje.delete()

        assert programa.schedule.get(weekday=0).routine is None
