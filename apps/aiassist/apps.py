from django.apps import AppConfig


class AiassistConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.aiassist"
    verbose_name = "Asistente de IA"

    def ready(self):
        from . import signals  # noqa: F401
