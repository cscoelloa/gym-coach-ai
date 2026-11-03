import importlib
import json
import sys
from pathlib import Path

import pytest
from django.conf import settings

from scripts.check_frontend import verificar

BASE_DIR = Path(settings.BASE_DIR)


class TestFrontendEnLaImagen:
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


class TestLosSettingsDeProduccion:
    @pytest.fixture(autouse=True)
    def variables_de_produccion(self, monkeypatch):
        monkeypatch.setenv("ALLOWED_HOSTS", "ejemplo.com")
        monkeypatch.setenv("EMAIL_HOST", "smtp.ejemplo.com")
        monkeypatch.setenv("EMAIL_HOST_USER", "ci")
        monkeypatch.setenv("EMAIL_HOST_PASSWORD", "ci")
        sys.modules.pop("config.settings.prod", None)
        yield
        sys.modules.pop("config.settings.prod", None)

    def test_media_vive_en_disco(self):
        prod = importlib.import_module("config.settings.prod")

        assert prod.STORAGES["default"]["BACKEND"] == "django.core.files.storage.FileSystemStorage"

    def test_los_estaticos_de_produccion_sobreviven_a_importar_dev(self):
        prod = importlib.import_module("config.settings.prod")
        importlib.import_module("config.settings.dev")

        assert (
            prod.STORAGES["staticfiles"]["BACKEND"]
            == "whitenoise.storage.CompressedManifestStaticFilesStorage"
        )

    def test_la_csp_solo_deja_imagenes_del_propio_origen(self):
        prod = importlib.import_module("config.settings.prod")

        assert prod.CONTENT_SECURITY_POLICY["DIRECTIVES"]["img-src"] == ["'self'", "data:"]
