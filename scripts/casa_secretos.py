import base64
import re
import secrets
import string
import sys

HOST_VALIDO = re.compile(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+$")
CORREO_VALIDO = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _b64(datos: bytes) -> str:
    return base64.urlsafe_b64encode(datos).rstrip(b"=").decode()


def claves_vapid() -> tuple[str, str]:
    from cryptography.hazmat.primitives import serialization
    from py_vapid import Vapid

    vapid = Vapid()
    vapid.generate_keys()
    publica = vapid.public_key.public_bytes(
        serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint
    )
    privada = vapid.private_key.private_numbers().private_value.to_bytes(32, "big")
    return _b64(publica), _b64(privada)


def generar(host: str, correo: str | None = None) -> str:
    host = host.strip().lower()
    if not HOST_VALIDO.match(host):
        raise ValueError(
            f"{host!r} no es un nombre de máquina: tiene que ser algo como "
            "'gym.tu-tailnet.ts.net', sin https://, sin barra y sin puerto."
        )
    if correo is not None and not CORREO_VALIDO.match(correo.strip()):
        raise ValueError(f"{correo!r} no parece un correo.")

    from cryptography.fernet import Fernet

    alfanumerico = string.ascii_letters + string.digits
    lineas = [
        "# Generado por `scripts/casa.sh preparar`. No se comitea; guarda una copia fuera del PC.",
        f"ALLOWED_HOSTS={host}",
        f"CSRF_TRUSTED_ORIGINS=https://{host}",
        f"SITE_URL=https://{host}",
        f"SECRET_KEY={secrets.token_urlsafe(50)}",
        f"FIELD_ENCRYPTION_KEYS={Fernet.generate_key().decode()}",
        "POSTGRES_PASSWORD=" + "".join(secrets.choice(alfanumerico) for _ in range(40)),
    ]
    if correo:
        lineas += lineas_vapid(correo)
    return "\n".join(lineas) + "\n"


def lineas_vapid(correo: str) -> list[str]:
    if not CORREO_VALIDO.match(correo.strip()):
        raise ValueError(f"{correo!r} no parece un correo.")
    publica, privada = claves_vapid()
    return [
        f"VAPID_PUBLIC_KEY={publica}",
        f"VAPID_PRIVATE_KEY={privada}",
        f"VAPID_SUBJECT=mailto:{correo.strip()}",
    ]


def main(argv: list[str]) -> int:
    if len(argv) == 3 and argv[1] == "--vapid":
        try:
            sys.stdout.write("\n".join(lineas_vapid(argv[2])) + "\n")
        except ValueError as error:
            print(error, file=sys.stderr)
            return 2
        return 0
    if len(argv) not in (2, 3):
        print(
            "Uso: casa_secretos.py <host.ts.net> [correo-para-los-avisos]\n"
            "     casa_secretos.py --vapid <correo>",
            file=sys.stderr,
        )
        return 2
    try:
        sys.stdout.write(generar(argv[1], argv[2] if len(argv) == 3 else None))
    except ValueError as error:
        print(error, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
