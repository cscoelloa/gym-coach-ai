import re
from pathlib import Path

from django.conf import settings

TEMPLATES = Path(settings.BASE_DIR, "templates")
CSS = Path(settings.BASE_DIR, "assets", "app.css")

CLASES = re.compile(r'class="([^"]*)"')
PISTAS = re.compile(r"grid-cols-\[([^\]]*)\]")


def plantillas():
    return sorted(TEMPLATES.rglob("*.html"))


class TestLasRejillasPuedenEncogerse:
    def test_ninguna_rejilla_se_queda_sin_columnas_para_movil(self):
        culpables = []
        for ruta in plantillas():
            for clases in CLASES.findall(ruta.read_text(encoding="utf-8")):
                fichas = clases.split()
                if "grid" not in fichas:
                    continue
                if not any(f.startswith("grid-cols-") for f in fichas):
                    culpables.append(f"{ruta.name}: {clases}")

        assert not culpables, "rejillas sin columnas en móvil:\n" + "\n".join(culpables)

    def test_ninguna_pista_fr_se_escribe_desnuda(self):
        culpables = []
        for ruta in [*plantillas(), CSS]:
            for pista in PISTAS.findall(ruta.read_text(encoding="utf-8")):
                for casilla in re.finditer(r"[\d.]*fr\b", pista):
                    if not pista[: casilla.start()].endswith("minmax(0,"):
                        culpables.append(f"{ruta.name}: grid-cols-[{pista}]")

        assert not culpables, "pistas `fr` sin minmax(0,…):\n" + "\n".join(culpables)


class TestLosContenedoresQueSeDesbordaban:
    def test_la_tarjeta_puede_encogerse(self):
        css = CSS.read_text(encoding="utf-8")
        bloque = css[css.index("@utility card {") :]

        assert "min-w-0" in bloque[: bloque.index("}")]

    def test_el_hueco_del_grafico_tambien(self):
        css = CSS.read_text(encoding="utf-8")
        bloque = css[css.index("@utility chart-box {") :]
        cuerpo = bloque[: bloque.index("}")]

        assert "min-w-0" in cuerpo
        assert "w-full" in cuerpo

    def test_la_tabla_ancha_sigue_desplazandose(self):
        css = CSS.read_text(encoding="utf-8")
        bloque = css[css.index("@utility table-scroll {") :]

        assert "overflow-x-auto" in bloque[: bloque.index("}")]
