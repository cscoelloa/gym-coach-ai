from json import dumps

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.workouts.models import (
    Exercise,
    MuscleGroup,
    Program,
    Routine,
    WorkoutSession,
)

User = get_user_model()


@pytest.fixture
def catalogo(db):
    abs_ = MuscleGroup.objects.create(slug="abs", name="Abdominales")
    pecho = MuscleGroup.objects.create(slug="pectorals", name="Pectorales")
    return [
        Exercise.objects.create(
            name="Plancha", slug="plancha", body_part="waist",
            equipment="body weight", target_muscle=abs_,
            instruction_steps={"es": ["Apoya los antebrazos."], "en": ["Rest on forearms."]},
            attribution="© Gym visual — https://gymvisual.com/",
        ),
        Exercise.objects.create(
            name="Press de banca", slug="press-banca", body_part="chest",
            equipment="barbell", target_muscle=pecho,
        ),
        Exercise.objects.create(
            name="Press con mancuernas", slug="press-mancuernas", body_part="chest",
            equipment="dumbbell", target_muscle=pecho,
        ),
    ]


@pytest.fixture
def usuario(db):
    return User.objects.create_user("ana", password="Contrasena-Larga-1")


def json(client, url, datos):
    return client.post(url, data=dumps(datos), content_type="application/json")


def test_flujo_completo(client, usuario, catalogo):
    client.force_login(usuario)
    plancha = catalogo[0]

    rutina_id = json(client, reverse("api-routine-list"), {"name": "Empuje"}).json()["id"]
    json(client, reverse("api-routine-exercise-list"), {
        "routine": rutina_id, "exercise": plancha.pk, "target_sets": 3,
    })

    routine = Routine.objects.get(user=usuario, name="Empuje")
    assert routine.exercises.count() == 1

    programa_id = json(client, reverse("api-program-list"), {"name": "Mi programa"}).json()["id"]
    programa = Program.objects.get(pk=programa_id)
    assert programa.schedule.count() == 7
    assert programa.schedule.filter(routine__isnull=True).count() == 7

    lunes = programa.schedule.get(weekday=0)
    client.patch(
        reverse("api-schedule-entry-detail", args=[lunes.pk]),
        data=dumps({"routine": rutina_id}),
        content_type="application/json",
    )
    lunes.refresh_from_db()
    assert lunes.routine == routine

    sesion_id = json(client, reverse("api-session-list"), {"routine": rutina_id}).json()["id"]
    session = WorkoutSession.objects.get(user=usuario)
    assert session.pk == sesion_id
    assert session.routine == routine

    foco = client.get(reverse("api-session-foco", args=[sesion_id])).json()
    assert foco["actual"]["nombre"] == "Plancha"
    assert len(foco["filas"]) == 3

    for _ in range(2):
        json(client, reverse("api-set-list"), {
            "session": sesion_id, "exercise": plancha.pk,
            "weight_kg": "20", "reps": 12, "rpe": "8",
        })

    assert list(session.sets.order_by("set_number").values_list("set_number", flat=True)) == [1, 2]

    resumen = client.post(reverse("api-session-finalizar", args=[sesion_id])).json()

    session.refresh_from_db()
    assert session.finished_at is not None
    assert resumen["series"] == 2
    assert resumen["ejercicios"] == 1
