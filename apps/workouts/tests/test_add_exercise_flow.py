import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.workouts.models import Exercise, MuscleGroup, Routine, RoutineExercise

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
def musculo():
    return MuscleGroup.objects.create(slug="pectorals", name="Pectorales")


@pytest.fixture
def press(musculo):
    return Exercise.objects.create(
        external_id="0001", name="barbell front chest squat", slug="press",
        body_part="chest", equipment="barbell", target_muscle=musculo, is_global=True,
    )


@pytest.fixture
def mancuerna(musculo):
    return Exercise.objects.create(
        external_id="0002", name="dumbbell fly", slug="fly", body_part="chest",
        equipment="dumbbell", target_muscle=musculo, is_global=True,
    )


@pytest.fixture
def rutina(ana):
    return Routine.objects.create(user=ana, name="Empuje")


def anadir(cliente, rutina, exercise, **config):
    datos = {"target_sets": "4", "target_reps_min": "6", "target_reps_max": "8",
             "rest_seconds": "150"}
    datos.update(config)
    return cliente.post(
        reverse("routine_add_exercise", args=[rutina.pk, exercise.pk]), datos
    )


class TestLaPantallaDeEdicionYaNoExiste:
    def test_no_queda_ninguna_ruta_ni_plantilla(self):
        from pathlib import Path

        from django.conf import settings
        from django.urls import NoReverseMatch

        with pytest.raises(NoReverseMatch):
            reverse("routine_exercise_edit", args=[1])

        plantilla = Path(settings.BASE_DIR, "templates", "workouts", "routine_exercise_form.html")
        assert not plantilla.exists()


class TestCamposQueYaNoSeGuardan:
    @pytest.mark.parametrize("campo", ["notes", "target_rpe"])
    def test_routine_exercise_no_tiene(self, campo):
        assert campo not in {f.name for f in RoutineExercise._meta.get_fields()}

    def test_la_serie_no_guarda_duracion(self):
        from apps.workouts.models import SetLog

        assert "duration_seconds" not in {f.name for f in SetLog._meta.get_fields()}

    def test_la_sesion_no_guarda_fatiga(self):
        from apps.workouts.models import WorkoutSession

        assert "perceived_fatigue" not in {f.name for f in WorkoutSession._meta.get_fields()}

    def test_pero_el_rpe_de_cada_serie_SI_se_guarda(self):
        from apps.workouts.models import SetLog

        assert "rpe" in {f.name for f in SetLog._meta.get_fields()}
