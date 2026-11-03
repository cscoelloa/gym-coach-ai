import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from apps.bodyweight.models import BodyWeightEntry
from apps.notifications.models import Notification
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

User = get_user_model()


@pytest.fixture
def alice(db):
    return User.objects.create_user("alice", password="Contrasena-Larga-1")


@pytest.fixture
def bob(db):
    return User.objects.create_user("bob", password="Contrasena-Larga-2")


@pytest.fixture
def exercise(db):
    muscle = MuscleGroup.objects.create(slug="abs", name="Abdominales")
    return Exercise.objects.create(
        name="Plancha", slug="plancha", body_part="waist",
        equipment="body weight", target_muscle=muscle,
    )


@pytest.fixture
def datos_de_bob(bob, exercise):
    routine = Routine.objects.create(user=bob, name="Rutina de Bob")
    item = RoutineExercise.objects.create(routine=routine, exercise=exercise, order=0)
    program = Program.objects.create(user=bob, name="Programa de Bob")
    day = ScheduleEntry.objects.create(program=program, weekday=0, routine=routine)
    session = WorkoutSession.objects.create(user=bob, date="2026-09-01")
    set_log = SetLog.objects.create(session=session, exercise=exercise, set_number=1, reps=10)
    weight = BodyWeightEntry.objects.create(user=bob, date="2026-09-01", weight_kg=80)
    notification = Notification.objects.create(
        user=bob, kind="stall_detected", title="Estancamiento", body="Llevas seis semanas igual.",
    )
    return {
        "routine": routine, "program": program, "day": day, "item": item,
        "session": session, "set_log": set_log, "weight": weight,
        "notification": notification,
    }


@pytest.fixture
def como_alice(alice):
    cliente = APIClient()
    cliente.force_login(alice)
    return cliente


RECURSOS = [
    ("api-routine-detail", "routine"),
    ("api-program-detail", "program"),
    ("api-schedule-entry-detail", "day"),
    ("api-routine-exercise-detail", "item"),
    ("api-session-detail", "session"),
    ("api-set-detail", "set_log"),
    ("api-bodyweight-detail", "weight"),
    ("api-notification-detail", "notification"),
]


@pytest.mark.parametrize("url_name, key", RECURSOS)
def test_no_puede_leer_recursos_ajenos(como_alice, datos_de_bob, url_name, key):
    respuesta = como_alice.get(reverse(url_name, args=[datos_de_bob[key].pk]))

    assert respuesta.status_code == 404


@pytest.mark.parametrize("url_name, key", RECURSOS)
def test_no_puede_modificar_recursos_ajenos(como_alice, datos_de_bob, url_name, key):
    respuesta = como_alice.patch(reverse(url_name, args=[datos_de_bob[key].pk]), {}, format="json")

    assert respuesta.status_code == 404


@pytest.mark.parametrize("url_name, key", RECURSOS)
def test_no_puede_borrar_recursos_ajenos(como_alice, datos_de_bob, url_name, key):
    objeto = datos_de_bob[key]

    respuesta = como_alice.delete(reverse(url_name, args=[objeto.pk]))

    assert respuesta.status_code in (404, 405)
    assert type(objeto).objects.filter(pk=objeto.pk).exists()


@pytest.mark.parametrize(
    "url_name",
    ["dashboard", "plan", "session_list", "bodyweight_list", "profile"],
)
def test_requiere_iniciar_sesion(client, db, url_name):
    response = client.get(reverse(url_name))

    assert response.status_code == 302
    assert reverse("login") in response.url
