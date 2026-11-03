import pytest

from apps.workouts import bodymap
from apps.workouts.bodymap.paths import REGIONS
from apps.workouts.models import Exercise, MuscleGroup
from apps.workouts.taxonomy import (
    MUSCLE_ES,
    MUSCLE_WITHOUT_REGION,
    REGION_INERT,
    REGION_MUSCLE,
    muscle_label,
    muscle_slug,
)


class TestLaAnatomiaLlegoEntera:
    def test_estan_las_ochenta_y_nueve_regiones(self):
        assert len(REGIONS) == 89, f"llegaron {len(REGIONS)}"
        assert len([r for r in REGIONS if r[2] == "front"]) == 40
        assert len([r for r in REGIONS if r[2] == "back"]) == 49

    def test_ningun_trazado_viene_vacio(self):
        cortos = [(r[0], len(r[3])) for r in REGIONS if len(r[3]) < 20]
        assert not cortos, f"trazados truncados: {cortos}"

    def test_ninguna_region_esta_repetida(self):
        ids = [r[0] for r in REGIONS]
        repetidos = {i for i in ids if ids.count(i) > 1}
        assert not repetidos, f"ids repetidos: {sorted(repetidos)}"

    def test_las_dos_vistas_se_dibujan_en_su_propio_plano(self):
        assert bodymap.VIEWBOX_FRONT == "0 0 35 93"
        assert bodymap.VIEWBOX_BACK == "37 0 35 93"


class TestElMapeoCierraPorLosDosLados:
    def test_toda_region_tiene_destino_o_es_silueta(self):
        huerfanas = {r[0] for r in REGIONS} - set(REGION_MUSCLE) - REGION_INERT
        assert not huerfanas, (
            "regiones que se pintan pero no filtran nada:\n" + "\n".join(sorted(huerfanas))
        )

    def test_ningun_destino_apunta_a_una_region_que_no_existe(self):
        fantasmas = (set(REGION_MUSCLE) | REGION_INERT) - {r[0] for r in REGIONS}
        assert not fantasmas, "destinos sin región:\n" + "\n".join(sorted(fantasmas))

    def test_todo_musculo_se_pinta_o_se_declara_sin_region(self):
        pintados = set(REGION_MUSCLE.values())
        todos = {muscle_slug(nombre) for nombre in MUSCLE_ES}
        olvidados = todos - pintados - MUSCLE_WITHOUT_REGION
        assert not olvidados, (
            "músculos que no están en el mapa ni declarados fuera de él:\n"
            + "\n".join(sorted(olvidados))
        )

    def test_ningun_destino_es_un_musculo_inventado(self):
        conocidos = {muscle_slug(nombre) for nombre in MUSCLE_ES}
        inventados = (set(REGION_MUSCLE.values()) | MUSCLE_WITHOUT_REGION) - conocidos
        assert not inventados, "destinos que no son músculos:\n" + "\n".join(sorted(inventados))

    def test_una_region_no_puede_ser_musculo_y_silueta_a_la_vez(self):
        ambas = set(REGION_MUSCLE) & REGION_INERT
        assert not ambas, sorted(ambas)


class TestLosDestinosSonSlugs:
    def test_ningun_destino_lleva_espacios(self):
        con_espacio = [
            m for m in set(REGION_MUSCLE.values()) | MUSCLE_WITHOUT_REGION if " " in m
        ]
        assert not con_espacio, (
            "destinos con espacio en vez de guion (nunca coincidirán con un slug):\n"
            + "\n".join(sorted(con_espacio))
        )

    @pytest.mark.parametrize(
        "slug,esperado",
        [
            ("upper-back", "Espalda alta"),
            ("lower-back", "Espalda baja"),
            ("hip-flexors", "Flexores de cadera"),
            ("serratus-anterior", "Serrato anterior"),
            ("lats", "Dorsales"),
        ],
    )
    def test_la_etiqueta_sale_en_espanol_desde_el_slug(self, slug, esperado):
        assert muscle_label(slug) == esperado

    def test_la_etiqueta_tambien_acepta_el_nombre_canonico(self):
        assert muscle_label("upper back") == "Espalda alta"


class TestLoQueSePintaEstaResuelto:
    def test_las_regiones_inertes_van_debajo(self):
        for vista in (bodymap.FRONT, bodymap.BACK):
            inertes = [i for i, r in enumerate(vista) if r.is_inert]
            musculos = [i for i, r in enumerate(vista) if not r.is_inert]
            assert max(inertes) < min(musculos)

    def test_sin_niveles_todo_queda_apagado(self):
        for vista in bodymap.painted():
            for region in vista.regions:
                assert region.css in {"bm-0", "bm-inert"}
                assert region.level == 0

    def test_el_nivel_llega_a_todas_las_porciones_de_un_musculo(self):
        vistas = bodymap.painted(levels={"lats": 3})
        dorsales = [r for v in vistas for r in v.regions if r.muscle == "lats"]

        assert len(dorsales) == 6
        assert {r.css for r in dorsales} == {"bm-3"}

    def test_la_silueta_nunca_se_enciende_ni_se_enlaza(self):
        vistas = bodymap.painted(levels={"lats": 4}, urls={"lats": "?muscle=lats"})
        inertes = [r for v in vistas for r in v.regions if r.is_inert]

        assert inertes
        assert all(r.css == "bm-inert" and r.url == "" for r in inertes)

    def test_el_musculo_activo_se_distingue_del_que_esta_a_tope(self):
        vistas = bodymap.painted(levels={"lats": 4, "quads": 4}, active="lats")
        por_musculo = {r.muscle: r.css for v in vistas for r in v.regions if r.muscle}

        assert por_musculo["lats"] == "bm-on"
        assert por_musculo["quads"] == "bm-4"

    def test_sin_urls_el_mapa_es_de_solo_lectura(self):
        vistas = bodymap.painted(levels={"lats": 2})
        assert all(r.url == "" for v in vistas for r in v.regions)


@pytest.mark.django_db
class TestElMapaCuadraConLaBaseDeDatos:
    def test_los_musculos_del_catalogo_tienen_sitio_en_el_mapa(self, django_user_model):
        creados = [MuscleGroup.from_canonical(nombre) for nombre in MUSCLE_ES]
        pintables = set(bodymap.PAINTED_MUSCLES)

        sin_sitio = [
            m.slug
            for m in creados
            if m.slug not in pintables and m.slug not in MUSCLE_WITHOUT_REGION
        ]
        assert not sin_sitio, (
            "músculos importables que el mapa no sabe colocar:\n" + "\n".join(sin_sitio)
        )

    def test_el_importador_y_el_mapa_construyen_el_mismo_slug(self):
        for nombre in MUSCLE_ES:
            assert MuscleGroup.from_canonical(nombre).slug == muscle_slug(nombre)


@pytest.mark.django_db
class TestElFiltroPorMusculo:
    @pytest.fixture
    def catalogo(self):
        dorsales = MuscleGroup.from_canonical("lats")
        biceps = MuscleGroup.from_canonical("biceps")

        dominada = Exercise.objects.create(
            external_id="0001", name="Dominada", slug="dominada",
            body_part="back", equipment="body weight", target_muscle=dorsales,
        )
        dominada.secondary_muscles.add(biceps)

        curl = Exercise.objects.create(
            external_id="0002", name="Curl con barra", slug="curl",
            body_part="upper arms", equipment="barbell", target_muscle=biceps,
        )

        triceps = MuscleGroup.from_canonical("triceps")
        encogimiento = Exercise.objects.create(
            external_id="0003", name="Encogimiento", slug="encogimiento",
            body_part="back", equipment="barbell", target_muscle=dorsales,
        )
        encogimiento.secondary_muscles.add(dorsales, triceps)

        return {"dominada": dominada, "curl": curl, "encogimiento": encogimiento}

    def filtrar(self, slug, **extra):
        from django.contrib.auth.models import AnonymousUser

        from apps.workouts import catalog

        filtros = {"q": "", "body_part": "", "equipment": "", "muscle": slug, **extra}
        return list(
            catalog.filtrar(AnonymousUser(), filtros).values_list("name", flat=True)
        )

    def test_trae_los_que_lo_tienen_como_objetivo(self, catalogo):
        assert "Dominada" in self.filtrar("lats")

    def test_trae_tambien_los_que_lo_trabajan_de_secundario(self, catalogo):
        nombres = self.filtrar("biceps")

        assert "Curl con barra" in nombres
        assert "Dominada" in nombres

    def test_no_duplica_cuando_es_objetivo_y_secundario(self, catalogo):
        assert self.filtrar("lats").count("Encogimiento") == 1

    def test_un_musculo_inexistente_devuelve_vacio_sin_reventar(self, catalogo):
        assert self.filtrar("no-existe") == []

    def test_convive_con_los_otros_filtros(self, catalogo):
        assert self.filtrar("lats", equipment="barbell") == ["Encogimiento"]
