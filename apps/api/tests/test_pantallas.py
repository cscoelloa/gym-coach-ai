from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.bodyweight.models import BodyWeightEntry
from apps.workouts.models import (
    Exercise,
    MuscleGroup,
    Program,
    Routine,
    RoutineExercise,
    ScheduleEntry,
    WorkoutSession,
)

pytestmark = pytest.mark.django_db

User = get_user_model()


@pytest.fixture
def ana():
    return User.objects.create_user("ana", password="Contrasena-Larga-Api-1")


@pytest.fixture
def api(ana):
    cliente = APIClient()
    cliente.force_login(ana)
    return cliente


@pytest.fixture
def ejercicio():
    pecho = MuscleGroup.objects.create(slug="pectorals", name="Pectorales")
    return Exercise.objects.create(
        external_id="0001", name="Press de banca", slug="press-banca",
        body_part="chest", equipment="barbell", target_muscle=pecho,
    )


def con_rutina_hoy(usuario, ejercicio=None, *, nombre="Empuje"):
    programa = Program.objects.create(user=usuario, name="Volumen", is_active=True)
    rutina = Routine.objects.create(user=usuario, name=nombre)
    if ejercicio:
        RoutineExercise.objects.create(
            routine=rutina, exercise=ejercicio, order=0, target_sets=3,
            target_reps_min=6, target_reps_max=8, rest_seconds=90,
        )
    for dia in range(7):
        ScheduleEntry.objects.create(
            program=programa,
            weekday=dia,
            routine=rutina if dia == timezone.localdate().weekday() else None,
        )
    return rutina


class TestQueTocaHoy:
    def test_sin_programa_lo_dice(self, api):
        datos = api.get(reverse("api-inicio")).json()

        assert datos["hoy_toca"]["estado"] == "sin_programa"

    def test_un_dia_sin_rutina_es_descanso_y_no_falta_de_plan(self, api, ana):
        programa = Program.objects.create(user=ana, name="Volumen", is_active=True)
        for dia in range(7):
            ScheduleEntry.objects.create(program=programa, weekday=dia, routine=None)

        datos = api.get(reverse("api-inicio")).json()

        assert datos["hoy_toca"]["estado"] == "descanso"

    def test_con_rutina_dice_cuál_y_sus_ejercicios(self, api, ana, ejercicio):
        rutina = con_rutina_hoy(ana, ejercicio)

        datos = api.get(reverse("api-inicio")).json()["hoy_toca"]

        assert datos["estado"] == "rutina"
        assert datos["rutina"]["id"] == rutina.pk
        assert datos["rutina"]["nombre"] == "Empuje"
        assert datos["rutina"]["ejercicios"] == [
            {"id": ejercicio.pk, "name": "Press de banca", "image": None}
        ]

    def test_una_sesion_sin_terminar_manda_sobre_todo_lo_demas(self, api, ana, ejercicio):
        con_rutina_hoy(ana, ejercicio)
        sesion = WorkoutSession.objects.create(user=ana, date=timezone.localdate())

        datos = api.get(reverse("api-inicio")).json()["hoy_toca"]

        assert datos["estado"] == "sesion_abierta"
        assert datos["sesion"]["id"] == sesion.pk

    def test_una_sesion_terminada_no_cuenta(self, api, ana):
        WorkoutSession.objects.create(
            user=ana, date=timezone.localdate(), finished_at=timezone.now()
        )

        datos = api.get(reverse("api-inicio")).json()["hoy_toca"]

        assert datos["estado"] == "sin_programa"


class TestLaSemana:
    def test_son_siete_dias_de_lunes_a_domingo(self, api):
        semana = api.get(reverse("api-inicio")).json()["semana"]

        assert len(semana) == 7
        assert semana[0]["inicial"] == "L"
        assert semana[-1]["inicial"] == "D"

    def test_marca_el_dia_de_hoy_una_sola_vez(self, api):
        semana = api.get(reverse("api-inicio")).json()["semana"]

        assert sum(1 for dia in semana if dia["hoy"]) == 1

    def test_un_dia_entrenado_se_marca(self, api, ana):
        WorkoutSession.objects.create(user=ana, date=timezone.localdate())

        semana = api.get(reverse("api-inicio")).json()["semana"]

        assert next(dia for dia in semana if dia["hoy"])["entrenado"] is True


class TestElPeso:
    def test_la_serie_va_de_antigua_a_reciente(self, api, ana):
        hoy = timezone.localdate()
        for dias, peso in [(4, "80.0"), (2, "81.0"), (0, "82.0")]:
            BodyWeightEntry.objects.create(
                user=ana, date=hoy - timedelta(days=dias), weight_kg=Decimal(peso)
            )

        serie = api.get(reverse("api-inicio")).json()["peso"]["serie"]

        assert serie["values"] == [80.0, 81.0, 82.0]
        meses = ("ene", "feb", "mar", "abr", "may", "jun",
                 "jul", "ago", "sep", "oct", "nov", "dic")
        esperado = [
            f"{(hoy - timedelta(days=dias)).day} {meses[(hoy - timedelta(days=dias)).month - 1]}"
            for dias in (4, 2, 0)
        ]
        assert serie["labels"] == esperado

    def test_con_un_solo_registro_no_hay_serie(self, api, ana):
        BodyWeightEntry.objects.create(
            user=ana, date=timezone.localdate(), weight_kg=Decimal("80.0")
        )

        peso = api.get(reverse("api-inicio")).json()["peso"]

        assert peso["serie"] is None
        assert peso["ultimo"]["kg"] == 80.0

    def test_el_cambio_es_contra_el_registro_anterior(self, api, ana):
        hoy = timezone.localdate()
        BodyWeightEntry.objects.create(user=ana, date=hoy - timedelta(days=1),
                                       weight_kg=Decimal("80.0"))
        BodyWeightEntry.objects.create(user=ana, date=hoy, weight_kg=Decimal("81.5"))

        peso = api.get(reverse("api-inicio")).json()["peso"]

        assert peso["cambio"] == pytest.approx(1.5)

    def test_sin_registros_no_revienta(self, api):
        peso = api.get(reverse("api-inicio")).json()["peso"]

        assert peso["ultimo"] is None
        assert peso["cambio"] is None
        assert peso["serie"] is None

    def test_la_meta_viaja_con_los_datos(self, api, ana):
        ana.target_weight_kg = Decimal("78.0")
        ana.save(update_fields=["target_weight_kg"])
        hoy = timezone.localdate()
        for dias in (1, 0):
            BodyWeightEntry.objects.create(
                user=ana, date=hoy - timedelta(days=dias), weight_kg=Decimal("80.0") + dias
            )

        serie = api.get(reverse("api-inicio")).json()["peso"]["serie"]

        assert serie["goal"] == 78.0


class TestElResumenDePeso:
    def test_la_grafica_no_depende_de_la_pagina_del_listado(self, api, ana):
        hoy = timezone.localdate()
        for dias in range(40):
            BodyWeightEntry.objects.create(
                user=ana, date=hoy - timedelta(days=dias), weight_kg=Decimal("80.0")
            )

        serie = api.get(reverse("api-bodyweight-resumen")).json()["serie"]

        assert len(serie["values"]) == 40

    def test_no_enseña_el_peso_de_otra_persona(self, api):
        otra = User.objects.create_user("beto", password="Contrasena-Larga-Api-1")
        BodyWeightEntry.objects.create(
            user=otra, date=timezone.localdate(), weight_kg=Decimal("99.0")
        )

        datos = api.get(reverse("api-bodyweight-resumen")).json()

        assert datos["ultimo"] is None


class TestLaRacha:
    def test_cuenta_las_semanas_y_lo_de_esta(self, api, ana):
        WorkoutSession.objects.create(user=ana, date=timezone.localdate())

        racha = api.get(reverse("api-inicio")).json()["racha"]

        assert racha["semanas"] == 1
        assert racha["hechas_esta_semana"] == 1
        assert racha["total_sesiones"] == 1

    def test_sin_nada_no_revienta(self, api):
        racha = api.get(reverse("api-inicio")).json()["racha"]

        assert racha == {
            "semanas": 0,
            "hechas_esta_semana": 0,
            "planificadas_esta_semana": 0,
            "total_sesiones": 0,
        }


class TestElMapaCorporal:
    def test_los_niveles_llevan_todos_los_musculos(self, api):
        niveles = api.get(reverse("api-inicio")).json()["mapa_corporal"]

        assert len(niveles) > 20
        assert all(valor == 0 for valor in niveles.values())

    def test_los_trazados_van_en_su_propio_endpoint(self, api):
        datos = api.get(reverse("api-mapa-corporal")).json()

        assert {vista["nombre"] for vista in datos["vistas"]} == {"front", "back"}
        assert sum(len(vista["regiones"]) for vista in datos["vistas"]) > 80
        assert all(region["d"] for vista in datos["vistas"] for region in vista["regiones"])

    def test_inicio_no_arrastra_los_trazados(self, api):
        cuerpo = api.get(reverse("api-inicio")).json()

        assert "vistas" not in cuerpo.get("mapa_corporal", {})
        assert '"d":' not in str(cuerpo)

    def test_las_regiones_inertes_van_primero(self, api):
        vistas = api.get(reverse("api-mapa-corporal")).json()["vistas"]
        regiones = vistas[0]["regiones"]

        inertes = [i for i, r in enumerate(regiones) if r["musculo"] is None]
        musculos = [i for i, r in enumerate(regiones) if r["musculo"] is not None]

        assert max(inertes) < min(musculos)


class TestElAislamiento:
    @pytest.mark.parametrize("ruta", ["api-inicio", "api-mapa-corporal"])
    def test_sin_sesion_no_se_ve_nada(self, ruta):
        respuesta = APIClient().get(reverse(ruta))

        assert respuesta.status_code in (401, 403)

    def test_inicio_no_mezcla_datos_de_dos_personas(self, api, ana):
        otra = User.objects.create_user("beto", password="Contrasena-Larga-Api-1")
        WorkoutSession.objects.create(user=otra, date=timezone.localdate())
        BodyWeightEntry.objects.create(user=otra, date=timezone.localdate(),
                                       weight_kg=Decimal("99.0"))

        datos = api.get(reverse("api-inicio")).json()

        assert datos["racha"]["total_sesiones"] == 0
        assert datos["peso"]["ultimo"] is None


class TestNoSalenDatosQueNoTocan:
    def test_inicio_no_lleva_la_fecha_de_nacimiento(self, api, ana):
        ana.birth_date = date(1994, 3, 2)
        ana.injuries_notes = "Hombro derecho"
        ana.save(update_fields=["birth_date", "injuries_notes"])

        cuerpo = str(api.get(reverse("api-inicio")).json())

        assert "1994" not in cuerpo
        assert "Hombro" not in cuerpo
