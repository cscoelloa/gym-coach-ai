from datetime import date

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxLengthValidator, MaxValueValidator, MinValueValidator
from django.db import models


class Goal(models.TextChoices):
    BULK = "bulk", "Volumen"
    CUT = "cut", "Definición"
    MAINTAIN = "maintain", "Mantenimiento"


class ExperienceLevel(models.TextChoices):
    BEGINNER = "beginner", "Principiante"
    INTERMEDIATE = "intermediate", "Intermedio"
    ADVANCED = "advanced", "Avanzado"


class Sex(models.TextChoices):
    FEMALE = "female", "Mujer"
    MALE = "male", "Hombre"
    OTHER = "other", "Otro"
    UNDISCLOSED = "undisclosed", "Prefiero no decirlo"


class User(AbstractUser):
    goal = models.CharField(
        "objetivo",
        max_length=16,
        choices=Goal.choices,
        default=Goal.MAINTAIN,
    )
    experience_level = models.CharField(
        "nivel de experiencia",
        max_length=16,
        choices=ExperienceLevel.choices,
        default=ExperienceLevel.BEGINNER,
    )
    sex = models.CharField(
        "sexo",
        max_length=16,
        choices=Sex.choices,
        default=Sex.UNDISCLOSED,
        blank=True,
    )
    birth_date = models.DateField("fecha de nacimiento", null=True, blank=True)
    height_cm = models.PositiveSmallIntegerField(
        "altura (cm)",
        null=True,
        blank=True,
        validators=[MinValueValidator(100), MaxValueValidator(250)],
    )
    target_weight_kg = models.DecimalField(
        "peso objetivo (kg)",
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(30), MaxValueValidator(400)],
    )
    weekly_weight_change_target_kg = models.DecimalField(
        "cambio de peso semanal objetivo (kg)",
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Positivo para ganar, negativo para perder. Ej.: 0.25 o -0.50",
        validators=[MinValueValidator(-2), MaxValueValidator(2)],
    )
    available_days_per_week = models.PositiveSmallIntegerField(
        "días disponibles por semana",
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(7)],
    )
    available_equipment = models.JSONField(
        "equipamiento disponible",
        default=list,
        blank=True,
        help_text="Lista de tipos de equipamiento del catálogo. Vacío = sin restricción.",
    )
    injuries_notes = models.TextField(
        "lesiones y limitaciones",
        blank=True,
        max_length=settings.PROMPT_MAX_INJURIES_CHARS,
        validators=[MaxLengthValidator(settings.PROMPT_MAX_INJURIES_CHARS)],
        help_text="Este texto se le pasa a la IA como dato, nunca como instrucción.",
    )

    class Meta(AbstractUser.Meta):
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"

    def __str__(self):
        return self.get_full_name() or self.username

    @property
    def age(self) -> int | None:
        if not self.birth_date:
            return None
        today = date.today()
        had_birthday = (today.month, today.day) >= (self.birth_date.month, self.birth_date.day)
        return today.year - self.birth_date.year - (0 if had_birthday else 1)

    def ai_profile(self) -> dict:
        return {
            "edad": self.age,
            "sexo": self.get_sex_display() if self.sex else None,
            "altura_cm": self.height_cm,
            "objetivo": self.get_goal_display(),
            "nivel": self.get_experience_level_display(),
            "peso_objetivo_kg": (
                float(self.target_weight_kg) if self.target_weight_kg is not None else None
            ),
            "cambio_semanal_objetivo_kg": (
                float(self.weekly_weight_change_target_kg)
                if self.weekly_weight_change_target_kg is not None
                else None
            ),
            "dias_disponibles": self.available_days_per_week,
            "equipamiento": self.available_equipment or [],
            "lesiones": (self.injuries_notes or "")[: settings.PROMPT_MAX_INJURIES_CHARS],
        }
