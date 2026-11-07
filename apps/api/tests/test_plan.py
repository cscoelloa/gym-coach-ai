import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

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
    return {
        "press": Exercise.objects.create(
            external_id="0001", name="Press de banca", slug="press-banca",
            body_part="chest", equipment="barbell", target_muscle=pecho,
        ),
        "fondos": Exercise.objects.create(
            external_id="0002", name="Fondos", slug="fondos",
            body_part="chest", equipment="body weight", target_muscle=pecho,
        ),
    }


@pytest.fixture
def rutina(ana):
    return Routine.objects.create(user=ana, name="Empuje A")


@pytest.fixture
def programa(ana, rutina):
    p = Program.objects.create(user=ana, name="Volumen", is_active=True)
    for dia in range(7):
        ScheduleEntry.objects.create(program=p, weekday=dia, routine=rutina if dia == 0 else None)
    return p


class TestLaPantallaDePlan:
    def test_sin_programa_lo_dice_sin_reventar(self, api):
        datos = api.get(reverse("api-plan")).json()

        assert datos["programa"] is None
        assert datos["programas"] == []
        assert len(datos["semana"]) == 7

    def test_la_semana_trae_siempre_los_siete_dias(self, api, ana, rutina):
        p = Program.objects.create(user=ana, name="Cojo", is_active=True)
        ScheduleEntry.objects.create(program=p, weekday=0, routine=rutina)

        semana = api.get(reverse("api-plan")).json()["semana"]

        assert [dia["weekday"] for dia in semana] == [0, 1, 2, 3, 4, 5, 6]
        assert semana[0]["rutina"]["nombre"] == "Empuje A"
        assert semana[0]["rutina"]["n_ejercicios"] == 0
        assert semana[3]["rutina"] is None

    def test_las_rutinas_dicen_cuantos_ejercicios_y_en_qué_días_están(
        self, api, programa, rutina, catalogo
    ):
        RoutineExercise.objects.create(routine=rutina, exercise=catalogo["press"], order=0)

        fila = api.get(reverse("api-plan")).json()["rutinas"][0]

        assert fila["n_ejercicios"] == 1
        assert fila["dias"] == ["Lunes"]
        assert fila["imagenes"] == []

    def test_la_rutina_trae_portada_con_las_imagenes_de_sus_ejercicios(
        self, api, programa, rutina, catalogo
    ):
        catalogo["press"].image = "exercises/images/press.png"
        catalogo["press"].save(update_fields=["image"])
        RoutineExercise.objects.create(routine=rutina, exercise=catalogo["press"], order=0)
        RoutineExercise.objects.create(routine=rutina, exercise=catalogo["fondos"], order=1)

        fila = api.get(reverse("api-plan")).json()["rutinas"][0]

        assert len(fila["imagenes"]) == 1
        assert fila["imagenes"][0].endswith("exercises/images/press.png")

    def test_los_dias_son_solo_los_del_programa_activo(self, api, ana, programa, rutina):
        otro = Program.objects.create(user=ana, name="Viejo", is_active=False)
        ScheduleEntry.objects.create(program=otro, weekday=2, routine=rutina)

        fila = api.get(reverse("api-plan")).json()["rutinas"][0]

        assert fila["dias"] == ["Lunes"]

    def test_no_se_ve_el_plan_de_otra_persona(self, api, beto):
        ajena = Routine.objects.create(user=beto, name="Rutina de Beto")
        p = Program.objects.create(user=beto, name="De Beto", is_active=True)
        ScheduleEntry.objects.create(program=p, weekday=0, routine=ajena)

        datos = api.get(reverse("api-plan")).json()

        assert datos["programa"] is None
        assert datos["rutinas"] == []

    def test_sin_sesion_no_se_ve(self):
        assert APIClient().get(reverse("api-plan")).status_code in (401, 403)


class TestAsignarUnaRutinaAUnDia:
    def test_asigna(self, api, programa, rutina):
        entrada = programa.schedule.get(weekday=2)

        respuesta = api.patch(
            reverse("api-schedule-entry-detail", args=[entrada.pk]),
            {"routine": rutina.pk},
            format="json",
        )

        assert respuesta.status_code == 200
        entrada.refresh_from_db()
        assert entrada.routine == rutina

    def test_dejarlo_en_descanso_es_mandar_null(self, api, programa):
        entrada = programa.schedule.get(weekday=0)

        api.patch(
            reverse("api-schedule-entry-detail", args=[entrada.pk]),
            {"routine": None},
            format="json",
        )

        entrada.refresh_from_db()
        assert entrada.routine is None

    def test_no_se_puede_asignar_la_rutina_de_otra_persona(self, api, programa, beto):
        ajena = Routine.objects.create(user=beto, name="Ajena")
        entrada = programa.schedule.get(weekday=1)

        respuesta = api.patch(
            reverse("api-schedule-entry-detail", args=[entrada.pk]),
            {"routine": ajena.pk},
            format="json",
        )

        assert respuesta.status_code == 400
        entrada.refresh_from_db()
        assert entrada.routine is None

    def test_no_se_puede_tocar_el_dia_de_otra_persona(self, api, beto):
        p = Program.objects.create(user=beto, name="De Beto", is_active=True)
        entrada = ScheduleEntry.objects.create(program=p, weekday=0)

        respuesta = api.patch(
            reverse("api-schedule-entry-detail", args=[entrada.pk]),
            {"routine": None},
            format="json",
        )

        assert respuesta.status_code == 404


class TestAnadirUnEjercicio:
    def anadir(self, api, rutina, ejercicio, **extra):
        return api.post(
            reverse("api-routine-exercise-list"),
            {"routine": rutina.pk, "exercise": ejercicio.pk, **extra},
            format="json",
        )

    def test_entra_ya_configurado(self, api, rutina, catalogo):
        respuesta = self.anadir(
            api, rutina, catalogo["press"],
            target_sets=4, target_reps_min=6, target_reps_max=8, rest_seconds=150,
        )

        assert respuesta.status_code == 201
        item = RoutineExercise.objects.get()
        assert (item.target_sets, item.target_reps_min, item.target_reps_max) == (4, 6, 8)
        assert item.rest_seconds == 150

    @pytest.mark.parametrize(
        "clave,descanso", [("press", 180), ("fondos", 90)]
    )
    def test_el_descanso_por_defecto_depende_del_material(
        self, api, rutina, catalogo, clave, descanso
    ):
        self.anadir(api, rutina, catalogo[clave])

        assert RoutineExercise.objects.get().rest_seconds == descanso

    def test_se_coloca_al_final_sin_que_el_cliente_lo_diga(self, api, rutina, catalogo):
        self.anadir(api, rutina, catalogo["press"])
        self.anadir(api, rutina, catalogo["fondos"])

        ordenes = list(rutina.exercises.order_by("order").values_list("exercise__name", "order"))
        assert ordenes == [("Press de banca", 0), ("Fondos", 1)]

    def test_un_minimo_por_encima_del_maximo_arrastra_el_maximo(self, api, rutina, catalogo):
        self.anadir(api, rutina, catalogo["press"], target_reps_min=12, target_reps_max=8)

        item = RoutineExercise.objects.get()
        assert (item.target_reps_min, item.target_reps_max) == (12, 12)

    def test_no_se_puede_añadir_a_la_rutina_de_otra_persona(self, api, beto, catalogo):
        ajena = Routine.objects.create(user=beto, name="Ajena")

        respuesta = self.anadir(api, ajena, catalogo["press"])

        assert respuesta.status_code == 400
        assert not RoutineExercise.objects.exists()

    def test_no_se_puede_meter_el_ejercicio_propio_de_otra_persona(
        self, api, rutina, beto, catalogo
    ):
        suyo = Exercise.objects.create(
            name="Secreto", slug="secreto", body_part="chest", equipment="barbell",
            is_global=False, created_by=beto,
        )

        respuesta = self.anadir(api, rutina, suyo)

        assert respuesta.status_code == 400


class TestEditarYReordenar:
    @pytest.fixture
    def items(self, rutina, catalogo):
        return [
            RoutineExercise.objects.create(
                routine=rutina, exercise=catalogo["press"], order=0, rest_seconds=180
            ),
            RoutineExercise.objects.create(
                routine=rutina, exercise=catalogo["fondos"], order=1, rest_seconds=90
            ),
        ]

    def test_guarda_la_configuracion(self, api, items):
        api.patch(
            reverse("api-routine-exercise-detail", args=[items[0].pk]),
            {"target_sets": 5, "rest_seconds": 120},
            format="json",
        )

        items[0].refresh_from_db()
        assert items[0].target_sets == 5
        assert items[0].rest_seconds == 120

    def test_bajar_el_primero_lo_pone_segundo(self, api, rutina, items):
        respuesta = api.post(
            reverse("api-routine-exercise-mover", args=[items[0].pk]),
            {"direccion": "bajar"},
            format="json",
        )

        assert respuesta.status_code == 200
        assert [fila["id"] for fila in respuesta.json()] == [items[1].pk, items[0].pk]

    def test_subir_el_primero_no_hace_nada(self, api, rutina, items):
        api.post(
            reverse("api-routine-exercise-mover", args=[items[0].pk]),
            {"direccion": "subir"},
            format="json",
        )

        assert list(rutina.exercises.order_by("order").values_list("pk", flat=True)) == [
            items[0].pk, items[1].pk
        ]

    def test_reordena_aunque_los_ordenes_vinieran_repetidos(self, api, rutina, items):
        RoutineExercise.objects.filter(routine=rutina).update(order=0)

        api.post(
            reverse("api-routine-exercise-mover", args=[items[1].pk]),
            {"direccion": "subir"},
            format="json",
        )

        assert list(rutina.exercises.order_by("order").values_list("pk", flat=True)) == [
            items[1].pk, items[0].pk
        ]

    def test_una_direccion_inventada_se_rechaza(self, api, items):
        respuesta = api.post(
            reverse("api-routine-exercise-mover", args=[items[0].pk]),
            {"direccion": "aleatorio"},
            format="json",
        )

        assert respuesta.status_code == 400

    def test_mover_exige_post(self, api, items):
        respuesta = api.get(reverse("api-routine-exercise-mover", args=[items[0].pk]))

        assert respuesta.status_code == 405

    def test_no_se_puede_mover_lo_de_otra_persona(self, api, beto, catalogo):
        ajena = Routine.objects.create(user=beto, name="Ajena")
        suyo = RoutineExercise.objects.create(
            routine=ajena, exercise=catalogo["press"], order=0
        )

        respuesta = api.post(
            reverse("api-routine-exercise-mover", args=[suyo.pk]),
            {"direccion": "bajar"},
            format="json",
        )

        assert respuesta.status_code == 404

    def test_quitar_uno_no_borra_el_ejercicio_del_catalogo(self, api, items, catalogo):
        api.delete(reverse("api-routine-exercise-detail", args=[items[0].pk]))

        assert not RoutineExercise.objects.filter(pk=items[0].pk).exists()
        assert Exercise.objects.filter(pk=catalogo["press"].pk).exists()


class TestBorrarUnaRutina:
    def test_los_dias_que_la_tenian_pasan_a_descanso(self, api, programa, rutina):
        api.delete(reverse("api-routine-detail", args=[rutina.pk]))

        entrada = programa.schedule.get(weekday=0)
        assert entrada.routine is None

    def test_no_se_puede_borrar_la_de_otra_persona(self, api, beto):
        ajena = Routine.objects.create(user=beto, name="Ajena")

        respuesta = api.delete(reverse("api-routine-detail", args=[ajena.pk]))

        assert respuesta.status_code == 404
        assert Routine.objects.filter(pk=ajena.pk).exists()


class TestGuardadoCompleto:
    def fila(self, ejercicio, **extra):
        return {
            "exercise": ejercicio.pk,
            "target_sets": 4,
            "target_reps_min": 6,
            "target_reps_max": 8,
            "rest_seconds": 180,
            **extra,
        }

    def test_crea_rutina_y_lista_en_orden(self, api, ana, catalogo):
        response = api.post(
            "/api/rutinas/",
            {
                "name": "Completa",
                "exercises": [self.fila(catalogo["fondos"]), self.fila(catalogo["press"])],
            },
            format="json",
        )
        assert response.status_code == 201
        rows = response.json()["exercises"]
        assert [row["exercise"] for row in rows] == [catalogo["fondos"].pk, catalogo["press"].pk]
        assert [row["order"] for row in rows] == [0, 1]
        assert rows[0]["exercise_detail"]["name"] == "Fondos"
        assert Routine.objects.get(pk=response.json()["id"]).user == ana

    def test_edita_conserva_ids_quita_y_reordena(self, api, rutina, catalogo):
        first = RoutineExercise.objects.create(routine=rutina, exercise=catalogo["press"])
        deleted = RoutineExercise.objects.create(routine=rutina, exercise=catalogo["fondos"])
        response = api.patch(
            f"/api/rutinas/{rutina.pk}/",
            {
                "name": "Editada",
                "exercises": [
                    self.fila(catalogo["fondos"]),
                    self.fila(catalogo["press"], id=first.pk, target_sets=5),
                ],
            },
            format="json",
        )
        assert response.status_code == 200
        rows = response.json()["exercises"]
        assert rows[1]["id"] == first.pk
        assert rows[1]["target_sets"] == 5
        assert not RoutineExercise.objects.filter(pk=deleted.pk).exists()
        rutina.refresh_from_db()
        assert rutina.name == "Editada"

    def test_un_error_no_modifica_nombre_ni_ejercicios(self, api, rutina, catalogo):
        item = RoutineExercise.objects.create(routine=rutina, exercise=catalogo["press"])
        response = api.patch(
            f"/api/rutinas/{rutina.pk}/",
            {
                "name": "No guardar",
                "exercises": [
                    self.fila(catalogo["press"], id=item.pk),
                    self.fila(catalogo["fondos"], target_sets=99),
                ],
            },
            format="json",
        )
        assert response.status_code == 400
        rutina.refresh_from_db()
        assert rutina.name == "Empuje A"
        assert list(rutina.exercises.values_list("pk", flat=True)) == [item.pk]

    def test_rollback_si_falla_la_escritura(self, api, rutina, catalogo, monkeypatch):
        original = RoutineExercise.save

        def fallo(self, *args, **kwargs):
            if self.exercise_id == catalogo["fondos"].pk:
                raise RuntimeError("fallo simulado")
            return original(self, *args, **kwargs)

        monkeypatch.setattr(RoutineExercise, "save", fallo)
        with pytest.raises(RuntimeError, match="fallo simulado"):
            api.patch(
                f"/api/rutinas/{rutina.pk}/",
                {
                    "name": "No guardar",
                    "exercises": [self.fila(catalogo["press"]), self.fila(catalogo["fondos"])],
                },
                format="json",
            )
        rutina.refresh_from_db()
        assert rutina.name == "Empuje A"
        assert not rutina.exercises.exists()

    def test_rechaza_elementos_ajenos_y_duplicados(self, api, rutina, beto, catalogo):
        other = Routine.objects.create(user=beto, name="Ajena")
        item = RoutineExercise.objects.create(routine=other, exercise=catalogo["press"])
        response = api.patch(
            f"/api/rutinas/{rutina.pk}/",
            {"exercises": [self.fila(catalogo["press"], id=item.pk)]},
            format="json",
        )
        assert response.status_code == 404
        assert (
            api.patch(f"/api/rutinas/{other.pk}/", {"name": "Otro"}, format="json").status_code
            == 404
        )
        item = RoutineExercise.objects.create(routine=rutina, exercise=catalogo["press"])
        fila = self.fila(catalogo["press"], id=item.pk)
        assert (
            api.patch(
                f"/api/rutinas/{rutina.pk}/", {"exercises": [fila, fila]}, format="json"
            ).status_code
            == 400
        )

    def test_no_admite_ejercicio_privado_de_otro(self, api, beto, catalogo):
        ejercicio = catalogo["press"]
        ejercicio.is_global = False
        ejercicio.created_by = beto
        ejercicio.save()
        response = api.post(
            "/api/rutinas/",
            {"name": "No crear", "exercises": [self.fila(ejercicio)]},
            format="json",
        )
        assert response.status_code == 400
        assert not Routine.objects.filter(name="No crear").exists()

    def test_omitir_lista_conserva_elementos_y_el_historial(self, api, rutina, catalogo, ana):
        from apps.workouts.models import SetLog, WorkoutSession

        item = RoutineExercise.objects.create(routine=rutina, exercise=catalogo["press"])
        session = WorkoutSession.objects.create(user=ana, routine=rutina, date="2026-09-20")
        registro = SetLog.objects.create(
            session=session, exercise=catalogo["press"], set_number=1, reps=8, weight_kg=20
        )
        assert (
            api.patch(
                f"/api/rutinas/{rutina.pk}/", {"name": "Nuevo nombre"}, format="json"
            ).status_code
            == 200
        )
        assert rutina.exercises.get().pk == item.pk
        assert (
            api.patch(f"/api/rutinas/{rutina.pk}/", {"exercises": []}, format="json").status_code
            == 200
        )
        assert SetLog.objects.filter(pk=registro.pk).exists()


    def test_patch_con_lista_exige_configuracion_completa(self, api, rutina, catalogo):
        item = RoutineExercise.objects.create(
            routine=rutina, exercise=catalogo["press"], target_reps_max=8,
        )
        response = api.patch(f"/api/rutinas/{rutina.pk}/", {
            "exercises": [{"id": item.pk, "exercise": catalogo["press"].pk,
                           "target_reps_min": 12}],
        }, format="json")
        assert response.status_code == 400
        item.refresh_from_db()
        assert item.target_reps_min == 8
        assert item.target_reps_max == 8


class TestEjerciciosDeMisRutinas:
    def url(self):
        return reverse("api-routine-ejercicios")

    @pytest.fixture
    def pierna(self, ana, catalogo):
        pierna = Routine.objects.create(user=ana, name="Pierna")
        RoutineExercise.objects.create(
            routine=pierna, exercise=catalogo["fondos"], order=1,
            target_sets=3, target_reps_min=10, target_reps_max=12, rest_seconds=90,
        )
        RoutineExercise.objects.create(
            routine=pierna, exercise=catalogo["press"], order=0,
            target_sets=5, target_reps_min=5, target_reps_max=5, rest_seconds=120,
        )
        return pierna

    def nombres(self, respuesta):
        return [
            (r["name"], [e["exercise_detail"]["name"] for e in r["exercises"]])
            for r in respuesta.json()
        ]

    def test_trae_mis_rutinas_con_sus_ejercicios_en_orden_y_su_configuracion(
        self, api, pierna, rutina, catalogo
    ):
        RoutineExercise.objects.create(routine=rutina, exercise=catalogo["fondos"])

        respuesta = api.get(self.url())

        assert respuesta.status_code == 200
        assert self.nombres(respuesta) == [
            ("Empuje A", ["Fondos"]),
            ("Pierna", ["Press de banca", "Fondos"]),
        ]
        press = respuesta.json()[1]["exercises"][0]
        assert (press["target_sets"], press["target_reps_min"], press["target_reps_max"]) == (
            5, 5, 5,
        )
        assert press["rest_seconds"] == 120

    def test_una_rutina_vacia_no_sale(self, api, rutina, pierna):
        assert self.nombres(api.get(self.url())) == [("Pierna", ["Press de banca", "Fondos"])]

    def test_excluir_quita_la_rutina_que_se_esta_editando(self, api, pierna, rutina, catalogo):
        RoutineExercise.objects.create(routine=rutina, exercise=catalogo["fondos"])

        respuesta = api.get(self.url(), {"excluir": pierna.pk})

        assert self.nombres(respuesta) == [("Empuje A", ["Fondos"])]

    @pytest.mark.parametrize("excluir", ["abc", "-1", "99999999999999999999999999"])
    def test_un_excluir_raro_no_rompe_nada(self, api, pierna, excluir):
        respuesta = api.get(self.url(), {"excluir": excluir})

        assert respuesta.status_code == 200
        assert self.nombres(respuesta) == [("Pierna", ["Press de banca", "Fondos"])]

    def test_el_texto_filtra_por_nombre_y_omite_las_rutinas_sin_coincidencias(
        self, api, pierna, rutina, catalogo
    ):
        RoutineExercise.objects.create(routine=rutina, exercise=catalogo["fondos"])

        respuesta = api.get(self.url(), {"q": "pRESs"})

        assert self.nombres(respuesta) == [("Pierna", ["Press de banca"])]

    def test_nunca_salen_las_rutinas_de_otra_persona(self, api, beto, catalogo, pierna):
        ajena = Routine.objects.create(user=beto, name="Secreta")
        RoutineExercise.objects.create(routine=ajena, exercise=catalogo["press"])

        assert self.nombres(api.get(self.url())) == [("Pierna", ["Press de banca", "Fondos"])]
        assert self.nombres(api.get(self.url(), {"excluir": ajena.pk})) == [
            ("Pierna", ["Press de banca", "Fondos"])
        ]

    def test_sin_sesion_no_hay_datos(self, pierna):
        respuesta = APIClient().get(self.url())

        assert respuesta.status_code == 401

    def test_no_consulta_una_vez_por_ejercicio(
        self, api, ana, catalogo, pierna, django_assert_max_num_queries
    ):
        for n in range(5):
            otra = Routine.objects.create(user=ana, name=f"Otra {n}")
            for orden, clave in enumerate(("press", "fondos")):
                RoutineExercise.objects.create(
                    routine=otra, exercise=catalogo[clave], order=orden
                )

        with django_assert_max_num_queries(8):
            respuesta = api.get(self.url())

        assert len(respuesta.json()) == 6
