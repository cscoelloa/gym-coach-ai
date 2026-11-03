import re
from pathlib import Path

from django.conf import settings

BASE_DIR = Path(settings.BASE_DIR)
REGISTRO = BASE_DIR / ".docs" / "01-decisions.md"

CITA = re.compile(r"ADR-(\d{3})")
ENCABEZADO = re.compile(r"^## ADR-(\d{3})\b", re.MULTILINE)

RAICES = [
    "apps",
    "config",
    ".docs",
    "frontend/src",
    "frontend/e2e",
    "templates",
    "assets",
    "static",
    ".github",
]
SUELTOS = [
    "CLAUDE.md",
    "README.md",
    "NOTICE.md",
    "requirements.txt",
    ".env.example",
    ".gitignore",
]
IGNORADOS = {"node_modules", "dist", "__pycache__", ".pytest_cache", ".ruff_cache", "migrations"}
EXTENSIONES = {
    ".py",
    ".md",
    ".ts",
    ".tsx",
    ".js",
    ".css",
    ".html",
    ".yml",
    ".yaml",
    ".txt",
    ".sh",
    ".toml",
    "",
}


def archivos():
    for raiz in RAICES:
        for ruta in sorted((BASE_DIR / raiz).rglob("*")):
            if not ruta.is_file() or ruta.suffix not in EXTENSIONES:
                continue
            if IGNORADOS & set(ruta.relative_to(BASE_DIR).parts):
                continue
            yield ruta
    for nombre in SUELTOS:
        ruta = BASE_DIR / nombre
        if ruta.is_file():
            yield ruta


def citas():
    encontradas: dict[str, list[str]] = {}
    for ruta in archivos():
        texto = ruta.read_text(encoding="utf-8", errors="ignore")
        if ruta == REGISTRO:
            texto = ENCABEZADO.sub("", texto)
        for numero in set(CITA.findall(texto)):
            encontradas.setdefault(numero, []).append(str(ruta.relative_to(BASE_DIR)))
    return encontradas


def entradas():
    return ENCABEZADO.findall(REGISTRO.read_text(encoding="utf-8"))


class TestElRegistroDeDecisiones:
    def test_todo_adr_citado_tiene_su_entrada(self):
        escritas = set(entradas())

        huerfanos = {
            numero: rutas for numero, rutas in sorted(citas().items()) if numero not in escritas
        }

        assert not huerfanos, "se cita un ADR que no está en .docs/01-decisions.md:\n" + "\n".join(
            f"  ADR-{numero} ← {', '.join(sorted(rutas))}" for numero, rutas in huerfanos.items()
        )

    def test_la_numeracion_no_tiene_huecos(self):
        numeros = sorted(int(n) for n in entradas())

        faltan = sorted(set(range(numeros[0], numeros[-1] + 1)) - set(numeros))

        assert not faltan, "huecos en la numeración: " + ", ".join(f"ADR-{n:03d}" for n in faltan)

    def test_ningun_numero_se_usa_dos_veces(self):
        escritas = entradas()

        repetidos = sorted({n for n in escritas if escritas.count(n) > 1})

        assert not repetidos, "número de ADR usado más de una vez: " + ", ".join(
            f"ADR-{n}" for n in repetidos
        )
