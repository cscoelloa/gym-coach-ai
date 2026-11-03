from django.conf import settings
from django.db import models


class NotificationKind(models.TextChoices):
    STALL_DETECTED = "stall_detected", "Estancamiento detectado"
    WEIGHT_OFF_TRACK = "weight_off_track", "Peso fuera de objetivo"
    PROGRESS_READY = "progress_ready", "Análisis de progreso listo"
    ROUTINE_READY = "routine_ready", "Rutina lista"


class Severity(models.TextChoices):
    INFO = "info", "Información"
    WARNING = "warning", "Atención"


class Notification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="usuario",
        related_name="notifications",
        on_delete=models.CASCADE,
    )
    kind = models.CharField("tipo", max_length=32, choices=NotificationKind.choices, db_index=True)
    severity = models.CharField(
        "importancia", max_length=16, choices=Severity.choices, default=Severity.INFO
    )
    title = models.CharField("título", max_length=200)
    body = models.TextField("contenido")
    payload = models.JSONField(
        "datos", default=dict, blank=True, help_text="Detalle estructurado para la interfaz."
    )
    generation = models.ForeignKey(
        "aiassist.AIGeneration",
        verbose_name="generación",
        related_name="notifications",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Qué llamada a la IA la produjo, si vino de ahí.",
    )
    is_read = models.BooleanField("leída", default=False, db_index=True)
    emailed_at = models.DateTimeField("enviada por correo", null=True, blank=True)
    created_at = models.DateTimeField("fecha", auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "notificación"
        verbose_name_plural = "notificaciones"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "is_read", "-created_at"])]

    def __str__(self):
        return self.title

    @property
    def badge_class(self) -> str:
        return "badge-warn" if self.severity == Severity.WARNING else "badge-accent"


class SuscripcionPush(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="usuario",
        related_name="suscripciones_push",
        on_delete=models.CASCADE,
    )
    endpoint = models.URLField("endpoint", max_length=1000, unique=True)
    p256dh = models.CharField("clave p256dh", max_length=200)
    auth = models.CharField("clave auth", max_length=100)
    creada = models.DateTimeField("creada", auto_now_add=True)

    class Meta:
        verbose_name = "suscripción push"
        verbose_name_plural = "suscripciones push"

    def __str__(self):
        return f"{self.user} — {self.endpoint[:40]}…"
