from cryptography.fernet import Fernet, InvalidToken, MultiFernet
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models

PREFIX = "enc$"


class DecryptionError(Exception):
    pass


class UndecryptableSecret(str):
    __slots__ = ()

    def __new__(cls):
        return super().__new__(cls, "")


def get_cipher() -> MultiFernet:
    keys = getattr(settings, "FIELD_ENCRYPTION_KEYS", None)
    if not keys:
        raise ImproperlyConfigured(
            "Falta FIELD_ENCRYPTION_KEYS. Genera una clave con "
            "`python -c \"from cryptography.fernet import Fernet; "
            'print(Fernet.generate_key().decode())"` y añádela al .env. '
            "Ver el README"
        )
    return MultiFernet([Fernet(key.strip()) for key in keys])


def encrypt(value: str) -> str:
    return PREFIX + get_cipher().encrypt(value.encode()).decode()


def decrypt(value: str) -> str:
    try:
        return get_cipher().decrypt(value.removeprefix(PREFIX).encode()).decode()
    except InvalidToken as exc:
        raise DecryptionError(
            "No se pudo descifrar un valor: ninguna de las claves de FIELD_ENCRYPTION_KEYS sirve. "
            "¿Se retiró una clave antes de ejecutar `rotate_encryption_key`? "
            "Ver el README"
        ) from exc


def is_encrypted(value) -> bool:
    return isinstance(value, str) and value.startswith(PREFIX)


class EncryptedTextField(models.TextField):
    def get_prep_value(self, value):
        if not value:
            return value
        if is_encrypted(value):
            return value
        return encrypt(str(value))

    def from_db_value(self, value, expression, connection):
        if not value:
            return value
        if not is_encrypted(value):
            return value
        try:
            return decrypt(value)
        except DecryptionError:
            return UndecryptableSecret()

    def to_python(self, value):
        if is_encrypted(value):
            return decrypt(value)
        return value
