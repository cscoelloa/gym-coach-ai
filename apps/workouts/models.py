from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from .taxonomy import BodyPart, Equipment, muscle_label


class MuscleGroup(models.Model):
    slug = models.SlugField("identificador", max_length=64, unique=True)
    name = models.CharField("nombre", max_length=64)

    class Meta:
        verbose_name = "grupo muscular"
        verbose_name_plural = "grupos musculares"
        ordering = ["name"]

    def __str__(self):
        return self.name

    @classmethod
    def from_canonical(cls, canonical: str) -> "MuscleGroup":
        obj, _created = cls.objects.get_or_create(
            slug=canonical.replace(" ", "-"),
            defaults={"name": muscle_label(canonical)},
        )
        return obj


class ExerciseQuerySet(models.QuerySet):
    def visible_to(self, user):
        if user.is_authenticated:
            return self.filter(models.Q(is_global=True) | models.Q(created_by=user))
        return self.filter(is_global=True)


class Exercise(models.Model):
    external_id = models.CharField(
        "id del catálogo",
        max_length=16,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        help_text="Id en el dataset original. Vacío en los ejercicios creados por usuarios.",
    )
    name = models.CharField("nombre", max_length=200)
    slug = models.SlugField("identificador", max_length=220, unique=True)
    category = models.CharField("categoría", max_length=32, blank=True)
    body_part = models.CharField(
        "zona", max_length=32, choices=BodyPart.choices, db_index=True
    )
    equipment = models.CharField(
        "equipamiento", max_length=40, choices=Equipment.choices, blank=True, db_index=True
    )
    target_muscle = models.ForeignKey(
        MuscleGroup,
        verbose_name="músculo objetivo",
        related_name="primary_exercises",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    secondary_muscles = models.ManyToManyField(
        MuscleGroup,
        verbose_name="músculos secundarios",
        related_name="secondary_exercises",
        blank=True,
    )
    instruction_steps = models.JSONField(
        "pasos de ejecución",
        default=dict,
        blank=True,
        help_text="Mapa idioma → lista de pasos. Se guardan los 10 idiomas del dataset.",
    )
    image = models.ImageField("foto", upload_to="exercises/images/", blank=True)
    animation = models.FileField("animación", upload_to="exercises/animations/", blank=True)
    attribution = models.CharField(
        "atribución",
        max_length=255,
        blank=True,
        help_text=(
            "Requisito de licencia del material visual: debe mostrarse junto a la imagen y no "
            "puede alterarse. Ver ADR-007."
        ),
    )
    is_cardio = models.BooleanField("es cardio", default=False, db_index=True)
    is_bodyweight = models.BooleanField("es de peso corporal", default=False)
    is_unilateral = models.BooleanField(
        "unilateral",
        default=False,
        help_text=(
            "Se hace un lado y luego el otro (remo a una mano, zancada). Las series se anotan "
            "POR LADO y el tonelaje cuenta los dos."
        ),
    )
    is_global = models.BooleanField("del catálogo", default=True, db_index=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="creado por",
        related_name="custom_exercises",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    objects = ExerciseQuerySet.as_manager()

    class Meta:
        verbose_name = "ejercicio"
        verbose_name_plural = "ejercicios"
        ordering = ["name"]
        indexes = [models.Index(fields=["body_part", "equipment"])]

    def __str__(self):
        return self.name

    def steps(self, lang: str = "es") -> list[str]:
        data = self.instruction_steps or {}
        return data.get(lang) or data.get("en") or []

    @property
    def default_rest(self) -> int:
        return 180 if self.equipment in ("barbell", "olympic barbell") else 90


class Weekday(models.IntegerChoices):
    MONDAY = 0, _("Lunes")
    TUESDAY = 1, _("Martes")
    WEDNESDAY = 2, _("Miércoles")
    THURSDAY = 3, _("Jueves")
    FRIDAY = 4, _("Viernes")
    SATURDAY = 5, _("Sábado")
    SUNDAY = 6, _("Domingo")


class Source(models.TextChoices):
    MANUAL = "manual", "Creada a mano"
    AI = "ai", "Generada por IA"


class Routine(models.Model):
    Source = Source

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="usuario",
        related_name="routines",
        on_delete=models.CASCADE,
    )
    name = models.CharField("nombre", max_length=120, help_text="Ej.: Empuje, Tirón, Pierna")
    description = models.TextField("descripción", blank=True)
    source = models.CharField(
        "origen", max_length=16, choices=Source.choices, default=Source.MANUAL
    )
    generation = models.ForeignKey(
        "aiassist.AIGeneration",
        verbose_name="generación",
        related_name="routines",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Qué llamada a la IA produjo esta rutina, si fue generada.",
    )
    created_at = models.DateTimeField("creada", auto_now_add=True)
    updated_at = models.DateTimeField("actualizada", auto_now=True)

    class Meta:
        verbose_name = "rutina"
        verbose_name_plural = "rutinas"
        ordering = ["name", "pk"]

    def __str__(self):
        return self.name


class Program(models.Model):
    Source = Source

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="usuario",
        related_name="programs",
        on_delete=models.CASCADE,
    )
    name = models.CharField("nombre", max_length=120, help_text="Ej.: Volumen invierno")
    description = models.TextField("descripción", blank=True)
    is_active = models.BooleanField("activo", default=True, db_index=True)
    source = models.CharField(
        "origen", max_length=16, choices=Source.choices, default=Source.MANUAL
    )
    generation = models.ForeignKey(
        "aiassist.AIGeneration",
        verbose_name="generación",
        related_name="programs",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField("creado", auto_now_add=True)
    updated_at = models.DateTimeField("actualizado", auto_now=True)

    class Meta:
        verbose_name = "programa"
        verbose_name_plural = "programas"
        ordering = ["-is_active", "-created_at"]

    def __str__(self):
        return self.name

    def activate(self):
        Program.objects.filter(user=self.user).exclude(pk=self.pk).update(is_active=False)
        if not self.is_active:
            self.is_active = True
            self.save(update_fields=["is_active"])


class ScheduleEntry(models.Model):
    program = models.ForeignKey(
        Program, verbose_name="programa", related_name="schedule", on_delete=models.CASCADE
    )
    weekday = models.IntegerField("día", choices=Weekday.choices)
    routine = models.ForeignKey(
        Routine,
        verbose_name="rutina",
        related_name="scheduled_on",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Sin rutina = día de descanso.",
    )

    class Meta:
        verbose_name = "día del programa"
        verbose_name_plural = "días del programa"
        ordering = ["weekday"]
        constraints = [
            models.UniqueConstraint(fields=["program", "weekday"], name="unique_day_per_program")
        ]

    def __str__(self):
        return f"{self.get_weekday_display()} — {self.routine or 'Descanso'}"

    @property
    def is_rest_day(self) -> bool:
        return self.routine_id is None


class RoutineExercise(models.Model):
    routine = models.ForeignKey(
        Routine, verbose_name="rutina", related_name="exercises", on_delete=models.CASCADE
    )
    exercise = models.ForeignKey(
        Exercise, verbose_name="ejercicio", related_name="+", on_delete=models.PROTECT
    )
    order = models.PositiveSmallIntegerField("orden", default=0)
    target_sets = models.PositiveSmallIntegerField(
        "series", default=3, validators=[MinValueValidator(1), MaxValueValidator(20)]
    )
    target_reps_min = models.PositiveSmallIntegerField(
        "repeticiones (mín.)", default=8, validators=[MinValueValidator(1), MaxValueValidator(100)]
    )
    target_reps_max = models.PositiveSmallIntegerField(
        "repeticiones (máx.)", default=12, validators=[MinValueValidator(1), MaxValueValidator(100)]
    )
    rest_seconds = models.PositiveSmallIntegerField(
        "descanso (s)",
        default=90,
        validators=[MinValueValidator(0), MaxValueValidator(900)],
    )


    class Meta:
        verbose_name = "ejercicio de la rutina"
        verbose_name_plural = "ejercicios de la rutina"
        ordering = ["routine", "order", "pk"]

    def __str__(self):
        reps = f"{self.target_reps_min}-{self.target_reps_max}"
        return f"{self.exercise.name} — {self.target_sets}×{reps}"


class WorkoutSession(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="usuario",
        related_name="sessions",
        on_delete=models.CASCADE,
    )
    routine = models.ForeignKey(
        Routine,
        verbose_name="rutina",
        related_name="sessions",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Qué rutina se estaba haciendo. Vacío = entrenamiento libre.",
    )
    date = models.DateField("fecha", db_index=True)
    started_at = models.DateTimeField("inicio", null=True, blank=True)
    finished_at = models.DateTimeField("fin", null=True, blank=True)
    notes = models.TextField("notas", max_length=settings.PROMPT_MAX_NOTES_CHARS, blank=True)
    rest_ends_at = models.DateTimeField("fin del descanso", null=True, blank=True)
    rest_seconds = models.PositiveSmallIntegerField("descanso total (s)", null=True, blank=True)

    class Meta:
        verbose_name = "sesión"
        verbose_name_plural = "sesiones"
        ordering = ["-date"]
        indexes = [models.Index(fields=["user", "-date"])]

    def __str__(self):
        return f"{self.user} — {self.date}"


class SetLog(models.Model):
    session = models.ForeignKey(
        WorkoutSession, verbose_name="sesión", related_name="sets", on_delete=models.CASCADE
    )
    exercise = models.ForeignKey(
        Exercise, verbose_name="ejercicio", related_name="set_logs", on_delete=models.PROTECT
    )
    set_number = models.PositiveSmallIntegerField("nº de serie", default=1)
    weight_kg = models.DecimalField(
        "peso (kg)",
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(1000)],
    )
    reps = models.PositiveSmallIntegerField(
        "repeticiones", null=True, blank=True, validators=[MaxValueValidator(1000)]
    )
    rpe = models.DecimalField(
        "RPE",
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
    )
    is_warmup = models.BooleanField("calentamiento", default=False)
    completed = models.BooleanField("completada", default=True)

    class Meta:
        verbose_name = "serie"
        verbose_name_plural = "series"
        ordering = ["session", "exercise", "set_number"]
        indexes = [models.Index(fields=["exercise", "session"])]

    def __str__(self):
        return f"{self.exercise.name} — {self.weight_kg} kg × {self.reps}"


    @classmethod
    def siguiente_numero(cls, session_id: int, exercise_id: int) -> int:
        mayor = cls.objects.filter(session_id=session_id, exercise_id=exercise_id).aggregate(
            mayor=models.Max("set_number")
        )["mayor"]
        return (mayor or 0) + 1

    @classmethod
    def renumerar(cls, session_id: int, exercise_id: int) -> None:
        series = cls.objects.filter(session_id=session_id, exercise_id=exercise_id).order_by(
            "set_number", "pk"
        )
        cambiadas = []
        for numero, serie in enumerate(series, start=1):
            if serie.set_number != numero:
                serie.set_number = numero
                cambiadas.append(serie)
        cls.objects.bulk_update(cambiadas, ["set_number"])
