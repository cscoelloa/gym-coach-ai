import pytest
from cryptography.fernet import Fernet
from django.core.management import call_command
from django.db import connection

from apps.aiassist.fields import (
    PREFIX,
    DecryptionError,
    UndecryptableSecret,
    decrypt,
    encrypt,
)
from apps.aiassist.models import AIProviderConfig, Provider

pytestmark = pytest.mark.django_db

CLAVE_VIEJA = Fernet.generate_key().decode()
CLAVE_NUEVA = Fernet.generate_key().decode()
SECRETO = "sk-ant-api03-ejemplo-de-clave-secreta-1234"


def crear_config(**kwargs):
    return AIProviderConfig.objects.create(
        provider=kwargs.pop("provider", Provider.ANTHROPIC),
        api_key=kwargs.pop("api_key", SECRETO),
        **kwargs,
    )


def valor_en_bruto(pk) -> str:
    with connection.cursor() as cursor:
        cursor.execute("SELECT api_key FROM aiassist_aiproviderconfig WHERE id = %s", [pk])
        return cursor.fetchone()[0]


class TestCifrado:
    def test_ida_y_vuelta(self, settings):
        settings.FIELD_ENCRYPTION_KEYS = [CLAVE_VIEJA]

        assert decrypt(encrypt(SECRETO)) == SECRETO

    def test_el_cifrado_no_es_determinista(self, settings):
        settings.FIELD_ENCRYPTION_KEYS = [CLAVE_VIEJA]

        assert encrypt(SECRETO) != encrypt(SECRETO)

    def test_lo_guardado_en_la_base_de_datos_no_es_el_secreto(self, settings):
        settings.FIELD_ENCRYPTION_KEYS = [CLAVE_VIEJA]
        config = crear_config()

        crudo = valor_en_bruto(config.pk)

        assert SECRETO not in crudo
        assert crudo.startswith(PREFIX)

    def test_al_releer_vuelve_el_texto_plano(self, settings):
        settings.FIELD_ENCRYPTION_KEYS = [CLAVE_VIEJA]
        config = crear_config()

        assert AIProviderConfig.objects.get(pk=config.pk).api_key == SECRETO

    def test_guardar_un_valor_ya_cifrado_no_lo_cifra_otra_vez(self, settings):
        settings.FIELD_ENCRYPTION_KEYS = [CLAVE_VIEJA]
        config = crear_config()
        ya_cifrado = valor_en_bruto(config.pk)

        AIProviderConfig.objects.filter(pk=config.pk).update(api_key=ya_cifrado)

        assert valor_en_bruto(config.pk) == ya_cifrado
        assert AIProviderConfig.objects.get(pk=config.pk).api_key == SECRETO

    def test_descifrar_a_mano_con_una_clave_que_no_sirve_falla(self, settings):
        settings.FIELD_ENCRYPTION_KEYS = [CLAVE_VIEJA]
        cifrado = encrypt(SECRETO)

        settings.FIELD_ENCRYPTION_KEYS = [CLAVE_NUEVA]
        with pytest.raises(DecryptionError):
            decrypt(cifrado)


class TestRotacion:
    def test_multifernet_descifra_con_cualquier_clave_de_la_lista(self, settings):
        settings.FIELD_ENCRYPTION_KEYS = [CLAVE_VIEJA]
        config = crear_config()

        settings.FIELD_ENCRYPTION_KEYS = [CLAVE_NUEVA, CLAVE_VIEJA]

        assert AIProviderConfig.objects.get(pk=config.pk).api_key == SECRETO

    def test_el_comando_recifra_con_la_primera_clave(self, settings):
        settings.FIELD_ENCRYPTION_KEYS = [CLAVE_VIEJA]
        config = crear_config()
        settings.FIELD_ENCRYPTION_KEYS = [CLAVE_NUEVA, CLAVE_VIEJA]

        call_command("rotate_encryption_key")

        settings.FIELD_ENCRYPTION_KEYS = [CLAVE_NUEVA]
        assert AIProviderConfig.objects.get(pk=config.pk).api_key == SECRETO

    def test_dry_run_no_toca_nada(self, settings):
        settings.FIELD_ENCRYPTION_KEYS = [CLAVE_VIEJA]
        config = crear_config()
        antes = valor_en_bruto(config.pk)
        settings.FIELD_ENCRYPTION_KEYS = [CLAVE_NUEVA, CLAVE_VIEJA]

        call_command("rotate_encryption_key", dry_run=True)

        assert valor_en_bruto(config.pk) == antes


class TestNoSeEscapa:
    def test_str_no_revela_la_clave(self, settings):
        settings.FIELD_ENCRYPTION_KEYS = [CLAVE_VIEJA]
        config = crear_config()

        assert SECRETO not in str(config)
        assert SECRETO not in repr(config)

    def test_la_version_enmascarada_solo_deja_ver_el_final(self, settings):
        settings.FIELD_ENCRYPTION_KEYS = [CLAVE_VIEJA]
        config = crear_config()

        enmascarada = config.masked_api_key

        assert SECRETO not in enmascarada
        assert enmascarada.endswith(SECRETO[-4:])

class TestClaveIlegible:
    @pytest.fixture
    def config_ilegible(self, settings):
        settings.FIELD_ENCRYPTION_KEYS = [CLAVE_VIEJA]
        config = crear_config(is_active=True)
        settings.FIELD_ENCRYPTION_KEYS = [CLAVE_NUEVA]
        return AIProviderConfig.objects.get(pk=config.pk)

    def test_leer_la_fila_no_revienta(self, config_ilegible):
        assert isinstance(config_ilegible.api_key, UndecryptableSecret)
        assert not config_ilegible.has_usable_key

    def test_el_admin_puede_listarla_y_ve_el_aviso(self, config_ilegible):
        assert "no se pudo descifrar" in config_ilegible.masked_api_key

    def test_el_marcador_es_falso_como_una_cadena_vacia(self, config_ilegible):
        assert not config_ilegible.api_key

    def test_la_factoria_se_niega_a_usarla(self, config_ilegible):
        from apps.aiassist.providers import ProviderError, get_provider

        with pytest.raises(ProviderError, match="no se puede descifrar"):
            get_provider(config_ilegible)


class TestConfiguracionActiva:
    def test_activar_una_desactiva_las_demas(self, settings):
        settings.FIELD_ENCRYPTION_KEYS = [CLAVE_VIEJA]
        primera = crear_config(is_active=True)

        segunda = crear_config(provider=Provider.OPENAI, model="algun-modelo", is_active=True)

        primera.refresh_from_db()
        assert primera.is_active is False
        assert segunda.is_active is True
        assert AIProviderConfig.objects.filter(is_active=True).count() == 1
