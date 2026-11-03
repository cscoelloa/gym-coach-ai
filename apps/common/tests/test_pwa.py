import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest
from django.conf import settings
from django.contrib.staticfiles import finders
from django.urls import resolve, reverse

from apps.common import pwa, vite
from apps.common.tests.test_design_system import CLARO, OSCURO, bloque

RAIZ = Path(settings.BASE_DIR)


@pytest.fixture(autouse=True)
def sin_cache():
    vite._manifiesto.cache_clear()
    pwa._version_memorizada.cache_clear()
    yield
    vite._manifiesto.cache_clear()
    pwa._version_memorizada.cache_clear()


@pytest.fixture
def bundle(tmp_path, settings):
    settings.VITE_DEV_SERVER_URL = ""

    def escribir(principal: str = "assets/main-abc12345.js"):
        ruta = tmp_path / "manifest.json"
        ruta.write_text(
            json.dumps({
                "src/main.tsx": {
                    "file": principal,
                    "isEntry": True,
                    "css": ["assets/main-def45678.css"],
                    "assets": ["assets/Inter-Variable-latin-aaaa1111.woff2"],
                },
                "src/ds/grafica/Lienzo.tsx": {
                    "file": "assets/Lienzo-bbbb2222.js",
                    "isDynamicEntry": True,
                },
            }),
            encoding="utf-8",
        )
        settings.VITE_MANIFEST = ruta

    escribir()
    return escribir


def tramo(texto: str, desde: str, hasta: str) -> str:
    return texto[texto.index(desde) : texto.index(hasta)]


def configuracion(respuesta) -> dict:
    texto = respuesta.content.decode()
    encontrada = re.search(r"const CONFIG = (\{.*?\});\n", texto)
    assert encontrada, "el service worker no lleva configuración"
    return json.loads(encontrada.group(1))


class TestElManifiesto:
    def test_sale_con_el_tipo_que_chrome_exige(self, client):
        respuesta = client.get(reverse("manifest"))

        assert respuesta.status_code == 200
        assert respuesta["Content-Type"] == "application/manifest+json"

    def test_lo_que_lo_hace_instalable(self, client):
        datos = client.get(reverse("manifest")).json()

        assert datos["display"] == "standalone"
        assert datos["id"] == datos["start_url"] == datos["scope"] == "/"
        tamanos = {(icono["sizes"], icono["purpose"]) for icono in datos["icons"]}
        assert {("192x192", "any"), ("512x512", "any"), ("512x512", "maskable")} <= tamanos

    def test_cada_icono_existe(self, client):
        datos = client.get(reverse("manifest")).json()
        iconos = [
            *datos["icons"],
            *(icono for atajo in datos["shortcuts"] for icono in atajo["icons"]),
        ]

        prefijo = settings.STATIC_URL
        faltan = [i["src"] for i in iconos if not finders.find(i["src"].removeprefix(prefijo))]
        assert not faltan, f"iconos del manifiesto que no existen: {faltan}"

    def test_cada_atajo_abre_una_pantalla_de_la_aplicacion(self, client):
        for atajo in client.get(reverse("manifest")).json()["shortcuts"]:
            assert resolve(atajo["url"]).url_name, atajo["url"]

    def test_los_colores_son_el_fondo_del_tema_claro(self, client):
        datos = client.get(reverse("manifest")).json()
        fondo = re.search(r"--surface-000:\s*(#[0-9a-f]{6})", bloque(CLARO)).group(1)

        assert datos["theme_color"] == datos["background_color"] == fondo


class TestElServiceWorker:
    def test_no_se_cachea_nunca(self, client, bundle):
        respuesta = client.get(reverse("service_worker"))

        assert respuesta["Content-Type"].startswith("application/javascript")
        assert "no-cache" in respuesta["Cache-Control"]
        assert "max-age=0" in respuesta["Cache-Control"]

    def test_precarga_el_build_y_solo_estaticos(self, client, bundle):
        config = configuracion(client.get(reverse("service_worker")))

        assert config["activo"] is True
        assert "/static/spa/assets/main-abc12345.js" in config["precarga"]
        assert "/static/spa/assets/Lienzo-bbbb2222.js" in config["precarga"]
        assert "/static/spa/assets/Inter-Variable-latin-aaaa1111.woff2" in config["precarga"]
        assert any(url.endswith(".js") and "theme" in url for url in config["precarga"])
        assert all(url.startswith(settings.STATIC_URL) for url in config["precarga"])
        assert config["cascara"] == reverse("login")

    def test_nunca_toca_la_api(self, client, bundle):
        texto = client.get(reverse("service_worker")).content.decode()
        nunca = re.search(r"const NUNCA = \[(.*?)\];", texto).group(1)

        for prefijo in ("/api/", "/admin/", "/media/", "/sw.js", "/manifest.webmanifest"):
            assert f'"{prefijo}"' in nunca, f"el service worker no excluye {prefijo}"
        assert 'peticion.method !== "GET"' in texto

    def test_la_version_nueva_espera_a_que_la_pidan(self, client, bundle):
        texto = re.sub(r"//.*", "", client.get(reverse("service_worker")).content.decode())
        instalar = tramo(texto, 'addEventListener("install"', 'addEventListener("activate"')

        rama_inactiva = instalar[instalar.index("if (!CONFIG.activo)") : instalar.index("return;")]
        assert "skipWaiting" in rama_inactiva
        assert instalar.count("skipWaiting()") == 1
        mensaje = tramo(texto, 'addEventListener("message"', 'addEventListener("fetch"')
        assert "SALTAR_ESPERA" in mensaje and "skipWaiting()" in mensaje

    def test_la_version_cambia_con_el_build(self, client, bundle, settings):
        settings.DEBUG = True
        antes = configuracion(client.get(reverse("service_worker")))["version"]

        bundle(principal="assets/main-zzz99999.js")
        despues = configuracion(client.get(reverse("service_worker")))["version"]

        assert re.fullmatch(r"[0-9a-f]{12}", antes)
        assert antes != despues

    def test_la_cascara_lleva_la_misma_version(self, client, bundle):
        config = configuracion(client.get(reverse("service_worker")))
        cascara = client.get(config["cascara"]).content.decode()

        assert f'<meta name="app-version" content="{config["version"]}">' in cascara

    def test_el_interruptor_de_emergencia_apaga_la_cache(self, client, bundle, settings):
        settings.PWA_OFFLINE = False

        config = configuracion(client.get(reverse("service_worker")))

        assert config["activo"] is False
        assert config["precarga"] == []
        assert config["icono"].endswith(".png")

    def test_con_el_servidor_de_vite_tampoco_cachea(self, client, settings):
        settings.VITE_DEV_SERVER_URL = "http://localhost:5173"

        assert configuracion(client.get(reverse("service_worker")))["activo"] is False

    def test_recibe_avisos_push_sin_hablar_con_la_api(self, client, bundle):
        texto = re.sub(r"//.*", "", client.get(reverse("service_worker")).content.decode())

        assert 'addEventListener("push"' in texto
        assert "showNotification(" in texto
        assert 'addEventListener("notificationclick"' in texto
        avisos = texto[texto.index('addEventListener("push"') :]
        assert "fetch(" not in avisos
        assert "self.location.origin" in avisos

    def test_contesta_si_sabe_recibir_avisos(self, client, bundle):
        texto = client.get(reverse("service_worker")).content.decode()
        mensaje = tramo(texto, 'addEventListener("message"', 'addEventListener("fetch"')

        assert "CAPACIDADES" in mensaje

    @pytest.mark.skipif(not shutil.which("node"), reason="no hay Node para comprobar la sintaxis")
    def test_el_javascript_generado_es_valido(self, client, bundle, tmp_path):
        archivo = tmp_path / "sw.js"
        archivo.write_bytes(client.get(reverse("service_worker")).content)

        resultado = subprocess.run(  # noqa: S603
            [shutil.which("node"), "--check", str(archivo)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert resultado.returncode == 0, resultado.stderr


class TestLosColoresDeLaMarcaSonTokens:
    HEX = re.compile(r"#[0-9a-fA-F]{6}\b")

    @staticmethod
    def tokens() -> set[str]:
        valores = re.findall(r"#[0-9a-fA-F]{6}\b", bloque(CLARO) + bloque(OSCURO))
        return {valor.lower() for valor in valores}

    @pytest.mark.parametrize(
        "ruta",
        [
            "static/js/theme.js",
            "templates/spa.html",
            "frontend/src/ds/grafica/tema.ts",
            "apps/common/pwa.py",
            "apps/common/sw.js",
        ],
    )
    def test_cada_hex_es_un_token(self, ruta):
        texto = (RAIZ / ruta).read_text(encoding="utf-8")
        encontrados = {valor.lower() for valor in self.HEX.findall(texto)}

        assert encontrados, f"{ruta} ya no escribe ningún color: quítalo de esta lista"
        ajenos = encontrados - self.tokens()
        assert not ajenos, f"{ruta}: colores que no son tokens de app.css: {sorted(ajenos)}"
