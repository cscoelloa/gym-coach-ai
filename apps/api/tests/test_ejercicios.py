import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from apps.workouts.models import Exercise, MuscleGroup

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
def musculos():
    return {
        "pecho": MuscleGroup.objects.create(slug="pectorals", name="Pectorales"),
        "triceps": MuscleGroup.objects.create(slug="triceps", name="Tríceps"),
        "cuadriceps": MuscleGroup.objects.create(slug="quads", name="Cuádriceps"),
    }


@pytest.fixture
def catalogo(musculos):
    press = Exercise.objects.create(
        external_id="0001", name="Press de banca", slug="press-banca",
        body_part="chest", equipment="barbell", target_muscle=musculos["pecho"],
    )
    press.secondary_muscles.add(musculos["triceps"])

    fondos = Exercise.objects.create(
        external_id="0002", name="Fondos", slug="fondos",
        body_part="chest", equipment="body weight", target_muscle=musculos["pecho"],
    )
    fondos.secondary_muscles.add(musculos["triceps"])

    sentadilla = Exercise.objects.create(
        external_id="0003", name="Sentadilla", slug="sentadilla",
        body_part="upper legs", equipment="barbell", target_muscle=musculos["cuadriceps"],
    )
    return {"press": press, "fondos": fondos, "sentadilla": sentadilla}


def nombres(respuesta):
    return [fila["name"] for fila in respuesta.json()["results"]]


class TestBuscarYFiltrar:
    def test_lista_el_catalogo_ordenado(self, api, catalogo):
        assert nombres(api.get(reverse("api-exercise-list"))) == [
            "Fondos", "Press de banca", "Sentadilla",
        ]

    def test_busca_por_nombre(self, api, catalogo):
        assert nombres(api.get(reverse("api-exercise-list"), {"q": "press"})) == [
            "Press de banca"
        ]

    def test_filtra_por_parte_y_material(self, api, catalogo):
        respuesta = api.get(
            reverse("api-exercise-list"), {"body_part": "chest", "equipment": "barbell"}
        )

        assert nombres(respuesta) == ["Press de banca"]

    def test_el_filtro_por_musculo_incluye_los_secundarios(self, api, catalogo):
        respuesta = api.get(reverse("api-exercise-list"), {"muscle": "triceps"})

        assert nombres(respuesta) == ["Fondos", "Press de banca"]

    def test_un_ejercicio_no_sale_dos_veces_por_ser_objetivo_y_secundario(
        self, api, catalogo, musculos
    ):
        catalogo["press"].secondary_muscles.add(musculos["pecho"])

        respuesta = api.get(reverse("api-exercise-list"), {"muscle": "pectorals"})

        assert nombres(respuesta) == ["Fondos", "Press de banca"]
        assert respuesta.json()["count"] == 2

    def test_la_ficha_se_pide_por_slug(self, api, catalogo):
        respuesta = api.get(reverse("api-exercise-detail", args=["press-banca"]))

        assert respuesta.status_code == 200
        assert respuesta.json()["name"] == "Press de banca"


class TestElBuscadorDeUnaRutina:
    def test_acota_a_lo_que_la_persona_tiene(self, api, ana, catalogo):
        ana.available_equipment = ["body weight"]
        ana.save(update_fields=["available_equipment"])

        assert nombres(api.get(reverse("api-exercise-list"), {"mi_material": "1"})) == ["Fondos"]

    def test_un_filtro_a_mano_gana_al_perfil(self, api, ana, catalogo):
        ana.available_equipment = ["body weight"]
        ana.save(update_fields=["available_equipment"])

        respuesta = api.get(
            reverse("api-exercise-list"), {"mi_material": "1", "equipment": "barbell"}
        )

        assert nombres(respuesta) == ["Press de banca", "Sentadilla"]

    def test_sin_material_declarado_no_acota_nada(self, api, catalogo):
        respuesta = api.get(reverse("api-exercise-list"), {"mi_material": "1"})

        assert len(nombres(respuesta)) == 3

    def test_sin_el_parametro_el_catalogo_no_se_acota(self, api, ana, catalogo):
        ana.available_equipment = ["body weight"]
        ana.save(update_fields=["available_equipment"])

        assert len(nombres(api.get(reverse("api-exercise-list")))) == 3


class TestLasFacetas:
    def test_cada_opcion_trae_su_recuento(self, api, catalogo):
        datos = api.get(reverse("api-exercise-facetas")).json()

        por_valor = {fila["valor"]: fila["n"] for fila in datos["body_part"]}
        assert por_valor["chest"] == 2
        assert por_valor["upper legs"] == 1
        assert datos["total"] == 3

    def test_el_recuento_tiene_en_cuenta_los_otros_filtros(self, api, catalogo):
        datos = api.get(reverse("api-exercise-facetas"), {"body_part": "chest"}).json()

        por_valor = {fila["valor"]: fila["n"] for fila in datos["equipment"]}
        assert por_valor["barbell"] == 1
        assert por_valor["body weight"] == 1

    def test_el_recuento_de_un_campo_ignora_su_propio_filtro(self, api, catalogo):
        datos = api.get(reverse("api-exercise-facetas"), {"body_part": "chest"}).json()

        assert {fila["valor"] for fila in datos["body_part"]} == {"chest", "upper legs"}

    def test_no_ofrece_opciones_sin_ejercicios(self, api, catalogo):
        datos = api.get(reverse("api-exercise-facetas")).json()

        assert {fila["valor"] for fila in datos["equipment"]} == {"barbell", "body weight"}

    def test_los_musculos_van_de_mas_ejercicios_a_menos(self, api, catalogo):
        datos = api.get(reverse("api-exercise-facetas")).json()

        recuentos = [fila["n"] for fila in datos["muscle"]]
        assert recuentos == sorted(recuentos, reverse=True)


class TestElAislamiento:
    @pytest.fixture
    def ajeno(self, beto, musculos):
        return Exercise.objects.create(
            name="Secreto de Beto", slug="secreto-de-beto", body_part="chest",
            equipment="barbell", target_muscle=musculos["pecho"],
            is_global=False, created_by=beto,
        )

    def test_no_sale_en_el_listado(self, api, catalogo, ajeno):
        assert "Secreto de Beto" not in nombres(api.get(reverse("api-exercise-list")))

    def test_su_ficha_no_existe(self, api, ajeno):
        assert api.get(reverse("api-exercise-detail", args=["secreto-de-beto"])).status_code == 404

    def test_no_cuenta_en_las_facetas(self, api, catalogo, ajeno):
        datos = api.get(reverse("api-exercise-facetas")).json()

        por_valor = {fila["valor"]: fila["n"] for fila in datos["body_part"]}
        assert por_valor["chest"] == 2
        assert datos["total"] == 3

    def test_el_propio_si_sale(self, api, ana, catalogo, musculos):
        Exercise.objects.create(
            name="Mi invento", slug="mi-invento", body_part="chest", equipment="barbell",
            target_muscle=musculos["pecho"], is_global=False, created_by=ana,
        )

        assert "Mi invento" in nombres(api.get(reverse("api-exercise-list")))

    def test_sin_sesion_no_se_ve_nada(self, catalogo):
        respuesta = APIClient().get(reverse("api-exercise-list"))

        assert respuesta.status_code in (401, 403)


class TestCrearUnEjercicioPropio:
    def test_lo_crea_y_devuelve_la_ficha_completa(self, api, ana):
        respuesta = api.post(
            reverse("api-exercise-list"),
            {"name": "Remo con banda", "body_part": "back", "equipment": "band"},
            format="json",
        )

        assert respuesta.status_code == 201
        assert respuesta.json()["slug"] == "remo-con-banda"
        assert respuesta.json()["equipment_label"]

    def test_queda_como_propio_y_no_en_el_catalogo(self, api, ana):
        api.post(
            reverse("api-exercise-list"),
            {"name": "Remo con banda", "body_part": "back", "equipment": "band",
             "is_global": True, "created_by": 999},
            format="json",
        )

        creado = Exercise.objects.get(name="Remo con banda")
        assert creado.is_global is False
        assert creado.created_by == ana

    def test_otra_persona_no_lo_ve(self, api, ana, beto):
        api.post(
            reverse("api-exercise-list"),
            {"name": "Remo con banda", "body_part": "back", "equipment": "band"},
            format="json",
        )

        otro = APIClient()
        otro.force_login(beto)
        assert nombres(otro.get(reverse("api-exercise-list"))) == []

    def test_el_nombre_no_puede_repetir_uno_visible(self, api, catalogo):
        respuesta = api.post(
            reverse("api-exercise-list"),
            {"name": "press de banca", "body_part": "chest", "equipment": "barbell"},
            format="json",
        )

        assert respuesta.status_code == 400
        assert "name" in respuesta.json()

    def test_pero_sí_uno_que_no_se_ve(self, api, beto, musculos):
        Exercise.objects.create(
            name="Secreto", slug="secreto", body_part="chest", equipment="barbell",
            target_muscle=musculos["pecho"], is_global=False, created_by=beto,
        )

        respuesta = api.post(
            reverse("api-exercise-list"),
            {"name": "Secreto", "body_part": "chest", "equipment": "barbell"},
            format="json",
        )

        assert respuesta.status_code == 201

    def test_el_slug_no_choca_con_uno_que_ya_existe(self, api, beto, musculos):
        Exercise.objects.create(
            name="Secreto", slug="secreto", body_part="chest", equipment="barbell",
            target_muscle=musculos["pecho"], is_global=False, created_by=beto,
        )

        respuesta = api.post(
            reverse("api-exercise-list"),
            {"name": "Secreto", "body_part": "chest", "equipment": "barbell"},
            format="json",
        )

        assert respuesta.json()["slug"] == "secreto-2"

    def test_un_nombre_en_blanco_se_rechaza(self, api):
        respuesta = api.post(
            reverse("api-exercise-list"),
            {"name": "   ", "body_part": "chest", "equipment": "barbell"},
            format="json",
        )

        assert respuesta.status_code == 400

    def test_no_se_puede_colar_material_visual(self, api, ana):
        api.post(
            reverse("api-exercise-list"),
            {"name": "Remo con banda", "body_part": "back", "equipment": "band",
             "image": "robada.png", "attribution": "© mío"},
            format="json",
        )

        creado = Exercise.objects.get(name="Remo con banda")
        assert not creado.image
        assert creado.attribution == ""
