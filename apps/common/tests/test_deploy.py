import importlib
import json
import sys
import tomllib
from pathlib import Path

import pytest
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from scripts.check_frontend import verificar

BASE_DIR = Path(settings.BASE_DIR)


class TestFrontendEnLaImagen:
    def test_railway_construye_con_node_y_el_proveedor_python(self):
        railway = tomllib.loads((BASE_DIR / "railway.toml").read_text(encoding="utf-8"))
        railpack = json.loads((BASE_DIR / "railpack.json").read_text(encoding="utf-8"))
        assert railway["build"]["builder"] == "RAILPACK"
        assert railpack["provider"] == "python"
        assert railpack["packages"]["node"] == "22"
        assert railway["build"]["buildCommand"] in railpack["steps"]["build"]["commands"]
        assert "deploy" not in railway

    def test_el_arranque_verifica_antes_de_migrar(self):
        script = (BASE_DIR / "scripts/start-web.sh").read_text(encoding="utf-8")
        assert script.index("python scripts/check_frontend.py") < script.index("python manage.py")

    @pytest.fixture
    def bundle(self, tmp_path):
        (tmp_path / ".vite").mkdir()
        (tmp_path / "assets").mkdir()
        manifiesto = {
            "src/main.tsx": {
                "file": "assets/main.js",
                "css": ["assets/main.css"],
                "imports": ["_vendor.js"],
                "dynamicImports": ["src/page.tsx"],
            },
            "_vendor.js": {"file": "assets/vendor.js"},
            "src/page.tsx": {"file": "assets/page.js"},
        }
        for archivo in ["main.js", "main.css", "vendor.js", "page.js"]:
            (tmp_path / "assets" / archivo).write_text("contenido", encoding="utf-8")
        (tmp_path / ".vite/manifest.json").write_text(json.dumps(manifiesto), encoding="utf-8")
        return tmp_path

    def test_acepta_un_bundle_completo(self, bundle):
        verificar(bundle)

    @pytest.mark.parametrize("archivo", ["main.js", "main.css", "vendor.js", "page.js"])
    def test_rechaza_bundles_incompletos(self, bundle, archivo):
        (bundle / "assets" / archivo).unlink()
        with pytest.raises(ValueError, match="Falta un archivo"):
            verificar(bundle)

    def test_reproduce_la_imagen_sin_frontend_del_log(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            verificar(tmp_path)

    @pytest.mark.parametrize("contenido", ["no es JSON", "{}", "[]"])
    def test_rechaza_manifiesto_invalido(self, bundle, contenido):
        (bundle / ".vite/manifest.json").write_text(contenido, encoding="utf-8")
        with pytest.raises(ValueError):
            verificar(bundle)

    def test_rechaza_imports_sin_entrada(self, bundle):
        ruta = bundle / ".vite/manifest.json"
        manifiesto = json.loads(ruta.read_text(encoding="utf-8"))
        del manifiesto["src/page.tsx"]
        ruta.write_text(json.dumps(manifiesto), encoding="utf-8")
        with pytest.raises(ValueError, match="Falta una entrada"):
            verificar(bundle)


class TestElServidorWSGI:
    def test_gunicorn_esta_en_requirements(self):
        texto = (BASE_DIR / "requirements.txt").read_text(encoding="utf-8")

        assert "gunicorn" in texto

    def test_el_script_de_arranque_migra_y_recolecta_antes_de_servir(self):
        script = (BASE_DIR / "scripts" / "start-web.sh").read_text(encoding="utf-8")

        assert "manage.py migrate" in script
        assert "manage.py collectstatic" in script
        assert script.index("migrate") < script.index("gunicorn")
        assert script.index("collectstatic") < script.index("gunicorn")

    def test_el_timeout_de_gunicorn_cubre_una_generacion_con_reintentos(self):
        script = (BASE_DIR / "scripts" / "start-web.sh").read_text(encoding="utf-8")

        assert "--timeout 120" in script

    def test_el_procfile_declara_los_tres_procesos(self):
        procfile = (BASE_DIR / "Procfile").read_text(encoding="utf-8")

        assert "web:" in procfile
        assert "worker:" in procfile
        assert "celery" in procfile
        assert "beat:" in procfile


class TestMediaEnProduccion:
    @pytest.fixture(autouse=True)
    def variables_de_produccion(self, monkeypatch):
        monkeypatch.setenv("ALLOWED_HOSTS", "ejemplo.com")
        monkeypatch.setenv("EMAIL_HOST", "smtp.ejemplo.com")
        monkeypatch.setenv("EMAIL_HOST_USER", "ci")
        monkeypatch.setenv("EMAIL_HOST_PASSWORD", "ci")
        monkeypatch.setenv("R2_ACCESS_KEY_ID", "ci")
        monkeypatch.setenv("R2_SECRET_ACCESS_KEY", "ci")
        monkeypatch.setenv("R2_BUCKET_NAME", "ci-bucket")
        monkeypatch.setenv("R2_ENDPOINT_URL", "https://ejemplo.r2.cloudflarestorage.com")
        monkeypatch.setenv("R2_PUBLIC_DOMAIN", "pub-ejemplo.r2.dev")

    def test_prod_usa_el_storage_de_s3(self):
        prod = importlib.import_module("config.settings.prod")

        assert prod.STORAGES["default"]["BACKEND"] == "storages.backends.s3.S3Storage"

    def test_las_urls_son_publicas_y_sin_firma(self):
        prod = importlib.import_module("config.settings.prod")

        assert prod.AWS_S3_CUSTOM_DOMAIN == "pub-ejemplo.r2.dev"
        assert prod.AWS_QUERYSTRING_AUTH is False

    def test_sobrescribe_en_vez_de_generar_nombres_al_azar(self):
        prod = importlib.import_module("config.settings.prod")

        assert prod.AWS_S3_FILE_OVERWRITE is True

    def test_no_toca_el_default_de_desarrollo(self):
        base = importlib.import_module("config.settings.base")

        assert base.STORAGES["default"]["BACKEND"] == "django.core.files.storage.FileSystemStorage"

    def test_los_estaticos_de_produccion_sobreviven_a_importar_dev(self):
        prod = importlib.import_module("config.settings.prod")
        importlib.import_module("config.settings.dev")

        assert (
            prod.STORAGES["staticfiles"]["BACKEND"]
            == "whitenoise.storage.CompressedManifestStaticFilesStorage"
        )

    def test_la_csp_deja_entrar_las_imagenes_del_bucket(self):
        prod = importlib.import_module("config.settings.prod")

        img_src = prod.CONTENT_SECURITY_POLICY["DIRECTIVES"]["img-src"]

        assert f"https://{prod.AWS_S3_CUSTOM_DOMAIN}" in img_src, (
            "la CSP de producción no permite el dominio de R2: ninguna imagen del catálogo cargará"
        )
        assert len(img_src) == 3

    @pytest.mark.parametrize(
        "valor,motivo",
        [
            (
                "https://pub-ejemplo.r2.dev",
                "django-storages le pega el esquema: quedaría https://https://… y el navegador "
                "descarta la fuente entera de la CSP",
            ),
            ("pub-ejemplo.r2.dev/", "la barra final duplica la de la ruta"),
            (
                "465ae845.r2.cloudflarestorage.com",
                "es el endpoint de la API, que exige peticiones firmadas y nunca sirve un <img>",
            ),
        ],
    )
    def test_un_dominio_publico_mal_puesto_no_deja_arrancar(self, monkeypatch, valor, motivo):
        monkeypatch.setenv("R2_PUBLIC_DOMAIN", valor)
        sys.modules.pop("config.settings.prod", None)

        with pytest.raises(ImproperlyConfigured):
            importlib.import_module("config.settings.prod")

    def test_el_dominio_publico_correcto_arranca(self, monkeypatch):
        monkeypatch.setenv("R2_PUBLIC_DOMAIN", "pub-ejemplo.r2.dev")
        sys.modules.pop("config.settings.prod", None)

        prod = importlib.import_module("config.settings.prod")

        assert prod.AWS_S3_CUSTOM_DOMAIN == "pub-ejemplo.r2.dev"

    def test_ajustar_la_csp_de_produccion_no_toca_la_de_desarrollo(self):
        importlib.import_module("config.settings.prod")
        base = importlib.import_module("config.settings.base")

        assert base.CONTENT_SECURITY_POLICY["DIRECTIVES"]["img-src"] == ["'self'", "data:"]
