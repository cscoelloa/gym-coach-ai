import json
from functools import lru_cache
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.html import format_html, format_html_join
from django.utils.safestring import SafeString, mark_safe

ENTRADA = "src/main.tsx"

PREAMBULO_REACT = """
import RefreshRuntime from "{servidor}/@react-refresh";
RefreshRuntime.injectIntoGlobalHook(window);
window.$RefreshReg$ = () => {{}};
window.$RefreshSig$ = () => (type) => type;
window.__vite_plugin_react_preamble_installed__ = true;
"""


def en_desarrollo() -> bool:
    return bool(getattr(settings, "VITE_DEV_SERVER_URL", ""))


@lru_cache(maxsize=1)
def _manifiesto() -> dict:
    ruta = Path(settings.VITE_MANIFEST)
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ImproperlyConfigured(
            f"No existe el manifiesto de Vite en {ruta}. El frontend no está construido: "
            "ejecuta `npm --prefix frontend ci && npm --prefix frontend run build`, o arranca "
            "el servidor de desarrollo y pon VITE_DEV_SERVER_URL en el entorno."
        ) from None


def _estatico(archivo: str) -> str:
    return f"{settings.STATIC_URL}{settings.VITE_STATIC_PREFIX}/{archivo}"


def _limpiar_cache_si_toca() -> None:
    if settings.DEBUG:
        _manifiesto.cache_clear()


def manifiesto_en_bruto() -> bytes:
    return Path(settings.VITE_MANIFEST).read_bytes()


def archivos_del_bundle() -> list[str]:
    _limpiar_cache_si_toca()
    vistos: dict[str, None] = {}
    for entrada in _manifiesto().values():
        for archivo in (entrada["file"], *entrada.get("css", []), *entrada.get("assets", [])):
            vistos.setdefault(_estatico(archivo))
    return sorted(vistos)


def etiquetas(nonce: str = "") -> SafeString:
    if en_desarrollo():
        return _etiquetas_de_desarrollo(nonce)
    return _etiquetas_construidas()


def _etiquetas_de_desarrollo(nonce: str) -> SafeString:
    servidor = settings.VITE_DEV_SERVER_URL.rstrip("/")

    return format_html(
        '<script type="module" nonce="{}">{}</script>'
        '<script type="module" src="{}/@vite/client"></script>'
        '<script type="module" src="{}/{}"></script>',
        nonce,
        mark_safe(PREAMBULO_REACT.format(servidor=servidor)),  # noqa: S308  # nosec B308 B703
        servidor,
        servidor,
        ENTRADA,
    )


def _etiquetas_construidas() -> SafeString:
    _limpiar_cache_si_toca()
    manifiesto = _manifiesto()

    try:
        entrada = manifiesto[ENTRADA]
    except KeyError:
        raise ImproperlyConfigured(
            f"El manifiesto de Vite no tiene la entrada «{ENTRADA}». "
            f"Claves disponibles: {sorted(manifiesto)}. Revisa `build.rollupOptions.input` en "
            "frontend/vite.config.ts."
        ) from None

    hojas = format_html_join(
        "",
        '<link rel="stylesheet" href="{}">',
        ((_estatico(css),) for css in entrada.get("css", [])),
    )

    precargas = format_html_join(
        "",
        '<link rel="modulepreload" href="{}">',
        (
            (_estatico(manifiesto[clave]["file"]),)
            for clave in entrada.get("imports", [])
            if clave in manifiesto
        ),
    )

    script = format_html('<script type="module" src="{}"></script>', _estatico(entrada["file"]))

    return hojas + precargas + script
