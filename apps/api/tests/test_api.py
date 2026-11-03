from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.urls import reverse
from rest_framework.test import APIClient

from apps.bodyweight.models import BodyWeightEntry
from apps.metrics.models import Metric
from apps.notifications.models import Notification, NotificationKind
from apps.workouts.models import (
    Exercise,
    MuscleGroup,
    Program,
    Routine,
    ScheduleEntry,
    SetLog,
    WorkoutSession,
)

pytestmark = pytest.mark.django_db

User = get_user_model()
PASSWORD = "Contrasena-Larga-Api-1"


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def ana():
    return User.objects.create_user("ana", password=PASSWORD, email="ana@example.com")


@pytest.fixture
def beto():
    return User.objects.create_user("beto", password=PASSWORD)


@pytest.fixture
def ejercicio():
    musculo = MuscleGroup.objects.create(slug="pectorals", name="Pectorales")
    return Exercise.objects.create(
        external_id="0001", name="Press de banca", slug="press", body_part="chest",
        equipment="barbell", target_muscle=musculo,
        instruction_steps={"es": ["Baja la barra."], "en": ["Lower the bar."]},
        attribution="© Gym visual — https://gymvisual.com/",
    )


@pytest.fixture
def datos_de_beto(beto, ejercicio):
    routine = Routine.objects.create(user=beto, name="Rutina de Beto")
    programa = Program.objects.create(user=beto, name="Programa de Beto")
    day = ScheduleEntry.objects.create(program=programa, weekday=0, routine=routine)
    session = WorkoutSession.objects.create(user=beto, date=date.today())
    set_log = SetLog.objects.create(session=session, exercise=ejercicio, set_number=1, reps=8)
    weight = BodyWeightEntry.objects.create(user=beto, date=date.today(), weight_kg=Decimal("80"))
    notificacion = Notification.objects.create(
        user=beto, kind=NotificationKind.PROGRESS_READY, title="Privado", body="Contenido privado"
    )
    return {"routine": routine, "day": day, "session": session,
            "set": set_log, "weight": weight, "notification": notificacion}


def autenticar(api, user) -> str:
    respuesta = api.post(
        reverse("api-token"), {"username": user.username, "password": PASSWORD}, format="json"
    )
    assert respuesta.status_code == 200, respuesta.data
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {respuesta.data['access']}")
    return respuesta.data["refresh"]


class TestAutenticacion:
    def test_devuelve_par_de_tokens(self, api, ana):
        respuesta = api.post(
            reverse("api-token"), {"username": "ana", "password": PASSWORD}, format="json"
        )

        assert respuesta.status_code == 200
        assert "access" in respuesta.data
        assert "refresh" in respuesta.data

    def test_credenciales_malas_no_entran(self, api, ana):
        respuesta = api.post(
            reverse("api-token"), {"username": "ana", "password": "incorrecta"}, format="json"
        )

        assert respuesta.status_code == 401

    def test_sin_token_no_se_accede(self, api, ana):
        assert api.get(reverse("api-profile")).status_code == 401

    def test_el_refresh_rota(self, api, ana):
        refresh = autenticar(api, ana)

        respuesta = api.post(reverse("api-token-refresh"), {"refresh": refresh}, format="json")

        assert respuesta.status_code == 200
        assert respuesta.data["refresh"] != refresh

    def test_el_logout_invalida_el_refresh(self, api, ana):
        refresh = autenticar(api, ana)

        api.post(reverse("api-token-blacklist"), {"refresh": refresh}, format="json")
        respuesta = api.post(reverse("api-token-refresh"), {"refresh": refresh}, format="json")

        assert respuesta.status_code == 401


class TestLimiteDeLogin:
    def test_el_login_tiene_su_propio_cupo(self, api, ana, monkeypatch):
        from rest_framework.throttling import SimpleRateThrottle

        monkeypatch.setitem(SimpleRateThrottle.THROTTLE_RATES, "login", "3/hour")

        codigos = [
            api.post(
                reverse("api-token"), {"username": "ana", "password": PASSWORD}, format="json"
            ).status_code
            for _ in range(4)
        ]

        assert codigos[:3] == [200, 200, 200]
        assert codigos[3] == 429

    def test_el_cupo_de_login_es_mas_alto_que_el_de_anonimos(self):
        from rest_framework.throttling import SimpleRateThrottle

        def por_hora(rate):
            cantidad, _periodo = rate.split("/")
            return int(cantidad)

        rates = SimpleRateThrottle.THROTTLE_RATES
        assert por_hora(rates["login"]) > por_hora(rates["anon"])


class TestAislamiento:
    @pytest.mark.parametrize(
        "ruta, clave",
        [
            ("api-routine-detail", "routine"),
            ("api-schedule-entry-detail", "day"),
            ("api-session-detail", "session"),
            ("api-set-detail", "set"),
            ("api-bodyweight-detail", "weight"),
            ("api-notification-detail", "notification"),
        ],
    )
    def test_los_recursos_ajenos_dan_404_no_403(self, api, ana, datos_de_beto, ruta, clave):
        autenticar(api, ana)

        respuesta = api.get(reverse(ruta, args=[datos_de_beto[clave].pk]))

        assert respuesta.status_code == 404

    def test_no_se_puede_borrar_lo_ajeno(self, api, ana, datos_de_beto):
        autenticar(api, ana)

        respuesta = api.delete(
            reverse("api-routine-detail", args=[datos_de_beto["routine"].pk])
        )

        assert respuesta.status_code == 404
        assert Routine.objects.filter(pk=datos_de_beto["routine"].pk).exists()

    def test_los_listados_solo_traen_lo_propio(self, api, ana, datos_de_beto):
        Routine.objects.create(user=ana, name="Rutina de Ana")
        autenticar(api, ana)

        datos = api.get(reverse("api-routine-list")).data

        nombres = [r["name"] for r in datos["results"]]
        assert nombres == ["Rutina de Ana"]

    def test_no_se_puede_crear_a_nombre_de_otro(self, api, ana, beto):
        autenticar(api, ana)

        api.post(
            reverse("api-bodyweight-list"),
            {"date": str(date.today()), "weight_kg": "70", "user": beto.pk},
            format="json",
        )

        assert BodyWeightEntry.objects.filter(user=beto).count() == 0
        assert BodyWeightEntry.objects.filter(user=ana).count() == 1

    def test_no_se_pueden_registrar_series_en_sesion_ajena(
        self, api, ana, datos_de_beto, ejercicio
    ):
        autenticar(api, ana)

        respuesta = api.post(
            reverse("api-set-list"),
            {"session": datos_de_beto["session"].pk, "exercise": ejercicio.pk,
             "set_number": 1, "reps": 10},
            format="json",
        )

        assert respuesta.status_code == 400
        assert "no es tuya" in str(respuesta.data)


class TestSuperficie:
    @pytest.mark.parametrize(
        "ruta",
        ["/api/configuraciones/", "/api/prompts/", "/api/generaciones/", "/api/almacenes/"],
    )
    def test_la_configuracion_de_ia_no_esta_expuesta(self, api, ana, ruta):
        autenticar(api, ana)

        assert api.get(ruta).status_code == 404

    @pytest.mark.parametrize("metodo", ["put", "patch", "delete"])
    def test_el_catalogo_global_no_se_puede_modificar(self, api, ana, ejercicio, metodo):
        autenticar(api, ana)
        url = reverse("api-exercise-detail", args=[ejercicio.slug])

        assert getattr(api, metodo)(url, {"name": "Otro"}).status_code == 405
        ejercicio.refresh_from_db()
        assert ejercicio.name == "Press de banca"

    def test_las_notificaciones_no_se_pueden_crear_desde_fuera(self, api, ana):
        autenticar(api, ana)

        assert api.post(reverse("api-notification-list"), {}).status_code == 405


class TestUsoNormal:
    def test_el_catalogo_trae_media_y_atribucion(self, api, ana, ejercicio):
        autenticar(api, ana)

        datos = api.get(reverse("api-exercise-list")).data["results"][0]

        assert datos["name"] == "Press de banca"
        assert datos["steps"] == ["Baja la barra."]
        assert "gymvisual.com" in datos["attribution"]

    def test_se_puede_buscar_y_filtrar(self, api, ana, ejercicio):
        autenticar(api, ana)

        assert api.get(reverse("api-exercise-list"), {"q": "press"}).data["count"] == 1
        assert api.get(reverse("api-exercise-list"), {"q": "sentadilla"}).data["count"] == 0
        assert api.get(reverse("api-exercise-list"), {"equipment": "cable"}).data["count"] == 0

    def test_registrar_peso(self, api, ana):
        autenticar(api, ana)

        respuesta = api.post(
            reverse("api-bodyweight-list"),
            {"date": str(date.today()), "weight_kg": "70.5"},
            format="json",
        )

        assert respuesta.status_code == 201
        assert BodyWeightEntry.objects.get(user=ana).weight_kg == Decimal("70.50")

    def test_dos_pesos_el_mismo_dia_se_rechazan_con_explicacion(self, api, ana):
        autenticar(api, ana)
        api.post(
            reverse("api-bodyweight-list"),
            {"date": str(date.today()), "weight_kg": "70"}, format="json",
        )

        respuesta = api.post(
            reverse("api-bodyweight-list"),
            {"date": str(date.today()), "weight_kg": "71"}, format="json",
        )

        assert respuesta.status_code == 400
        assert "Edítalo" in str(respuesta.data)

    def test_activar_un_programa_desactiva_los_demas(self, api, ana):
        vieja = Program.objects.create(user=ana, name="Vieja", is_active=True)
        nueva = Program.objects.create(user=ana, name="Nueva", is_active=False)
        autenticar(api, ana)

        api.post(reverse("api-program-activate", args=[nueva.pk]))

        vieja.refresh_from_db()
        nueva.refresh_from_db()
        assert vieja.is_active is False
        assert nueva.is_active is True

    def test_marcar_todas_las_notificaciones(self, api, ana):
        Notification.objects.create(
            user=ana, kind=NotificationKind.PROGRESS_READY, title="A", body="a"
        )
        autenticar(api, ana)

        respuesta = api.post(reverse("api-notification-read-all"))

        assert respuesta.data["updated"] == 1
        assert Notification.objects.filter(user=ana, is_read=False).count() == 0

    def test_el_perfil_se_puede_leer_y_actualizar(self, api, ana):
        autenticar(api, ana)

        assert api.get(reverse("api-profile")).data["username"] == "ana"

        respuesta = api.patch(reverse("api-profile"), {"goal": "cut"}, format="json")

        assert respuesta.status_code == 200
        ana.refresh_from_db()
        assert ana.goal == "cut"

    def test_el_perfil_expone_la_edad_no_el_dia_exacto(self, api, ana):
        ana.birth_date = date(1998, 3, 15)
        ana.save()
        autenticar(api, ana)

        datos = api.get(reverse("api-profile")).data

        assert datos["age"] is not None


class TestMetricas:
    def test_devuelve_las_metricas_con_su_cobertura(self, api, ana):
        call_command("sync_metrics")
        autenticar(api, ana)

        datos = api.get(reverse("api-my-metrics")).data

        assert len(datos) == Metric.objects.count()
        assert all("coverage" in metrica for metrica in datos)

    def test_el_catalogo_describe_cada_metrica(self, api, ana):
        call_command("sync_metrics")
        autenticar(api, ana)

        datos = api.get(reverse("api-metric-list")).data

        assert len(datos) == Metric.objects.count()
        assert all(m["description"] and m["unit"] is not None for m in datos)


class TestLaBarridaDeAislamiento:
    GLOBALES = {"api-exercise", "api-metric"}

    def test_cubre_todos_los_recursos(self):
        from apps.accounts.tests.test_authorization import RECURSOS
        from apps.api.urls import router

        cubiertos = {nombre for nombre, _ in RECURSOS}
        propios = {
            f"{basename}-detail"
            for _, _, basename in router.registry
            if basename not in self.GLOBALES
        }

        sin_cubrir = propios - cubiertos
        assert not sin_cubrir, (
            f"recursos de usuario sin caso de aislamiento: {sorted(sin_cubrir)}. "
            "Añádelos a RECURSOS en apps/accounts/tests/test_authorization.py, o a GLOBALES "
            "aquí si de verdad son de todo el mundo."
        )

    def test_no_sobra_ninguno(self):
        from apps.accounts.tests.test_authorization import RECURSOS
        from apps.api.urls import router

        registrados = {f"{basename}-detail" for _, _, basename in router.registry}

        assert {nombre for nombre, _ in RECURSOS} <= registrados
