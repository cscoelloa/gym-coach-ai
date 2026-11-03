import json
import re
from pathlib import Path

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse

from apps.common import vite

ENTRADA_MINIMA = {
    "src/main.tsx": {
        "file": "assets/main-abc123.js",
        "name": "main",
        "src": "src/main.tsx",
        "isEntry": True,
        "css": ["assets/main-def456.css"],
    }
}


@pytest.fixture(autouse=True)
def sin_cache():
    vite._manifiesto.cache_clear()
    yield
    vite._manifiesto.cache_clear()


@pytest.fixture
def manifiesto(tmp_path, settings):
    def escribir(contenido: dict):
        ruta = tmp_path / "manifest.json"
        ruta.write_text(json.dumps(contenido), encoding="utf-8")
        settings.VITE_MANIFEST = ruta
        return ruta

    return escribir


class TestElBundleConstruido:
    def test_pone_la_hoja_antes_del_script(self, manifiesto, settings):
        settings.VITE_DEV_SERVER_URL = ""
        manifiesto(ENTRADA_MINIMA)

        html = vite.etiquetas()

        assert html.index("main-def456.css") < html.index("main-abc123.js")

    def test_las_rutas_son_las_de_vite_también_con_el_almacén_de_producción(
        self, manifiesto, settings
    ):
        settings.VITE_DEV_SERVER_URL = ""
        settings.STORAGES = {
            **settings.STORAGES,
            "staticfiles": {
                "BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"
            },
        }
        manifiesto({
            "src/main.tsx": {**ENTRADA_MINIMA["src/main.tsx"], "imports": ["_vendor.js"]},
            "_vendor.js": {"file": "assets/vendor-999.js"},
        })

        html = vite.etiquetas()

        assert '<script type="module" src="/static/spa/assets/main-abc123.js">' in html
        assert '<link rel="stylesheet" href="/static/spa/assets/main-def456.css">' in html
        assert '<link rel="modulepreload" href="/static/spa/assets/vendor-999.js">' in html

    def test_precarga_los_trozos_que_el_bundle_va_a_pedir_seguro(self, manifiesto, settings):
        settings.VITE_DEV_SERVER_URL = ""
        manifiesto({
            "src/main.tsx": {**ENTRADA_MINIMA["src/main.tsx"], "imports": ["_vendor.js"]},
            "_vendor.js": {"file": "assets/vendor-999.js"},
        })

        html = vite.etiquetas()

        assert '<link rel="modulepreload" href="/static/spa/assets/vendor-999.js">' in html

    def test_sin_manifiesto_falla_diciendo_qué_ejecutar(self, settings, tmp_path):
        settings.VITE_DEV_SERVER_URL = ""
        settings.VITE_MANIFEST = tmp_path / "no-existe.json"

        with pytest.raises(ImproperlyConfigured, match="npm --prefix frontend run build"):
            vite.etiquetas()

    def test_un_manifiesto_sin_la_entrada_dice_cuáles_hay(self, manifiesto, settings):
        settings.VITE_DEV_SERVER_URL = ""
        manifiesto({"src/otro.tsx": {"file": "assets/otro.js"}})

        with pytest.raises(ImproperlyConfigured, match="src/otro.tsx"):
            vite.etiquetas()


class TestElServidorDeDesarrollo:
    def test_apunta_al_servidor_de_vite(self, settings):
        settings.VITE_DEV_SERVER_URL = "http://localhost:5173"

        html = vite.etiquetas(nonce="abc")

        assert 'src="http://localhost:5173/@vite/client"' in html
        assert 'src="http://localhost:5173/src/main.tsx"' in html

    def test_el_preambulo_de_react_refresh_lleva_el_nonce(self, settings):
        settings.VITE_DEV_SERVER_URL = "http://localhost:5173"

        html = vite.etiquetas(nonce="nonce-de-prueba")

        assert '<script type="module" nonce="nonce-de-prueba">' in html
        assert "__vite_plugin_react_preamble_installed__" in html

    def test_una_barra_de_más_no_duplica_la_del_camino(self, settings):
        settings.VITE_DEV_SERVER_URL = "http://localhost:5173/"

        html = vite.etiquetas(nonce="abc")

        assert "5173//" not in html


@pytest.mark.django_db
class TestElNonceSoloExisteEnDesarrollo:
    CABECERA = "Content-Security-Policy"

    @pytest.fixture
    def ana(self, client, django_user_model):
        usuario = django_user_model.objects.create_user("ana", password="Contrasena-Larga-1")
        client.force_login(usuario)
        return usuario

    def test_en_produccion_la_cabecera_no_lleva_nonce(self, client, ana, manifiesto, settings):
        settings.VITE_DEV_SERVER_URL = ""
        manifiesto(ENTRADA_MINIMA)

        respuesta = client.get(reverse("styleguide"))

        assert "'nonce-" not in respuesta[self.CABECERA], (
            "hay un nonce en script-src sin un solo script inline que lo use: "
            "la CSP está más floja de lo que debería y no se nota en nada"
        )

    def test_en_desarrollo_sí(self, client, ana, settings):
        settings.VITE_DEV_SERVER_URL = "http://localhost:5173"

        respuesta = client.get(reverse("styleguide"))

        assert "'nonce-" in respuesta[self.CABECERA]
        nonce = re.search(r"'nonce-([^']+)'", respuesta[self.CABECERA]).group(1)
        assert f'nonce="{nonce}"' in respuesta.content.decode()


class TestLosTrozosPerezososResuelven:
    REFERENCIA = re.compile(r'["\'][^"\']*?/([A-Za-z0-9_-]+-[A-Za-z0-9_-]{8}\.js)["\']')

    def test_todo_trozo_referenciado_existe(self, settings):
        dist = Path(settings.BASE_DIR, "frontend", "dist", "assets")
        if not dist.is_dir():
            pytest.skip("el frontend no está construido")

        emitidos = {ruta.name for ruta in dist.glob("*.js")}
        assert emitidos, "no hay ningún .js en frontend/dist/assets"

        faltan = set()
        for archivo in dist.glob("*.js"):
            for nombre in self.REFERENCIA.findall(archivo.read_text(encoding="utf-8")):
                if nombre not in emitidos:
                    faltan.add(f"{archivo.name} → {nombre}")

        assert not faltan, "trozos referenciados que no se han emitido:\n" + "\n".join(
            sorted(faltan)
        )


class TestLaCacheDelManifiesto:
    def test_en_desarrollo_se_relee(self, manifiesto, settings):
        settings.DEBUG = True
        settings.VITE_DEV_SERVER_URL = ""
        manifiesto(ENTRADA_MINIMA)
        vite.etiquetas()

        manifiesto({"src/main.tsx": {"file": "assets/main-NUEVO.js", "isEntry": True}})

        assert "main-NUEVO.js" in vite.etiquetas()

    def test_en_produccion_se_lee_una_vez(self, manifiesto, settings):
        settings.DEBUG = False
        settings.VITE_DEV_SERVER_URL = ""
        ruta = manifiesto(ENTRADA_MINIMA)
        vite.etiquetas()

        ruta.unlink()

        assert "main-abc123.js" in vite.etiquetas()


class TestLaCacheLargaDelBundle:
    @pytest.fixture
    def inmutable(self, settings):
        regex = re.compile(settings.WHITENOISE_IMMUTABLE_FILE_TEST)
        return lambda url: bool(regex.search(url))

    @pytest.mark.parametrize(
        "url",
        [
            "/static/spa/assets/main-BNTxZHpa.js",
            "/static/spa/assets/Lienzo-Dn2uRqwY.js",
            "/static/spa/assets/main-BfG_efqX.css",
            "/static/spa/assets/Inter-Variable-latin-C4zznr8T.woff2",
            "/static/js/theme.1f2e3d4c5b6a.js",
        ],
    )
    def test_lo_que_lleva_hash_es_inmutable(self, inmutable, url):
        assert inmutable(url)

    @pytest.mark.parametrize(
        "url",
        [
            "/static/js/theme.js",
            "/static/pwa/icon-192.png",
            "/static/spa/.vite/manifest.json",
            "/static/fonts/LEEME.md",
        ],
    )
    def test_lo_que_no_lo_lleva_no(self, inmutable, url):
        assert not inmutable(url)

    def test_no_se_borran_los_originales(self, settings):
        assert not getattr(settings, "WHITENOISE_KEEP_ONLY_HASHED_FILES", False)
