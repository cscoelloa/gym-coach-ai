from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class BodyWeightEntry(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="usuario",
        related_name="bodyweight_entries",
        on_delete=models.CASCADE,
    )
    date = models.DateField("fecha", db_index=True)
    weight_kg = models.DecimalField(
        "peso (kg)",
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(20), MaxValueValidator(400)],
    )
    body_fat_pct = models.DecimalField(
        "grasa corporal (%)",
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(70)],
    )
    notes = models.TextField("notas", max_length=settings.PROMPT_MAX_NOTES_CHARS, blank=True)
    created_at = models.DateTimeField("registrado", auto_now_add=True)

    class Meta:
        verbose_name = "registro de peso"
        verbose_name_plural = "registros de peso"
        ordering = ["-date"]
        constraints = [
            models.UniqueConstraint(fields=["user", "date"], name="unique_weight_per_day")
        ]
        indexes = [models.Index(fields=["user", "-date"])]

    def __str__(self):
        return f"{self.user} — {self.date}"
