from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403

DEBUG = False

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
        "las tres o ninguna. Ver el README."
    )
if VAPID_SUBJECT and not VAPID_SUBJECT.startswith(("mailto:", "https://")):  # noqa: F405
    raise ImproperlyConfigured("VAPID_SUBJECT tiene que empezar por «mailto:» o «https://».")
