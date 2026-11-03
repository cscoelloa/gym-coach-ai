from django.apps import AppConfig


class MetricsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.metrics"
    verbose_name = "Métricas"

    def ready(self):
        from . import catalog  # noqa: F401
