from datetime import timedelta
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
    Routine,
    RoutineExercise,
    SetLog,
    WorkoutSession,
)

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
def catalogo():
    pecho = MuscleGroup.objects.create(slug="pectorals", name="Pectorales")
    triceps = MuscleGroup.objects.create(slug="triceps", name="Tríceps")
    press = Exercise.objects.create(
        external_id="0001", name="Press de banca", slug="press-banca",
        body_part="chest", equipment="barbell", target_muscle=pecho,
    )
    press.secondary_muscles.add(triceps)
    return {
        "press": press,
        "fondos": Exercise.objects.create(
            external_id="0002", name="Fondos", slug="fondos", body_part="chest",
            equipment="body weight", target_muscle=pecho, is_bodyweight=True,
        ),
        "remo": Exercise.objects.create(
            external_id="0003", name="Remo a una mano", slug="remo", body_part="back",
            equipment="dumbbell", target_muscle=pecho, is_unilateral=True,
        ),
    }


@pytest.fixture
def rutina(ana, catalogo):
    r = Routine.objects.create(user=ana, name="Empuje A")
    RoutineExercise.objects.create(
        routine=r, exercise=catalogo["press"], order=0,
        target_sets=3, target_reps_min=6, target_reps_max=8, rest_seconds=180,
    )
    RoutineExercise.objects.create(
        routine=r, exercise=catalogo["fondos"], order=1,
        target_sets=3, target_reps_min=8, target_reps_max=12, rest_seconds=90,
    )
    return r


@pytest.fixture
def sesion(ana, rutina):
    return WorkoutSession.objects.create(
        user=ana, routine=rutina, date=timezone.localdate(), started_at=timezone.now()
    )


def foco(api, sesion, **params):
    return api.get(reverse("api-session-foco", args=[sesion.pk]), params).json()


def registrar(sesion, ejercicio, cuantas):
    ya = sesion.sets.filter(exercise=ejercicio).count()
    for numero in range(ya + 1, ya + cuantas + 1):
        SetLog.objects.create(
            session=sesion, exercise=ejercicio, set_number=numero,
            weight_kg=Decimal("50"), reps=8,
        )


class TestEmpezar:
    def test_el_servidor_pone_la_fecha_y_la_hora(self, api, ana, rutina):
        respuesta = api.post(
            reverse("api-session-list"), {"routine": rutina.pk}, format="json"
        )

        assert respuesta.status_code == 201
        sesion = WorkoutSession.objects.get()
        assert sesion.date == timezone.localdate()
        assert sesion.started_at is not None

    def test_no_se_puede_entrenar_la_rutina_de_otra_persona(self, api, beto):
        ajena = Routine.objects.create(user=beto, name="Ajena")

        respuesta = api.post(
            reverse("api-session-list"), {"routine": ajena.pk}, format="json"
        )

        assert respuesta.status_code == 400
        assert not WorkoutSession.objects.exists()


class TestElDiario:
    def test_cada_sesion_dice_de_qué_rutina_fue(self, api, sesion, rutina):
        filas = api.get(reverse("api-session-list")).json()["results"]

        assert filas[0]["routine_name"] == rutina.name

    def test_una_sesion_libre_no_tiene_nombre_de_rutina(self, api, ana):
        WorkoutSession.objects.create(user=ana, date=timezone.localdate())

        filas = api.get(reverse("api-session-list")).json()["results"]

        assert filas[0]["routine_name"] is None

    def test_cada_sesion_trae_su_duracion_y_su_tonelaje(self, api, ana, rutina, catalogo):
        sesion = WorkoutSession.objects.create(
            user=ana,
            routine=rutina,
            date=timezone.localdate(),
            started_at=timezone.now() - timedelta(minutes=45),
            finished_at=timezone.now(),
        )
        registrar(sesion, catalogo["press"], 2)

        fila = api.get(reverse("api-session-list")).json()["results"][0]

        assert fila["duracion_minutos"] == 45
        assert fila["tonelaje_kg"] == 800

    def test_una_sesion_sin_terminar_no_tiene_duracion(self, api, sesion):
        fila = api.get(reverse("api-session-list")).json()["results"][0]

        assert fila["duracion_minutos"] is None


class TestElFoco:
    def test_arranca_en_el_primer_ejercicio(self, api, sesion):
        datos = foco(api, sesion)

        assert datos["indice"] == 1
        assert datos["actual"]["nombre"] == "Press de banca"
        assert datos["total_ejercicios"] == 2

    def test_el_indice_viene_de_la_url(self, api, sesion):
        datos = foco(api, sesion, ejercicio=2)

        assert datos["actual"]["nombre"] == "Fondos"

    @pytest.mark.parametrize("valor", [0, 99, -3, "abc"])
    def test_un_indice_imposible_se_acota_en_vez_de_dar_404(self, api, sesion, valor):
        datos = foco(api, sesion, ejercicio=valor)

        assert datos["indice"] in (1, 2)
        assert datos["actual"] is not None

    def test_manda_la_animacion_y_su_atribucion(self, api, sesion, catalogo):
        press = catalogo["press"]
        press.image.name = "exercises/images/0001.jpg"
        press.animation.name = "exercises/animations/0001.gif"
        press.attribution = "© Gym visual — https://gymvisual.com/"
        press.save()

        actual = foco(api, sesion, ejercicio=1)["actual"]

        assert actual["imagen"].endswith("0001.jpg")
        assert actual["animacion"].endswith("0001.gif")
        assert actual["atribucion"] == "© Gym visual — https://gymvisual.com/"

    def test_sin_material_visual_no_inventa_nada(self, api, sesion):
        actual = foco(api, sesion, ejercicio=1)["actual"]

        assert actual["imagen"] is None
        assert actual["animacion"] is None
        assert actual["atribucion"] == ""

    def test_hay_una_fila_por_serie_planificada(self, api, sesion):
        filas = foco(api, sesion)["filas"]

        assert len(filas) == 3
        assert [f["numero"] for f in filas] == [1, 2, 3]
        assert filas[0]["activa"] is True

    def test_una_serie_de_mas_se_pinta_como_fila(self, api, sesion, catalogo):
        registrar(sesion, catalogo["press"], 4)

        filas = foco(api, sesion, ejercicio=1)["filas"]

        assert [f["numero"] for f in filas] == [1, 2, 3, 4]
        assert all(f["serie_id"] is not None for f in filas)
        assert not any(f["activa"] for f in filas)

    def test_la_fila_activa_avanza_con_cada_serie(self, api, sesion, catalogo):
        SetLog.objects.create(
            session=sesion, exercise=catalogo["press"], set_number=1,
            weight_kg=Decimal("80"), reps=8,
        )

        filas = foco(api, sesion)["filas"]

        assert filas[0]["activa"] is False
        assert filas[1]["activa"] is True

    def test_la_fila_activa_propone_lo_de_la_serie_anterior_de_hoy(
        self, api, sesion, catalogo
    ):
        SetLog.objects.create(
            session=sesion, exercise=catalogo["press"], set_number=1,
            weight_kg=Decimal("82.5"), reps=7,
        )

        activa = next(f for f in foco(api, sesion)["filas"] if f["activa"])

        assert activa["peso"] == "82.5"
        assert activa["reps"] == 7

    def test_sin_series_hoy_propone_lo_de_la_ultima_vez(self, api, ana, sesion, catalogo):
        anterior = WorkoutSession.objects.create(
            user=ana, date=timezone.localdate() - timedelta(days=3), finished_at=timezone.now()
        )
        SetLog.objects.create(
            session=anterior, exercise=catalogo["press"], set_number=1,
            weight_kg=Decimal("77.5"), reps=8,
        )

        activa = next(f for f in foco(api, sesion)["filas"] if f["activa"])

        assert activa["peso"] == "77.5"

    def test_el_peso_llega_con_punto_y_no_con_coma(self, api, sesion, catalogo):
        SetLog.objects.create(
            session=sesion, exercise=catalogo["press"], set_number=1,
            weight_kg=Decimal("92.50"), reps=6,
        )

        activa = next(f for f in foco(api, sesion)["filas"] if f["activa"])

        assert "," not in activa["peso"]
        assert activa["peso"] == "92.5"

    def test_trae_la_ultima_vez_y_el_mejor(self, api, ana, sesion, catalogo):
        anterior = WorkoutSession.objects.create(
            user=ana, date=timezone.localdate() - timedelta(days=3), finished_at=timezone.now()
        )
        for numero, peso in enumerate([Decimal("75"), Decimal("80")], start=1):
            SetLog.objects.create(
                session=anterior, exercise=catalogo["press"], set_number=numero,
                weight_kg=peso, reps=8,
            )

        datos = foco(api, sesion)

        assert datos["ultima_vez"]["series"] == [["75", 8], ["80", 8]]
        assert datos["mejor"] == "80"

    def test_la_lista_lateral_dice_cuantas_van_de_cada_uno(self, api, sesion, catalogo):
        SetLog.objects.create(
            session=sesion, exercise=catalogo["press"], set_number=1,
            weight_kg=Decimal("80"), reps=8,
        )

        planificados = foco(api, sesion)["planificados"]

        assert planificados[0]["hechas"] == 1
        assert planificados[1]["hechas"] == 0

    def test_el_avance_cuenta_las_series_de_todo_el_dia(self, api, sesion, catalogo):
        for ejercicio in (catalogo["press"], catalogo["fondos"]):
            SetLog.objects.create(
                session=sesion, exercise=ejercicio, set_number=1,
                weight_kg=Decimal("50"), reps=8,
            )

        avance = foco(api, sesion)["avance"]

        assert avance == {"hechas": 2, "objetivo": 6}

    def test_trae_el_descanso_del_ejercicio_en_pantalla(self, api, sesion):
        assert foco(api, sesion)["actual"]["descanso"] == 180
        assert foco(api, sesion, ejercicio=2)["actual"]["descanso"] == 90

    def test_el_ejercicio_se_completa_con_su_ultima_serie(self, api, sesion, catalogo):
        registrar(sesion, catalogo["press"], 2)
        assert foco(api, sesion, ejercicio=1)["actual"]["completo"] is False

        registrar(sesion, catalogo["press"], 1)
        assert foco(api, sesion, ejercicio=1)["actual"]["completo"] is True

    def test_sin_indice_retoma_el_primero_con_series_pendientes(self, api, sesion, catalogo):
        registrar(sesion, catalogo["press"], 3)

        assert foco(api, sesion)["indice"] == 2
        assert foco(api, sesion, ejercicio=1)["indice"] == 1

    def test_el_siguiente_es_el_proximo_con_series_pendientes(self, api, sesion, catalogo):
        RoutineExercise.objects.create(
            routine=sesion.routine, exercise=catalogo["remo"], order=2, target_sets=3,
        )
        registrar(sesion, catalogo["fondos"], 3)

        assert foco(api, sesion)["siguiente"] == 3

    def test_el_siguiente_da_la_vuelta(self, api, sesion, catalogo):
        assert foco(api, sesion, ejercicio=2)["siguiente"] == 1

    def test_con_todo_hecho_no_hay_siguiente(self, api, sesion, catalogo):
        registrar(sesion, catalogo["press"], 3)
        registrar(sesion, catalogo["fondos"], 3)

        datos = foco(api, sesion, ejercicio=2)

        assert datos["actual"]["completo"] is True
        assert datos["siguiente"] is None

    def test_el_actual_no_es_su_propio_siguiente(self, api, sesion, catalogo):
        registrar(sesion, catalogo["fondos"], 3)

        assert foco(api, sesion)["siguiente"] is None

    def test_una_sesion_libre_no_revienta(self, api, ana):
        libre = WorkoutSession.objects.create(user=ana, date=timezone.localdate())

        datos = foco(api, libre)

        assert datos["actual"] is None
        assert datos["filas"] == []
        assert datos["total_ejercicios"] == 0

    def test_no_se_ve_el_foco_de_otra_persona(self, api, beto):
        ajena = WorkoutSession.objects.create(user=beto, date=timezone.localdate())

        respuesta = api.get(reverse("api-session-foco", args=[ajena.pk]))

        assert respuesta.status_code == 404


class TestRegistrarUnaSerie:
    def test_el_numero_lo_pone_el_servidor(self, api, sesion, catalogo):
        for _ in range(3):
            api.post(
                reverse("api-set-list"),
                {"session": sesion.pk, "exercise": catalogo["press"].pk,
                 "weight_kg": "80", "reps": 8},
                format="json",
            )

        numeros = list(sesion.sets.order_by("set_number").values_list("set_number", flat=True))
        assert numeros == [1, 2, 3]

    def test_cada_ejercicio_cuenta_por_su_cuenta(self, api, sesion, catalogo):
        api.post(
            reverse("api-set-list"),
            {"session": sesion.pk, "exercise": catalogo["press"].pk, "weight_kg": "80", "reps": 8},
            format="json",
        )
        api.post(
            reverse("api-set-list"),
            {"session": sesion.pk, "exercise": catalogo["fondos"].pk, "reps": 10},
            format="json",
        )

        assert sesion.sets.filter(exercise=catalogo["fondos"]).first().set_number == 1

    def test_se_puede_registrar_algo_que_no_estaba_planificado(self, api, sesion, catalogo):
        respuesta = api.post(
            reverse("api-set-list"),
            {"session": sesion.pk, "exercise": catalogo["remo"].pk, "weight_kg": "30", "reps": 10},
            format="json",
        )

        assert respuesta.status_code == 201

    def test_no_se_puede_registrar_contra_el_ejercicio_propio_de_otra_persona(
        self, api, ana, beto, catalogo
    ):
        suyo = Exercise.objects.create(
            external_id="", name="Rehab hombro operado", slug="rehab-hombro",
            body_part="chest", equipment="body weight",
            target_muscle=catalogo["press"].target_muscle,
            is_global=False, created_by=beto,
        )
        sesion_propia = WorkoutSession.objects.create(user=ana, date=timezone.localdate())

        respuesta = api.post(
            reverse("api-set-list"),
            {"session": sesion_propia.pk, "exercise": suyo.pk, "weight_kg": "1", "reps": 1},
            format="json",
        )

        assert respuesta.status_code == 400
        assert "Rehab hombro operado" not in respuesta.content.decode()
        assert not SetLog.objects.exists()

    def test_no_se_puede_registrar_en_la_sesion_de_otra_persona(self, api, beto, catalogo):
        ajena = WorkoutSession.objects.create(user=beto, date=timezone.localdate())

        respuesta = api.post(
            reverse("api-set-list"),
            {"session": ajena.pk, "exercise": catalogo["press"].pk, "weight_kg": "80", "reps": 8},
            format="json",
        )

        assert respuesta.status_code == 400
        assert not SetLog.objects.exists()

    def test_borrar_una_serie_no_toca_las_demas(self, api, sesion, catalogo):
        for numero in (1, 2):
            SetLog.objects.create(
                session=sesion, exercise=catalogo["press"], set_number=numero,
                weight_kg=Decimal("80"), reps=8,
            )
        primera = sesion.sets.get(set_number=1)

        api.delete(reverse("api-set-detail", args=[primera.pk]))

        assert sesion.sets.count() == 1

    def test_borrar_y_registrar_no_repite_numero(self, api, sesion, catalogo):
        registrar(sesion, catalogo["press"], 3)
        api.delete(reverse("api-set-detail", args=[sesion.sets.get(set_number=1).pk]))

        api.post(
            reverse("api-set-list"),
            {"session": sesion.pk, "exercise": catalogo["press"].pk, "weight_kg": "80", "reps": 8},
            format="json",
        )

        numeros = sorted(sesion.sets.values_list("set_number", flat=True))
        assert numeros == [1, 2, 3]

    def test_borrar_una_del_medio_cierra_el_hueco_sin_cambiar_el_orden(
        self, api, sesion, catalogo
    ):
        for numero, peso in enumerate(("60", "70", "80"), start=1):
            SetLog.objects.create(
                session=sesion, exercise=catalogo["press"], set_number=numero,
                weight_kg=Decimal(peso), reps=8,
            )

        api.delete(reverse("api-set-detail", args=[sesion.sets.get(set_number=2).pk]))

        quedan = list(sesion.sets.order_by("set_number").values_list("set_number", "weight_kg"))
        assert quedan == [(1, Decimal("60")), (2, Decimal("80"))]

    def test_borrar_no_renumera_otro_ejercicio(self, api, sesion, catalogo):
        registrar(sesion, catalogo["press"], 2)
        registrar(sesion, catalogo["fondos"], 2)

        api.delete(reverse("api-set-detail", args=[sesion.sets.get(
            exercise=catalogo["press"], set_number=1
        ).pk]))

        fondos = sorted(
            sesion.sets.filter(exercise=catalogo["fondos"]).values_list("set_number", flat=True)
        )
        assert fondos == [1, 2]

    def test_no_se_puede_borrar_la_serie_de_otra_persona(self, api, beto, catalogo):
        ajena = WorkoutSession.objects.create(user=beto, date=timezone.localdate())
        serie = SetLog.objects.create(
            session=ajena, exercise=catalogo["press"], set_number=1,
            weight_kg=Decimal("80"), reps=8,
        )

        respuesta = api.delete(reverse("api-set-detail", args=[serie.pk]))

        assert respuesta.status_code == 404
        assert SetLog.objects.filter(pk=serie.pk).exists()

    def test_corregir_una_serie_cambia_kilos_y_reps_y_conserva_su_numero(
        self, api, sesion, catalogo
    ):
        registrar(sesion, catalogo["press"], 2)
        primera = sesion.sets.get(set_number=1)

        respuesta = api.patch(
            reverse("api-set-detail", args=[primera.pk]),
            {"weight_kg": "85", "reps": 6},
            format="json",
        )

        assert respuesta.status_code == 200
        primera.refresh_from_db()
        assert (primera.weight_kg, primera.reps, primera.set_number) == (Decimal("85"), 6, 1)

    def test_corregir_puede_dejar_la_serie_sin_peso(self, api, sesion, catalogo):
        registrar(sesion, catalogo["fondos"], 1)
        serie = sesion.sets.get()

        api.patch(
            reverse("api-set-detail", args=[serie.pk]),
            {"weight_kg": None, "reps": 12},
            format="json",
        )

        serie.refresh_from_db()
        assert serie.weight_kg is None
        assert serie.reps == 12

    def test_no_se_puede_corregir_la_serie_de_otra_persona(self, api, beto, catalogo):
        ajena = WorkoutSession.objects.create(user=beto, date=timezone.localdate())
        serie = SetLog.objects.create(
            session=ajena, exercise=catalogo["press"], set_number=1,
            weight_kg=Decimal("80"), reps=8,
        )

        respuesta = api.patch(
            reverse("api-set-detail", args=[serie.pk]), {"reps": 1}, format="json"
        )

        assert respuesta.status_code == 404
        serie.refresh_from_db()
        assert serie.reps == 8

    def test_un_get_no_borra_una_serie(self, api, sesion, catalogo):
        serie = SetLog.objects.create(
            session=sesion, exercise=catalogo["press"], set_number=1,
            weight_kg=Decimal("80"), reps=8,
        )

        api.get(reverse("api-set-detail", args=[serie.pk]))

        assert SetLog.objects.filter(pk=serie.pk).exists()

    def test_los_ejercicios_recientes_son_los_usados_y_los_planificados(
        self, api, ana, sesion, catalogo
    ):
        SetLog.objects.create(
            session=sesion, exercise=catalogo["remo"], set_number=1,
            weight_kg=Decimal("30"), reps=10,
        )

        nombres = [e["nombre"] for e in api.get(reverse("api-session-ejercicios-recientes")).json()]

        assert set(nombres) == {"Fondos", "Press de banca", "Remo a una mano"}


class TestElCierre:
    def test_finalizar_marca_la_hora_y_devuelve_el_resumen(self, api, sesion, catalogo):
        SetLog.objects.create(
            session=sesion, exercise=catalogo["press"], set_number=1,
            weight_kg=Decimal("80"), reps=10,
        )

        datos = api.post(reverse("api-session-finalizar", args=[sesion.pk])).json()

        sesion.refresh_from_db()
        assert sesion.finished_at is not None
        assert datos["series"] == 1
        assert datos["ejercicios"] == 1
        assert datos["tonelaje_kg"] == 800

    def test_finalizar_dos_veces_no_alarga_el_entrenamiento(self, api, sesion):
        primera = api.post(reverse("api-session-finalizar", args=[sesion.pk])).json()
        sesion.refresh_from_db()
        marca = sesion.finished_at

        segunda = api.post(reverse("api-session-finalizar", args=[sesion.pk])).json()

        sesion.refresh_from_db()
        assert sesion.finished_at == marca
        assert primera["duracion_minutos"] == segunda["duracion_minutos"]

    def test_el_resumen_se_puede_pedir_sin_cerrar(self, api, sesion):
        api.get(reverse("api-session-resumen", args=[sesion.pk]))

        sesion.refresh_from_db()
        assert sesion.finished_at is None

    def test_el_tonelaje_cuenta_los_dos_lados_de_un_unilateral(self, api, sesion, catalogo):
        SetLog.objects.create(
            session=sesion, exercise=catalogo["remo"], set_number=1,
            weight_kg=Decimal("30"), reps=10,
        )

        datos = api.get(reverse("api-session-resumen", args=[sesion.pk])).json()

        assert datos["tonelaje_kg"] == 600

    def test_el_peso_corporal_cuenta_en_una_dominada(self, api, ana, sesion, catalogo):
        BodyWeightEntry.objects.create(
            user=ana, date=timezone.localdate(), weight_kg=Decimal("75")
        )
        SetLog.objects.create(
            session=sesion, exercise=catalogo["fondos"], set_number=1, reps=10,
        )

        datos = api.get(reverse("api-session-resumen", args=[sesion.pk])).json()

        assert datos["tonelaje_kg"] == 750

    def test_sin_peso_registrado_la_serie_no_cuenta_y_se_dice(self, api, sesion, catalogo):
        SetLog.objects.create(
            session=sesion, exercise=catalogo["fondos"], set_number=1, reps=10,
        )

        datos = api.get(reverse("api-session-resumen", args=[sesion.pk])).json()

        assert datos["tonelaje_kg"] == 0
        assert datos["series_sin_cobertura"] == 1

    def test_un_record_es_superar_lo_anterior(self, api, ana, sesion, catalogo):
        anterior = WorkoutSession.objects.create(
            user=ana, date=timezone.localdate() - timedelta(days=7), finished_at=timezone.now()
        )
        SetLog.objects.create(
            session=anterior, exercise=catalogo["press"], set_number=1,
            weight_kg=Decimal("80"), reps=8,
        )
        SetLog.objects.create(
            session=sesion, exercise=catalogo["press"], set_number=1,
            weight_kg=Decimal("85"), reps=6,
        )

        datos = api.get(reverse("api-session-resumen", args=[sesion.pk])).json()

        assert datos["records"] == [{"ejercicio": "Press de banca", "kg": "85"}]

    def test_la_segunda_serie_de_hoy_no_es_record_por_superar_a_la_primera(
        self, api, ana, sesion, catalogo
    ):
        anterior = WorkoutSession.objects.create(
            user=ana, date=timezone.localdate() - timedelta(days=7), finished_at=timezone.now()
        )
        SetLog.objects.create(
            session=anterior, exercise=catalogo["press"], set_number=1,
            weight_kg=Decimal("90"), reps=8,
        )
        for numero, peso in enumerate([Decimal("70"), Decimal("80")], start=1):
            SetLog.objects.create(
                session=sesion, exercise=catalogo["press"], set_number=numero,
                weight_kg=peso, reps=8,
            )

        datos = api.get(reverse("api-session-resumen", args=[sesion.pk])).json()

        assert datos["records"] == []

    def test_un_ejercicio_nuevo_no_es_record(self, api, sesion, catalogo):
        SetLog.objects.create(
            session=sesion, exercise=catalogo["press"], set_number=1,
            weight_kg=Decimal("80"), reps=8,
        )

        datos = api.get(reverse("api-session-resumen", args=[sesion.pk])).json()

        assert datos["records"] == []

    def test_dice_qué_musculos_se_han_trabajado(self, api, sesion, catalogo):
        SetLog.objects.create(
            session=sesion, exercise=catalogo["press"], set_number=1,
            weight_kg=Decimal("80"), reps=8,
        )

        datos = api.get(reverse("api-session-resumen", args=[sesion.pk])).json()

        assert datos["musculos"] == ["Pectorales", "Tríceps"]

    def test_sin_hora_de_arranque_la_duracion_es_nula_y_no_cero(self, api, ana):
        sin_arranque = WorkoutSession.objects.create(user=ana, date=timezone.localdate())

        datos = api.post(reverse("api-session-finalizar", args=[sin_arranque.pk])).json()

        assert datos["duracion_minutos"] is None

    def test_no_se_puede_cerrar_la_sesion_de_otra_persona(self, api, beto):
        ajena = WorkoutSession.objects.create(user=beto, date=timezone.localdate())

        respuesta = api.post(reverse("api-session-finalizar", args=[ajena.pk]))

        assert respuesta.status_code == 404
        ajena.refresh_from_db()
        assert ajena.finished_at is None

    def test_cerrar_exige_post(self, api, sesion):
        respuesta = api.get(reverse("api-session-finalizar", args=[sesion.pk]))

        assert respuesta.status_code == 405
        sesion.refresh_from_db()
        assert sesion.finished_at is None


def serie(api, sesion, ejercicio, **extra):
    return api.post(
        reverse("api-set-list"),
        {"session": sesion.pk, "exercise": ejercicio.pk, "weight_kg": "50", "reps": 8, **extra},
        format="json",
    )


def accion(api, sesion, nombre):
    return api.post(
        reverse("api-session-descanso", args=[sesion.pk]), {"accion": nombre}, format="json"
    )


class TestElDescanso:
    def test_registrar_arranca_el_descanso_del_ejercicio(self, api, sesion, catalogo):
        respuesta = serie(api, sesion, catalogo["press"])

        assert respuesta.status_code == 201
        assert respuesta.json()["descanso"]["total"] == 180
        assert 179 <= respuesta.json()["descanso"]["restante"] <= 180
        sesion.refresh_from_db()
        assert sesion.rest_seconds == 180

    def test_el_foco_lo_da_en_segundos_que_quedan_y_no_como_hora(self, api, sesion, catalogo):
        serie(api, sesion, catalogo["press"])

        en_curso = foco(api, sesion, ejercicio=1)["descanso_en_curso"]

        assert set(en_curso) == {"restante", "total"}
        assert isinstance(en_curso["restante"], float)

    def test_un_descanso_terminado_no_se_devuelve(self, api, sesion):
        sesion.rest_ends_at = timezone.now() - timedelta(seconds=1)
        sesion.rest_seconds = 90
        sesion.save()

        assert foco(api, sesion, ejercicio=1)["descanso_en_curso"] is None

    def test_corregir_o_borrar_una_serie_no_lo_toca(self, api, sesion, catalogo):
        creada = serie(api, sesion, catalogo["press"]).json()
        sesion.refresh_from_db()
        antes = sesion.rest_ends_at

        api.patch(reverse("api-set-detail", args=[creada["id"]]), {"reps": 6}, format="json")
        sesion.refresh_from_db()
        assert sesion.rest_ends_at == antes

        api.delete(reverse("api-set-detail", args=[creada["id"]]))
        sesion.refresh_from_db()
        assert sesion.rest_ends_at == antes

    def test_tras_la_ultima_serie_pendiente_no_hay_descanso(self, api, sesion, catalogo):
        registrar(sesion, catalogo["press"], 3)
        registrar(sesion, catalogo["fondos"], 2)
        serie(api, sesion, catalogo["press"])
        sesion.refresh_from_db()
        assert sesion.rest_ends_at is not None

        respuesta = serie(api, sesion, catalogo["fondos"])

        assert respuesta.json()["descanso"] is None
        sesion.refresh_from_db()
        assert sesion.rest_ends_at is None

    def test_una_serie_de_mas_con_todo_hecho_si_descansa(self, api, sesion, catalogo):
        registrar(sesion, catalogo["press"], 3)
        registrar(sesion, catalogo["fondos"], 3)

        assert serie(api, sesion, catalogo["fondos"]).json()["descanso"]["total"] == 90

    def test_un_ejercicio_repetido_usa_el_descanso_de_la_fila_que_llena(
        self, api, ana, catalogo
    ):
        rutina = Routine.objects.create(user=ana, name="Pirámide")
        RoutineExercise.objects.create(
            routine=rutina, exercise=catalogo["press"], order=0,
            target_sets=3, target_reps_min=6, target_reps_max=8, rest_seconds=180,
        )
        RoutineExercise.objects.create(
            routine=rutina, exercise=catalogo["press"], order=1,
            target_sets=2, target_reps_min=10, target_reps_max=12, rest_seconds=60,
        )
        sesion = WorkoutSession.objects.create(user=ana, routine=rutina, date=timezone.localdate())
        registrar(sesion, catalogo["press"], 3)

        assert serie(api, sesion, catalogo["press"]).json()["descanso"]["total"] == 60
        datos = foco(api, sesion, ejercicio=1)
        assert [p["hechas"] for p in datos["planificados"]] == [3, 1]
        assert datos["siguiente"] == 2

    def test_en_una_sesion_libre_usa_el_descanso_del_ejercicio(self, api, ana, catalogo):
        libre = WorkoutSession.objects.create(user=ana, date=timezone.localdate())

        assert serie(api, libre, catalogo["press"]).json()["descanso"]["total"] == 180
        assert serie(api, libre, catalogo["fondos"]).json()["descanso"]["total"] == 90

    def test_un_descanso_configurado_a_cero_no_arranca(self, api, sesion, rutina, catalogo):
        rutina.exercises.filter(exercise=catalogo["press"]).update(rest_seconds=0)

        assert serie(api, sesion, catalogo["press"]).json()["descanso"] is None

    def test_terminar_lo_quita(self, api, sesion, catalogo):
        serie(api, sesion, catalogo["press"])

        api.post(reverse("api-session-finalizar", args=[sesion.pk]))

        sesion.refresh_from_db()
        assert sesion.rest_ends_at is None

    def test_alargar_suma_treinta_segundos_al_fin_y_al_total(self, api, sesion, catalogo):
        serie(api, sesion, catalogo["press"])
        sesion.refresh_from_db()
        antes = sesion.rest_ends_at

        respuesta = accion(api, sesion, "alargar")

        assert respuesta.json()["descanso"]["total"] == 210
        sesion.refresh_from_db()
        assert sesion.rest_ends_at == antes + timedelta(seconds=30)

    def test_alargar_tiene_tope(self, api, sesion, catalogo, settings):
        settings.REST_FRAMEWORK = {
            **settings.REST_FRAMEWORK,
            "DEFAULT_THROTTLE_RATES": {
                **settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"], "user": "10000/day",
            },
        }
        serie(api, sesion, catalogo["press"])
        for _ in range(60):
            accion(api, sesion, "alargar")

        sesion.refresh_from_db()
        assert sesion.rest_seconds == 30 * 60

    def test_sin_descanso_alargar_no_crea_uno(self, api, sesion):
        respuesta = accion(api, sesion, "alargar")

        assert respuesta.status_code == 200
        assert respuesta.json()["descanso"] is None

    def test_saltar_lo_quita(self, api, sesion, catalogo):
        serie(api, sesion, catalogo["press"])

        assert accion(api, sesion, "saltar").json()["descanso"] is None
        assert foco(api, sesion, ejercicio=1)["descanso_en_curso"] is None

    def test_una_accion_desconocida_es_un_400(self, api, sesion):
        assert accion(api, sesion, "pausar").status_code == 400

    def test_no_se_toca_el_descanso_de_otra_persona(self, api, beto):
        ajena = WorkoutSession.objects.create(user=beto, date=timezone.localdate())

        assert accion(api, ajena, "saltar").status_code == 404

    def test_solo_por_post(self, api, sesion):
        assert api.get(reverse("api-session-descanso", args=[sesion.pk])).status_code == 405
