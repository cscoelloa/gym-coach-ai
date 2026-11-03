import re
from pathlib import Path

from django.conf import settings

from config.urls import SPA_URLS, SPA_URLS_PUBLICAS

RUTAS_TS = Path(settings.BASE_DIR, "frontend", "src", "rutas.ts")


def rutas_declaradas_en_react() -> set[str]:
    texto = RUTAS_TS.read_text(encoding="utf-8")
    cuerpo = texto[texto.index("RUTAS_DE_LA_SPA = [") : texto.index("] as const;")]
    return set(re.findall(r'"([^"]+)"', cuerpo))


PARAMETRO = re.compile(r"<(?:[a-z_]+:)?([a-z_]+)>")


def rutas_declaradas_en_django() -> set[str]:
    return {
        PARAMETRO.sub(r":\1", f"/{ruta.pattern._route}")
        for ruta in (*SPA_URLS, *SPA_URLS_PUBLICAS)
    }


def test_hay_rutas_que_comparar():
    assert rutas_declaradas_en_django()
    assert rutas_declaradas_en_react()


def test_las_dos_listas_dicen_lo_mismo():
    en_django = rutas_declaradas_en_django()
    en_react = rutas_declaradas_en_react()

    assert en_django == en_react, (
        "las dos listas de rutas de la SPA se han separado.\n"
        f"  solo en config/urls.py:        {sorted(en_django - en_react) or '—'}\n"
        f"  solo en frontend/src/rutas.ts: {sorted(en_react - en_django) or '—'}"
    )


def test_todas_llevan_barra_final():
    sin_barra = [ruta for ruta in rutas_declaradas_en_react() if not ruta.endswith("/")]

    assert not sin_barra, sin_barra
