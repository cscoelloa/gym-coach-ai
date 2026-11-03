from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403

DEBUG = False

MEDIA_STORAGE = env("MEDIA_STORAGE", default="r2").strip()  # noqa: F405
if MEDIA_STORAGE not in ("r2", "disco"):
    raise ImproperlyConfigured(
        f"MEDIA_STORAGE tiene que ser «r2» o «disco». Recibido: {MEDIA_STORAGE!r}."
    )

if MEDIA_STORAGE == "r2":
    STORAGES = {**STORAGES, "default": {"BACKEND": "storages.backends.s3.S3Storage"}}  # noqa: F405

    AWS_ACCESS_KEY_ID = env("R2_ACCESS_KEY_ID")  # noqa: F405
    AWS_SECRET_ACCESS_KEY = env("R2_SECRET_ACCESS_KEY")  # noqa: F405
    AWS_STORAGE_BUCKET_NAME = env("R2_BUCKET_NAME")  # noqa: F405
    AWS_S3_ENDPOINT_URL = env("R2_ENDPOINT_URL")  # noqa: F405
    AWS_S3_CUSTOM_DOMAIN = env("R2_PUBLIC_DOMAIN")  # noqa: F405

    if "//" in AWS_S3_CUSTOM_DOMAIN or AWS_S3_CUSTOM_DOMAIN.endswith("/"):
        raise ImproperlyConfigured(
            f"R2_PUBLIC_DOMAIN tiene que ser solo el host, sin esquema ni barra final. "
            f"Recibido: {AWS_S3_CUSTOM_DOMAIN!r}. Debería ser algo como 'pub-abc123.r2.dev'."
        )

    if AWS_S3_CUSTOM_DOMAIN.endswith(".r2.cloudflarestorage.com"):
        raise ImproperlyConfigured(
            "R2_PUBLIC_DOMAIN apunta al endpoint de la API de R2, que exige peticiones firmadas "
            "y nunca servirá un <img>. Usa el dominio público del bucket: en Cloudflare, R2 → tu "
            "bucket → Settings → Public Development URL → Enable, y copia el 'pub-<id>.r2.dev' "
            "sin https://."
        )

    AWS_S3_REGION_NAME = "auto"
    AWS_DEFAULT_ACL = None
    AWS_QUERYSTRING_AUTH = False
    AWS_S3_FILE_OVERWRITE = True


    CONTENT_SECURITY_POLICY = {
        **CONTENT_SECURITY_POLICY,  # noqa: F405
        "DIRECTIVES": {
            **CONTENT_SECURITY_POLICY["DIRECTIVES"],  # noqa: F405
            "img-src": [
                *CONTENT_SECURITY_POLICY["DIRECTIVES"]["img-src"],  # noqa: F405
                f"https://{AWS_S3_CUSTOM_DOMAIN}",
            ],
        },
    }

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")  # noqa: F405

SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 365
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])  # noqa: F405

EMAIL_HOST = env("EMAIL_HOST", default="")  # noqa: F405
if EMAIL_HOST:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_PORT = env.int("EMAIL_PORT", default=587)  # noqa: F405
    EMAIL_HOST_USER = env("EMAIL_HOST_USER")  # noqa: F405
    EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")  # noqa: F405
    EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)  # noqa: F405
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"


_vapid = [VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY, VAPID_SUBJECT]  # noqa: F405
if any(_vapid) and not all(_vapid):
    raise ImproperlyConfigured(
        "Faltan claves VAPID: hacen falta VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY y VAPID_SUBJECT, "
        "las tres o ninguna. Ver .docs/05-runbook.md."
    )
if VAPID_SUBJECT and not VAPID_SUBJECT.startswith(("mailto:", "https://")):  # noqa: F405
    raise ImproperlyConfigured("VAPID_SUBJECT tiene que empezar por «mailto:» o «https://».")
