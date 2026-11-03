import json
from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.accounts.privacy import SCRUBBED, delete_account, export_data
from apps.aiassist.models import AIGeneration, GenerationKind
from apps.bodyweight.models import BodyWeightEntry
from apps.metrics.models import Metric, UserMetricPreference
from apps.notifications.models import Notification, NotificationKind
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
PASSWORD = "Contrasena-Larga-Privacidad-1"


@pytest.fixture
def ejercicio():
    musculo = MuscleGroup.objects.create(slug="pectorals", name="Pectorales")
    return Exercise.objects.create(
        external_id="0001", name="Press de banca", slug="press",
        body_part="chest", equipment="barbell", target_muscle=musculo,
    )


@pytest.fixture
def user(ejercicio):
    user = User.objects.create_user(
        "ana", password=PASSWORD, email="ana@example.com",
        goal="bulk", height_cm=170, birth_date=date(1995, 4, 12),
        injuries_notes="Molestia en el hombro derecho.",
    )
    routine = Routine.objects.create(user=user, name="Mi rutina")
    RoutineExercise.objects.create(routine=routine, exercise=ejercicio, order=0)
    program = Program.objects.create(user=user, name="Mi programa", is_active=True)
    ScheduleEntry.objects.create(program=program, weekday=0, routine=routine)
    session = WorkoutSession.objects.create(user=user, date=date.today())
    SetLog.objects.create(
        session=session, exercise=ejercicio, set_number=1,
        weight_kg=Decimal("80"), reps=8,
    )
    BodyWeightEntry.objects.create(user=user, date=date.today(), weight_kg=Decimal("70.5"))
    Notification.objects.create(
        user=user, kind=NotificationKind.PROGRESS_READY, title="Aviso", body="Contenido"
    )
    return user


class TestExportacion:
    def test_incluye_todo_el_historial(self, user):
        datos = export_data(user)

        assert set(datos) == {
            "perfil", "rutinas", "programas", "entrenamientos", "peso_corporal",
            "notificaciones", "avisos_push",
        }
        assert len(datos["rutinas"]) == 1
        assert len(datos["entrenamientos"]) == 1
        assert len(datos["peso_corporal"]) == 1
        assert len(datos["notificaciones"]) == 1

    def test_el_perfil_lleva_la_fecha_exacta(self, user):
        datos = export_data(user)

        assert datos["perfil"]["fecha_nacimiento"] == "1995-04-12"
        assert datos["perfil"]["lesiones"] == "Molestia en el hombro derecho."

    def test_baja_los_detalles_de_cada_serie(self, user):
        serie = export_data(user)["entrenamientos"][0]["series"][0]

        assert serie["ejercicio"] == "Press de banca"
        assert serie["peso_kg"] == 80.0
        assert serie["repeticiones"] == 8

    def test_es_serializable_a_json(self, user):
        texto = json.dumps(export_data(user), ensure_ascii=False)

        assert "Press de banca" in texto

    def test_la_descarga_llega_como_archivo(self, client, user):
        client.force_login(user)

        respuesta = client.get(reverse("api-cuenta"))

        assert respuesta.status_code == 200
        assert respuesta["Content-Type"].startswith("application/json")
        assert "attachment" in respuesta["Content-Disposition"]
        assert "ana" in respuesta["Content-Disposition"]

    def test_solo_se_exporta_lo_propio(self, client, user, ejercicio):
        otro = User.objects.create_user("beto", password=PASSWORD)
        Routine.objects.create(user=otro, name="Rutina de Beto")
        client.force_login(user)

        contenido = client.get(reverse("api-cuenta")).content.decode()

        assert "Rutina de Beto" not in contenido


class TestBorrado:
    def test_borra_la_cuenta_y_su_historial(self, user):
        delete_account(user)

        assert User.objects.filter(username="ana").count() == 0
        assert Routine.objects.count() == 0
        assert WorkoutSession.objects.count() == 0
        assert SetLog.objects.count() == 0
        assert BodyWeightEntry.objects.count() == 0
        assert Notification.objects.count() == 0

    def test_limpia_el_rastro_personal_de_la_auditoria(self, user):
        AIGeneration.objects.create(
            user=user, kind=GenerationKind.ROUTINE, provider="anthropic", model="claude-opus-5",
            prompt_rendered="Lesiones: molestia en el hombro derecho. Peso: 70,5 kg.",
            raw_response='{"name": "Rutina"}',
            parsed_output={"name": "Rutina"},
            input_tokens=500, output_tokens=200,
        )

        delete_account(user)

        generacion = AIGeneration.objects.get()
        assert generacion.user is None
        assert generacion.prompt_rendered == SCRUBBED
        assert generacion.raw_response == SCRUBBED
        assert generacion.parsed_output is None
        assert generacion.input_tokens == 500
        assert generacion.provider == "anthropic"

    def test_borra_las_preferencias_de_metricas(self, user):
        metrica = Metric.objects.create(
            key="prueba", label="Prueba", description="x", category="volume", chart="bar"
        )
        UserMetricPreference.objects.create(user=user, metric=metrica)

        delete_account(user)

        assert UserMetricPreference.objects.count() == 0

    def test_no_arrastra_el_catalogo_global(self, user, ejercicio):
        delete_account(user)

        assert Exercise.objects.filter(pk=ejercicio.pk).exists()

    def test_borra_tambien_los_ejercicios_propios(self, user):
        propio = Exercise.objects.create(
            name="Invento mío", slug="invento", body_part="chest",
            equipment="barbell", is_global=False, created_by=user,
        )

        delete_account(user)

        assert not Exercise.objects.filter(pk=propio.pk).exists()

    def test_un_ejercicio_propio_en_uso_no_bloquea_la_baja(self, user, ejercicio):
        propio = Exercise.objects.create(
            name="Invento mío", slug="invento", body_part="chest",
            equipment="barbell", is_global=False, created_by=user,
        )
        rutina = Routine.objects.filter(user=user).first()
        RoutineExercise.objects.create(routine=rutina, exercise=propio, order=1)
        sesion = WorkoutSession.objects.get(user=user)
        SetLog.objects.create(session=sesion, exercise=propio, set_number=1, reps=10)

        delete_account(user)

        assert not User.objects.filter(username="ana").exists()
        assert not Exercise.objects.filter(pk=propio.pk).exists()
        assert Exercise.objects.filter(pk=ejercicio.pk).exists()

    def test_si_otro_usa_el_ejercicio_propio_se_conserva_sin_autoria(self, user):
        propio = Exercise.objects.create(
            name="Compartido", slug="compartido", body_part="chest",
            equipment="barbell", is_global=False, created_by=user,
        )
        otro = User.objects.create_user("beto", password=PASSWORD)
        sesion_ajena = WorkoutSession.objects.create(user=otro, date=date.today())
        SetLog.objects.create(session=sesion_ajena, exercise=propio, set_number=1, reps=5)

        delete_account(user)

        propio.refresh_from_db()
        assert propio.created_by is None
        assert not User.objects.filter(username="ana").exists()

    def test_devuelve_el_resumen_de_lo_borrado(self, user):
        resumen = delete_account(user)

        assert resumen["rutinas"] == 1
        assert resumen["entrenamientos"] == 1
        assert resumen["registros_de_peso"] == 1

    def test_no_afecta_a_otros_usuarios(self, user, ejercicio):
        otro = User.objects.create_user("beto", password=PASSWORD)
        Routine.objects.create(user=otro, name="De Beto")
        BodyWeightEntry.objects.create(user=otro, date=date.today(), weight_kg=Decimal("90"))

        delete_account(user)

        assert User.objects.filter(username="beto").exists()
        assert Routine.objects.count() == 1
        assert BodyWeightEntry.objects.count() == 1


class TestElEndpointDeBorrado:
    def test_pide_escribir_el_nombre_de_usuario(self, client, user):
        client.force_login(user)

        respuesta = client.delete(
            reverse("api-cuenta"),
            data=json.dumps({"confirmacion": "cualquier-cosa"}),
            content_type="application/json",
        )

        assert respuesta.status_code == 400
        assert User.objects.filter(username="ana").exists()

    def test_sin_confirmacion_tampoco(self, client, user):
        client.force_login(user)

        respuesta = client.delete(reverse("api-cuenta"))

        assert respuesta.status_code == 400
        assert User.objects.filter(username="ana").exists()

    def test_con_la_confirmacion_correcta_borra_y_cierra_sesion(self, client, user):
        client.force_login(user)

        respuesta = client.delete(
            reverse("api-cuenta"),
            data=json.dumps({"confirmacion": "ana"}),
            content_type="application/json",
        )

        assert respuesta.status_code == 200
        assert not User.objects.filter(username="ana").exists()
        assert "_auth_user_id" not in client.session

    def test_devuelve_el_resumen_de_lo_borrado(self, client, user, ejercicio):
        client.force_login(user)

        datos = client.delete(
            reverse("api-cuenta"),
            data=json.dumps({"confirmacion": "ana"}),
            content_type="application/json",
        ).json()

        assert set(datos) >= {"rutinas", "entrenamientos", "registros_de_peso"}

    def test_requiere_iniciar_sesion(self, client, db):
        assert client.get(reverse("api-cuenta")).status_code in (401, 403)
        assert client.delete(reverse("api-cuenta")).status_code in (401, 403)
