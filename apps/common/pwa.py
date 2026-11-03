import hashlib
import json
from functools import lru_cache
from pathlib import Path

from django.conf import settings
from django.contrib.staticfiles import finders
from django.http import HttpResponse, JsonResponse
from django.templatetags.static import static
from django.urls import reverse
from django.views.decorators.cache import cache_control

from . import vite

PLANTILLA_DEL_SW = Path(__file__).with_name("sw.js")

MARCA = (
    '/*__CONFIG__*/ { version: "sin-version", precarga: [], cascara: "/entrar/", activo: false, '
    'icono: "" }'
)

ESTATICOS_DE_LA_CASCARA = (
    "js/theme.js",
    "pwa/favicon.png",
    "pwa/apple-touch-icon.png",
    "pwa/icon-192.png",
)


def offline_activo() -> bool:
    return settings.PWA_OFFLINE and not vite.en_desarrollo()


def _version_calculada() -> str:
    huella = hashlib.sha256()
    huella.update(vite.manifiesto_en_bruto())
    huella.update(PLANTILLA_DEL_SW.read_bytes())
    for nombre in ESTATICOS_DE_LA_CASCARA:
        ruta = finders.find(nombre)
        if ruta:
            huella.update(Path(ruta).read_bytes())
    return huella.hexdigest()[:12]


_version_memorizada = lru_cache(maxsize=1)(_version_calculada)


def version() -> str:
    if settings.DEBUG:
        return _version_calculada()
    return _version_memorizada()


def precarga() -> list[str]:
    return [*vite.archivos_del_bundle(), *(static(nombre) for nombre in ESTATICOS_DE_LA_CASCARA)]


@cache_control(max_age=0, no_cache=True)
def service_worker(request):
    plantilla = PLANTILLA_DEL_SW.read_text(encoding="utf-8")
    icono = static("pwa/icon-192.png")
    if offline_activo():
        config = {
            "version": version(),
            "precarga": precarga(),
            "cascara": reverse("login"),
            "activo": True,
            "icono": icono,
        }
    else:
        config = {
            "version": "sin-cache",
            "precarga": [],
            "cascara": "",
            "activo": False,
            "icono": icono,
        }

    cuerpo = plantilla.replace(MARCA, json.dumps(config), 1)
    return HttpResponse(cuerpo, content_type="application/javascript; charset=utf-8")


@cache_control(max_age=60 * 60 * 24)
def manifiesto(request):
    def icono(nombre: str, tamano: str, proposito: str = "any") -> dict:
        return {
            "src": static(f"pwa/{nombre}"),
            "sizes": tamano,
            "type": "image/png",
            "purpose": proposito,
        }

    return JsonResponse(
        {
            "id": "/",
            "name": "PROJECT_GYM",
            "short_name": "Gym",
            "description": "Tus rutinas, tus entrenamientos y tu progreso.",
            "lang": "es",
            "dir": "ltr",
            "start_url": "/",
            "scope": "/",
            "display": "standalone",
            "orientation": "portrait-primary",
            "theme_color": "#f2f2f7",
            "background_color": "#f2f2f7",
            "categories": ["health", "fitness", "sports"],
            "launch_handler": {"client_mode": "navigate-existing"},
            "icons": [
                icono("icon-192.png", "192x192"),
                icono("icon-512.png", "512x512"),
                icono("icon-maskable-512.png", "512x512", "maskable"),
            ],
            "shortcuts": [
                {
                    "name": "Entrenar",
                    "short_name": "Entrenar",
                    "url": "/entrenamientos/",
                    "icons": [icono("atajo-entrenar.png", "96x96")],
                },
                {
                    "name": "Mi plan",
                    "short_name": "Plan",
                    "url": "/plan/",
                    "icons": [icono("atajo-plan.png", "96x96")],
                },
                {
                    "name": "Registrar peso",
                    "short_name": "Peso",
                    "url": "/peso/",
                    "icons": [icono("atajo-peso.png", "96x96")],
                },
            ],
        },
        content_type="application/manifest+json",
    )
