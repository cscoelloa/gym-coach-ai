from datetime import timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.bodyweight.models import BodyWeightEntry
from apps.metrics.models import Metric, UserMetricPreference
from apps.workouts.models import Exercise, MuscleGroup, SetLog, WorkoutSession

pytestmark = pytest.mark.django_db

User = get_user_model()


@pytest.fixture
def ana():
    return User.objects.create_user("ana", password="Contrasena-Larga-Api-1")


@pytest.fixture
def beto():
    return User.objects.create_user("beto", password="Contrasena-Larga-Api-1")


@pytest.fixture
def api(ana):
    cliente = APIClient()
    cliente.force_login(ana)
    return cliente


@pytest.fixture
def press():
    pecho = MuscleGroup.objects.create(slug="pectorals", name="Pectorales")
    return Exercise.objects.create(
        external_id="0001", name="Press de banca", slug="press-banca",
        body_part="chest", equipment="barbell", target_muscle=pecho,
    )


def progreso(api):
    return api.get(reverse("api-progreso")).json()


class TestLasCifras:
    def test_cuenta_las_sesiones_totales_y_las_del_mes(self, api, ana):
        hoy = timezone.localdate()
        WorkoutSession.objects.create(user=ana, date=hoy)
        WorkoutSession.objects.create(user=ana, date=hoy - timedelta(days=95))

        cifras = progreso(api)["cifras"]

        assert cifras["total_sesiones"] == 2
        assert cifras["sesiones_este_mes"] >= 1

    def test_sin_dos_pesos_la_variacion_es_nula_y_no_cero(self, api, ana):
        BodyWeightEntry.objects.create(
            user=ana, date=timezone.localdate(), weight_kg=Decimal("80")
        )

        assert progreso(api)["cifras"]["peso_30_dias"] is None

    def test_con_dos_pesos_separados_da_la_diferencia(self, api, ana):
        hoy = timezone.localdate()
        BodyWeightEntry.objects.create(
            user=ana, date=hoy - timedelta(days=40), weight_kg=Decimal("82")
        )
        BodyWeightEntry.objects.create(user=ana, date=hoy, weight_kg=Decimal("79.5"))

        assert progreso(api)["cifras"]["peso_30_dias"] == pytest.approx(-2.5)

    def test_no_cuenta_las_sesiones_de_otra_persona(self, api, beto):
        WorkoutSession.objects.create(user=beto, date=timezone.localdate())

        assert progreso(api)["cifras"]["total_sesiones"] == 0


class TestElCalendario:
    def test_llega_en_columnas_de_siete_dias(self, api):
        calendario = progreso(api)["calendario"]

        assert calendario["semanas"]
        assert all(len(semana["dias"]) == 7 for semana in calendario["semanas"])

    def test_los_dias_futuros_de_la_semana_en_curso_son_nulos(self, api):
        ultima = progreso(api)["calendario"]["semanas"][-1]

        hoy = timezone.localdate()
        assert ultima["dias"][hoy.weekday()] is not None
        assert all(dia is None for dia in ultima["dias"][hoy.weekday() + 1:])

    def test_la_etiqueta_del_mes_viaja_dentro_de_su_columna(self, api):
        semanas = progreso(api)["calendario"]["semanas"]

        con_etiqueta = [s for s in semanas if s["etiqueta"]]
        assert con_etiqueta, "ninguna columna trae el nombre de su mes"
        assert all(isinstance(s["etiqueta"], str) for s in semanas)

    def test_el_nivel_sube_con_los_minutos_entrenados(self, api, ana):
        hoy = timezone.localdate()
        arranque = timezone.now() - timedelta(hours=2)
        WorkoutSession.objects.create(
            user=ana, date=hoy, started_at=arranque, finished_at=arranque + timedelta(minutes=100)
        )

        semanas = progreso(api)["calendario"]["semanas"]
        de_hoy = semanas[-1]["dias"][hoy.weekday()]

        assert de_hoy["minutos"] == 100
        assert de_hoy["nivel"] == 4

    def test_un_dia_entrenado_sin_duracion_no_se_pinta_como_vacio(self, api, ana):
        hoy = timezone.localdate()
        WorkoutSession.objects.create(user=ana, date=hoy)

        de_hoy = progreso(api)["calendario"]["semanas"][-1]["dias"][hoy.weekday()]

        assert de_hoy["sesiones"] == 1
        assert de_hoy["nivel"] > 0


class TestElRepartoPorMusculo:
    def test_trae_niveles_de_todos_los_musculos_aunque_esten_a_cero(self, api):
        niveles = progreso(api)["mapa_corporal"]["niveles"]

        assert len(niveles) > 20
        assert all(nivel == 0 for nivel in niveles.values())

    def test_una_serie_efectiva_enciende_el_musculo_objetivo(self, api, ana, press):
        sesion = WorkoutSession.objects.create(user=ana, date=timezone.localdate())
        SetLog.objects.create(
            session=sesion, exercise=press, set_number=1, weight_kg=Decimal("80"), reps=8
        )

        mapa = progreso(api)["mapa_corporal"]

        assert mapa["niveles"]["pectorals"] > 0
        assert mapa["total_series"] > 0

    def test_no_enseña_lo_que_ha_entrenado_otra_persona(self, api, beto, press):
        ajena = WorkoutSession.objects.create(user=beto, date=timezone.localdate())
        SetLog.objects.create(
            session=ajena, exercise=press, set_number=1, weight_kg=Decimal("80"), reps=8
        )

        assert progreso(api)["mapa_corporal"]["total_series"] == 0


class TestElRepartoPorDiaDeSemana:
    def test_siempre_vienen_los_siete_dias(self, api):
        por_dia = progreso(api)["por_dia_de_semana"]

        assert [d["weekday"] for d in por_dia] == [0, 1, 2, 3, 4, 5, 6]
        assert all(d["sesiones"] == 0 for d in por_dia)

    def test_cuenta_las_sesiones_en_su_dia(self, api, ana):
        hoy = timezone.localdate()
        WorkoutSession.objects.create(user=ana, date=hoy)

        por_dia = progreso(api)["por_dia_de_semana"]

        assert por_dia[hoy.weekday()]["sesiones"] == 1


class TestLaTendenciaDePeso:
    def test_con_un_solo_punto_no_hay_serie(self, api, ana):
        BodyWeightEntry.objects.create(
            user=ana, date=timezone.localdate(), weight_kg=Decimal("80")
        )

        assert progreso(api)["peso"]["serie"] is None

    def test_con_dos_o_mas_trae_los_puntos_y_la_meta(self, api, ana):
        ana.target_weight_kg = Decimal("75")
        ana.save()
        hoy = timezone.localdate()
        for dias, kg in ((10, "82"), (0, "80")):
            BodyWeightEntry.objects.create(
                user=ana, date=hoy - timedelta(days=dias), weight_kg=Decimal(kg)
            )

        serie = progreso(api)["peso"]["serie"]

        assert serie["values"] == [82.0, 80.0]
        assert serie["goal"] == 75.0

    def test_no_se_recorta_como_en_inicio(self, api, ana):
        hoy = timezone.localdate()
        for dias in range(70):
            BodyWeightEntry.objects.create(
                user=ana, date=hoy - timedelta(days=dias), weight_kg=Decimal("80")
            )

        assert len(progreso(api)["peso"]["serie"]["values"]) == 70


class TestSinSesion:
    def test_progreso_pide_identificarse(self):
        assert APIClient().get(reverse("api-progreso")).status_code in (401, 403)


class TestElCatalogoDeMetricas:
    @pytest.fixture(autouse=True)
    def _catalogo(self):
        call_command("sync_metrics")

    def test_cada_metrica_dice_si_esta_en_el_panel(self, api):
        datos = api.get(reverse("api-metric-list")).json()

        assert datos
        assert all("visible" in metrica for metrica in datos)

    def test_sin_preferencias_manda_el_valor_por_defecto(self, api):
        datos = {m["key"]: m["visible"] for m in api.get(reverse("api-metric-list")).json()}
        por_defecto = dict(
            Metric.objects.filter(is_active=True).values_list("key", "default_visible")
        )

        assert datos == por_defecto

    def test_guardar_la_lista_entera_apaga_lo_que_no_venga(self, api, ana):
        una = Metric.objects.filter(is_active=True, default_visible=True).first()
        assert una, "el catálogo no trae ninguna métrica visible por defecto"

        respuesta = api.put(
            reverse("api-metric-preferencias"), {"keys": []}, format="json"
        )

        assert respuesta.status_code == 200
        assert UserMetricPreference.objects.filter(
            user=ana, metric=una, is_visible=False
        ).exists()
        datos = {m["key"]: m["visible"] for m in api.get(reverse("api-metric-list")).json()}
        assert not any(datos.values())

    def test_lo_guardado_se_refleja_en_el_catalogo_y_en_el_panel(self, api):
        elegida = Metric.objects.filter(is_active=True).first().key

        api.put(reverse("api-metric-preferencias"), {"keys": [elegida]}, format="json")

        datos = {m["key"]: m["visible"] for m in api.get(reverse("api-metric-list")).json()}
        assert datos[elegida] is True
        panel = api.get(reverse("api-my-metrics")).json()
        assert [m["key"] for m in panel] == [elegida]

    def test_una_clave_que_no_existe_se_rechaza_entera(self, api, ana):
        respuesta = api.put(
            reverse("api-metric-preferencias"), {"keys": ["no-existe"]}, format="json"
        )

        assert respuesta.status_code == 400
        assert not UserMetricPreference.objects.filter(user=ana).exists()

    def test_hay_que_mandar_una_lista(self, api):
        respuesta = api.put(
            reverse("api-metric-preferencias"), {"keys": "fuerza"}, format="json"
        )

        assert respuesta.status_code == 400

    def test_lista_las_activas_y_no_las_desactivadas(self, api):
        Metric.objects.filter(key="session_density").update(is_active=False)

        claves = {m["key"] for m in api.get(reverse("api-metric-list")).json()}

        assert "weekly_tonnage" in claves
        assert "session_density" not in claves

    def test_guardar_dos_veces_no_duplica_filas(self, api, ana):
        api.put(reverse("api-metric-preferencias"), {"keys": ["weekly_tonnage"]}, format="json")
        api.put(reverse("api-metric-preferencias"), {"keys": ["adherence_rate"]}, format="json")

        assert (
            UserMetricPreference.objects.filter(user=ana).count()
            == Metric.objects.filter(is_active=True).count()
        )

    def test_las_preferencias_son_de_cada_uno(self, api, beto):
        elegida = Metric.objects.filter(is_active=True).first().key
        api.put(reverse("api-metric-preferencias"), {"keys": [elegida]}, format="json")

        otro = APIClient()
        otro.force_login(beto)
        datos = {m["key"]: m["visible"] for m in otro.get(reverse("api-metric-list")).json()}

        por_defecto = dict(
            Metric.objects.filter(is_active=True).values_list("key", "default_visible")
        )
        assert datos == por_defecto


class TestLasMetricasCalculadas:
    @pytest.fixture(autouse=True)
    def _catalogo(self):
        call_command("sync_metrics")

    def test_cada_una_trae_ya_resuelto_si_tiene_datos(self, api):
        datos = api.get(reverse("api-my-metrics")).json()

        assert datos
        for metrica in datos:
            assert set(metrica) >= {
                "has_no_data", "is_reliable", "empty_hint", "needs", "coverage_pct",
                "description", "category_label",
            }

    def test_ninguna_afirma_un_numero_que_no_pueda_respaldar(self, api):
        datos = api.get(reverse("api-my-metrics")).json()

        assert datos
        for metrica in datos:
            if metrica["has_no_data"]:
                assert metrica["empty_hint"]
            else:
                assert metrica["coverage"] > 0, f"{metrica['key']} enseña un número sin cobertura"

    def test_la_mayoria_se_calla_sin_historial(self, api):
        datos = api.get(reverse("api-my-metrics")).json()

        sin_datos = [m for m in datos if m["has_no_data"]]
        assert len(sin_datos) >= len(datos) - 1

    def test_el_panel_calcula_solo_las_elegidas(self, api, ana, press):
        sesion = WorkoutSession.objects.create(user=ana, date=timezone.localdate())
        SetLog.objects.create(
            session=sesion, exercise=press, set_number=1, weight_kg=Decimal("80"), reps=8
        )
        api.put(
            reverse("api-metric-preferencias"),
            {"keys": ["weekly_volume_by_muscle"]},
            format="json",
        )

        datos = api.get(reverse("api-my-metrics")).json()

        assert [m["key"] for m in datos] == ["weekly_volume_by_muscle"]
        assert datos[0]["series"] or datos[0]["rows"] or datos[0]["value"] is not None

    def test_sin_ninguna_elegida_el_panel_viene_vacio(self, api):
        api.put(reverse("api-metric-preferencias"), {"keys": []}, format="json")

        assert api.get(reverse("api-my-metrics")).json() == []

    def test_lo_que_no_se_puede_calcular_dice_qué_falta_sin_aviso_de_cobertura(
        self, api, ana, press
    ):
        press.is_bodyweight = True
        press.save()
        sesion = WorkoutSession.objects.create(user=ana, date=timezone.localdate())
        SetLog.objects.create(session=sesion, exercise=press, set_number=1, reps=10)
        api.put(reverse("api-metric-preferencias"), {"keys": ["weekly_tonnage"]}, format="json")

        tonelaje = api.get(reverse("api-my-metrics")).json()[0]

        assert tonelaje["has_no_data"] is True
        assert "peso corporal" in tonelaje["empty_hint"]

    def test_cuando_hay_cifra_poco_fiable_viaja_el_porcentaje_y_lo_que_falta(
        self, api, ana, press
    ):
        hoy = timezone.localdate()
        for dias in range(4):
            sesion = WorkoutSession.objects.create(user=ana, date=hoy - timedelta(days=dias))
            if dias == 0:
                inicio = timezone.now() - timedelta(hours=1)
                WorkoutSession.objects.filter(pk=sesion.pk).update(
                    started_at=inicio, finished_at=inicio + timedelta(minutes=50)
                )
            SetLog.objects.create(
                session=sesion, exercise=press, set_number=1, weight_kg=Decimal("80"), reps=8
            )
        api.put(reverse("api-metric-preferencias"), {"keys": ["session_density"]}, format="json")

        densidad = api.get(reverse("api-my-metrics")).json()[0]

        assert densidad["has_no_data"] is False
        assert densidad["is_reliable"] is False
        assert 0 < densidad["coverage_pct"] < 80
        assert densidad["needs"] == ["la hora de inicio y fin de tus sesiones"]

    def test_no_calcula_las_metricas_de_otra_persona(self, api, beto, ana, press):
        ajena = WorkoutSession.objects.create(user=beto, date=timezone.localdate())
        SetLog.objects.create(
            session=ajena, exercise=press, set_number=1, weight_kg=Decimal("80"), reps=8
        )

        datos = api.get(reverse("api-my-metrics"), {"key": "total_volume"}).json()

        assert all(m["has_no_data"] or not m["value"] for m in datos)
