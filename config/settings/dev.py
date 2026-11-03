from .base import *  # noqa: F403

DEBUG = True


if VITE_DEV_SERVER_URL:  # noqa: F405
    _vite = VITE_DEV_SERVER_URL.rstrip("/")  # noqa: F405
    _vite_ws = _vite.replace("http://", "ws://").replace("https://", "wss://")
    _directivas = CONTENT_SECURITY_POLICY["DIRECTIVES"]  # noqa: F405

    CONTENT_SECURITY_POLICY = {
        **CONTENT_SECURITY_POLICY,  # noqa: F405
        "DIRECTIVES": {
            **_directivas,
            "script-src": [*_directivas["script-src"], _vite],
            "connect-src": [*_directivas["connect-src"], _vite, _vite_ws],
            "style-src": [*_directivas["style-src"], _vite],
            "font-src": [*_directivas["font-src"], _vite],
            "img-src": [*_directivas["img-src"], _vite],
        },
    }
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]"]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

STORAGES = {  # noqa: F405
    **STORAGES,  # noqa: F405
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

MIDDLEWARE = [m for m in MIDDLEWARE if "whitenoise" not in m]  # noqa: F405

CELERY_TASK_ALWAYS_EAGER = env.bool("CELERY_TASK_ALWAYS_EAGER", default=True)  # noqa: F405
CELERY_TASK_EAGER_PROPAGATES = True
