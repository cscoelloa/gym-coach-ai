import importlib
import re
import sys
from pathlib import Path

import pytest
import yaml
from cryptography.fernet import Fernet
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from scripts.casa_secretos import generar, main

BASE_DIR = Path(settings.BASE_DIR)
CASA = BASE_DIR / "despliegue" / "casa"
VARIABLES_R2 = (
    "R2_ACCESS_KEY_ID",
    "R2_SECRET_ACCESS_KEY",
    "R2_BUCKET_NAME",
    "R2_ENDPOINT_URL",
    "R2_PUBLIC_DOMAIN",
)


@pytest.fixture
def prod_limpio():
    sys.modules.pop("config.settings.prod", None)
    yield lambda: importlib.import_module("config.settings.prod")
    sys.modules.pop("config.settings.prod", None)


class TestMediaEnDisco:
    @pytest.fixture(autouse=True)
    def entorno_de_casa(self, monkeypatch):
        monkeypatch.setenv("ALLOWED_HOSTS", "gym.ejemplo.ts.net")
        monkeypatch.setenv("MEDIA_STORAGE", "disco")
        for variable in VARIABLES_R2:
            monkeypatch.delenv(variable, raising=False)

    def test_arranca_sin_ninguna_variable_de_r2(self, prod_limpio):
        prod = prod_limpio()

        assert prod.STORAGES["default"]["BACKEND"] == (
            "django.core.files.storage.FileSystemStorage"
        )
        assert not hasattr(prod, "AWS_S3_CUSTOM_DOMAIN")

    def test_la_csp_no_abre_las_imagenes_a_otro_origen(self, prod_limpio):
        prod = prod_limpio()

        assert prod.CONTENT_SECURITY_POLICY["DIRECTIVES"]["img-src"] == ["'self'", "data:"]

    def test_conserva_el_endurecimiento_de_produccion(self, prod_limpio):
        prod = prod_limpio()

        assert prod.DEBUG is False
        assert prod.SECURE_SSL_REDIRECT is True
        assert prod.SECURE_PROXY_SSL_HEADER == ("HTTP_X_FORWARDED_PROTO", "https")
        assert prod.SESSION_COOKIE_SECURE is True
        assert prod.CSRF_COOKIE_SECURE is True


class TestElInterruptorDeMedia:
    def test_sin_valor_sigue_siendo_r2_y_exige_sus_variables(self, monkeypatch, prod_limpio):
        monkeypatch.setenv("ALLOWED_HOSTS", "ejemplo.com")
        monkeypatch.delenv("MEDIA_STORAGE", raising=False)
        for variable in VARIABLES_R2:
            monkeypatch.delenv(variable, raising=False)

        with pytest.raises(ImproperlyConfigured):
            prod_limpio()

    @pytest.mark.parametrize("valor", ["R2", "disk", "local", ""])
    def test_un_valor_desconocido_no_arranca(self, monkeypatch, prod_limpio, valor):
        monkeypatch.setenv("ALLOWED_HOSTS", "ejemplo.com")
        monkeypatch.setenv("MEDIA_STORAGE", valor)

        with pytest.raises(ImproperlyConfigured, match="MEDIA_STORAGE"):
            prod_limpio()


@pytest.fixture(scope="module")
def compose():
    return yaml.safe_load((CASA / "compose.yml").read_text(encoding="utf-8"))["services"]


class TestElCompose:
    def test_postgres_y_redis_no_publican_puertos(self, compose):
        assert "ports" not in compose["db"]
        assert "ports" not in compose["redis"]

    def test_lo_unico_publicado_escucha_solo_en_localhost(self, compose):
        publicados = [
            (nombre, puerto)
            for nombre, servicio in compose.items()
            for puerto in servicio.get("ports", [])
        ]

        assert [nombre for nombre, _ in publicados] == ["caddy"]
        for _, puerto in publicados:
            assert str(puerto).startswith("127.0.0.1:"), puerto

    @pytest.mark.parametrize("nombre", ["web", "worker", "beat"])
    def test_la_aplicacion_usa_produccion_y_el_disco(self, compose, nombre):
        entorno = compose[nombre]["environment"]

        assert entorno["DJANGO_SETTINGS_MODULE"] == "config.settings.prod"
        assert entorno["MEDIA_STORAGE"] == "disco"

    @pytest.mark.parametrize("nombre", ["db", "redis", "web", "worker", "beat", "caddy"])
    def test_vuelve_sola_al_arrancar_docker(self, compose, nombre):
        assert compose[nombre]["restart"] == "unless-stopped"

    def test_el_worker_no_arranca_un_proceso_por_nucleo(self, compose):
        assert "--concurrency=2" in compose["worker"]["command"]

    def test_las_herramientas_no_arrancan_con_up(self, compose):
        assert compose["herramientas"]["profiles"] == ["herramientas"]
        assert any(v.endswith(":/datos:ro") for v in compose["herramientas"]["volumes"])

    def test_caddy_ve_media_en_solo_lectura(self, compose):
        assert "media:/srv/media:ro" in compose["caddy"]["volumes"]


class TestLaImagen:
    def test_el_env_de_desarrollo_no_entra(self):
        lineas = (BASE_DIR / ".dockerignore").read_text(encoding="utf-8").splitlines()

        assert ".env" in lineas
        assert "**/.env" in lineas

    def test_corre_sin_privilegios(self):
        dockerfile = (BASE_DIR / "Dockerfile").read_text(encoding="utf-8")
        ultima_etapa = dockerfile.rsplit("\nFROM ", 1)[1]

        assert re.search(r"^USER app$", ultima_etapa, re.MULTILINE)

    def test_todo_el_python_usa_el_almacen_del_sistema(self):
        dockerfile = (BASE_DIR / "Dockerfile").read_text(encoding="utf-8")
        ultima_etapa = dockerfile.rsplit("\nFROM ", 1)[1]

        for variable in ("SSL_CERT_FILE", "REQUESTS_CA_BUNDLE", "PIP_CERT"):
            assert f"{variable}=/etc/ssl/certs/ca-certificates.crt" in ultima_etapa, variable
        assert "update-ca-certificates" in ultima_etapa

    def test_las_raices_del_pc_no_van_al_repositorio(self):
        gitignore = (BASE_DIR / ".gitignore").read_text(encoding="utf-8").splitlines()

        assert "/despliegue/casa/certificados/" in gitignore
        assert "/respaldos/" in gitignore

    def test_caddy_se_fia_de_tailscale_y_no_lista_directorios(self):
        caddyfile = (CASA / "Caddyfile").read_text(encoding="utf-8")
        sin_comentarios = "\n".join(
            linea for linea in caddyfile.splitlines() if not linea.lstrip().startswith("#")
        )

        assert "trusted_proxies static private_ranges" in sin_comentarios
        assert "browse" not in sin_comentarios


class TestLosSecretos:
    def test_genera_un_env_completo_y_coherente(self):
        entorno = dict(
            linea.split("=", 1)
            for linea in generar("gym.ejemplo.ts.net").splitlines()
            if linea and not linea.startswith("#")
        )

        assert entorno["ALLOWED_HOSTS"] == "gym.ejemplo.ts.net"
        assert entorno["CSRF_TRUSTED_ORIGINS"] == "https://gym.ejemplo.ts.net"
        assert entorno["SITE_URL"] == "https://gym.ejemplo.ts.net"
        Fernet(entorno["FIELD_ENCRYPTION_KEYS"].encode())
        assert re.fullmatch(r"[A-Za-z0-9]{40}", entorno["POSTGRES_PASSWORD"])
        assert re.fullmatch(r"[A-Za-z0-9_-]{60,}", entorno["SECRET_KEY"])

    def test_cada_vez_son_otros(self):
        assert generar("gym.ejemplo.ts.net") != generar("gym.ejemplo.ts.net")

    def test_sin_correo_no_hay_avisos_y_con_correo_van_las_tres(self):
        sin = generar("gym.ejemplo.ts.net")
        con = generar("gym.ejemplo.ts.net", "yo@ejemplo.com")

        assert "VAPID" not in sin
        assert re.search(r"^VAPID_PUBLIC_KEY=[A-Za-z0-9_-]{87}$", con, re.MULTILINE)
        assert re.search(r"^VAPID_PRIVATE_KEY=[A-Za-z0-9_-]{43}$", con, re.MULTILINE)
        assert "VAPID_SUBJECT=mailto:yo@ejemplo.com" in con

    def test_las_claves_de_aviso_se_pueden_anadir_despues(self, capsys):
        assert main(["casa_secretos.py", "--vapid", "yo@ejemplo.com"]) == 0
        salida = capsys.readouterr().out.splitlines()

        assert [linea.split("=", 1)[0] for linea in salida] == [
            "VAPID_PUBLIC_KEY",
            "VAPID_PRIVATE_KEY",
            "VAPID_SUBJECT",
        ]
        assert main(["casa_secretos.py", "--vapid", "no-es-un-correo"]) == 2

    @pytest.mark.parametrize(
        "host",
        ["https://gym.ejemplo.ts.net", "gym.ejemplo.ts.net/", "gym.ejemplo.ts.net:443", "gym"],
    )
    def test_rechaza_lo_que_no_es_un_nombre_de_maquina(self, host):
        with pytest.raises(ValueError):
            generar(host)
