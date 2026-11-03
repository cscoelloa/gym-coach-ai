from django.conf import settings
from django.db import models

from .registry import CATEGORY_LABELS


class Metric(models.Model):
    key = models.SlugField("clave", max_length=64, unique=True)
    label = models.CharField("nombre", max_length=120)
    description = models.TextField("descripción")
    unit = models.CharField("unidad", max_length=32, blank=True)
    category = models.CharField("categoría", max_length=32, db_index=True)
    chart = models.CharField("tipo de gráfico", max_length=16)
    order = models.PositiveSmallIntegerField("orden", default=0)

    is_active = models.BooleanField(
        "activa",
        default=True,
        help_text="Desactivada, deja de calcularse y desaparece del catálogo de los usuarios.",
    )
    send_to_ai = models.BooleanField(
        "enviar a la IA",
        default=True,
        help_text="Si se incluye en el prompt del análisis de progreso.",
    )
    default_visible = models.BooleanField(
        "visible por defecto",
        default=True,
        help_text="Si aparece en el panel de quien no haya elegido nada todavía.",
    )

    class Meta:
        verbose_name = "métrica"
        verbose_name_plural = "métricas"
        ordering = ["category", "order"]

    def __str__(self):
        return self.label

    @property
    def category_label(self) -> str:
        return CATEGORY_LABELS.get(self.category, self.category)

    @property
    def spec(self):
        from .registry import REGISTRY

        return REGISTRY.get(self.key)


class UserMetricPreference(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="usuario",
        related_name="metric_preferences",
        on_delete=models.CASCADE,
    )
    metric = models.ForeignKey(
        Metric, verbose_name="métrica", related_name="preferences", on_delete=models.CASCADE
    )
    is_visible = models.BooleanField("visible", default=True)
    order = models.PositiveSmallIntegerField("orden", default=0)

    class Meta:
        verbose_name = "preferencia de métrica"
        verbose_name_plural = "preferencias de métricas"
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(fields=["user", "metric"], name="unique_metric_per_user")
        ]

    def __str__(self):
        return f"{self.user} — {self.metric}"
