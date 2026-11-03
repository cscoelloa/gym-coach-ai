from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, transaction
from django.template import Template, TemplateSyntaxError

from .fields import EncryptedTextField, UndecryptableSecret


class Provider(models.TextChoices):
    ANTHROPIC = "anthropic", "Anthropic (Claude)"
    OPENAI = "openai", "OpenAI"
    GOOGLE = "google", "Google Gemini"


class Effort(models.TextChoices):
    LOW = "low", "Bajo"
    MEDIUM = "medium", "Medio"
    HIGH = "high", "Alto"
    XHIGH = "xhigh", "Muy alto"
    MAX = "max", "Máximo"


class AIProviderConfig(models.Model):
    provider = models.CharField("proveedor", max_length=16, choices=Provider.choices)
    model = models.CharField(
        "modelo",
        max_length=64,
        help_text=(
            "Identificador exacto del modelo. Para Anthropic, dejarlo vacío usa `claude-opus-5`. "
            "Para OpenAI y Google, consulta la documentación del proveedor: un identificador "
            "inventado devuelve 404."
        ),
        blank=True,
    )
    api_key = EncryptedTextField(
        "API key",
        help_text="Se guarda cifrada. Después de guardarla solo se mostrará enmascarada.",
    )
    max_tokens = models.PositiveIntegerField(
        "máximo de tokens",
        default=16000,
        validators=[MinValueValidator(256), MaxValueValidator(128000)],
        help_text="Tope de salida. Lo fija el admin, nunca el usuario: es control de gasto.",
    )
    effort = models.CharField(
        "esfuerzo",
        max_length=8,
        choices=Effort.choices,
        blank=True,
        help_text="Solo lo soportan algunos modelos. Vacío = el valor por defecto del proveedor.",
    )
    timeout_seconds = models.PositiveSmallIntegerField("tiempo de espera (s)", default=120)
    is_active = models.BooleanField(
        "activa",
        default=True,
        help_text="Al activar una, las demás se desactivan automáticamente.",
    )
    created_at = models.DateTimeField("creada", auto_now_add=True)
    updated_at = models.DateTimeField("actualizada", auto_now=True)

    class Meta:
        verbose_name = "configuración de IA"
        verbose_name_plural = "configuraciones de IA"
        ordering = ["-is_active", "-updated_at"]

    def __str__(self):
        return f"{self.get_provider_display()} — {self.effective_model}"

    def __repr__(self):
        return f"<AIProviderConfig {self.provider}:{self.effective_model}>"

    def save(self, *args, **kwargs):
        with transaction.atomic():
            super().save(*args, **kwargs)
            if self.is_active:
                AIProviderConfig.objects.exclude(pk=self.pk).update(is_active=False)

    @property
    def effective_model(self) -> str:
        return self.model or DEFAULT_MODELS.get(self.provider, "")

    @property
    def has_usable_key(self) -> bool:
        return bool(self.api_key) and not isinstance(self.api_key, UndecryptableSecret)

    @property
    def masked_api_key(self) -> str:
        key = self.api_key
        if isinstance(key, UndecryptableSecret):
            return "(no se pudo descifrar: vuelve a pegar la clave)"
        if not key or len(key) < 8:
            return "····"
        return f"{key[:3]}···{key[-4:]}"

    def clean(self):
        if self.provider and not self.effective_model:
            raise ValidationError(
                {"model": "Este proveedor no tiene modelo por defecto: indica uno explícitamente."}
            )


DEFAULT_MODELS = {Provider.ANTHROPIC: "claude-opus-5"}


class TrainingGoal(models.TextChoices):
    HYPERTROPHY = "hypertrophy", "Hipertrofia"
    STRENGTH = "strength", "Fuerza"
    ENDURANCE = "endurance", "Resistencia muscular"


class ProgrammingRules(models.Model):
    goal = models.CharField(
        "objetivo", max_length=16, choices=TrainingGoal.choices, unique=True
    )
    sets_min = models.PositiveSmallIntegerField("series mínimas por ejercicio", default=3)
    sets_max = models.PositiveSmallIntegerField("series máximas por ejercicio", default=4)
    reps_min = models.PositiveSmallIntegerField(
        "repeticiones mínimas",
        help_text=(
            "Una banda por objetivo, no un número por ejercicio: dentro de ella caben 8-12 en un "
            "press y 12-20 en un curl, que son las dos cosas correctas."
        ),
    )
    reps_max = models.PositiveSmallIntegerField("repeticiones máximas")
    rest_min_compound = models.PositiveSmallIntegerField(
        "descanso mínimo en compuestos (s)",
        help_text="Con menos, la serie siguiente cae por fatiga y no por estímulo.",
    )
    rest_min_isolation = models.PositiveSmallIntegerField("descanso mínimo en aislamiento (s)")
    sets_min_per_muscle_day = models.PositiveSmallIntegerField(
        "series mínimas por músculo y día",
        help_text=(
            "Se acota a lo que el día permite: con tres ejercicios y tres músculos no se pueden "
            "exigir seis series a cada uno."
        ),
    )

    class Meta:
        verbose_name = "reglas de programación"
        verbose_name_plural = "reglas de programación"
        ordering = ["goal"]

    def __str__(self):
        return f"{self.get_goal_display()}: {self.sets_min}-{self.sets_max} series"

    def clean(self):
        parejas = (
            ("sets_min", "sets_max", "series"),
            ("reps_min", "reps_max", "repeticiones"),
        )
        for campo_min, campo_max, que in parejas:
            minimo, maximo = getattr(self, campo_min), getattr(self, campo_max)
            if minimo is not None and maximo is not None and minimo > maximo:
                raise ValidationError(
                    {campo_max: f"El máximo de {que} no puede ser menor que el mínimo."}
                )


PROGRAMACION_POR_DEFECTO = {
    TrainingGoal.HYPERTROPHY: {
        "sets_min": 3, "sets_max": 4,
        "reps_min": 6, "reps_max": 20,
        "rest_min_compound": 120, "rest_min_isolation": 90,
        "sets_min_per_muscle_day": 6,
    },
    TrainingGoal.STRENGTH: {
        "sets_min": 3, "sets_max": 6,
        "reps_min": 3, "reps_max": 8,
        "rest_min_compound": 180, "rest_min_isolation": 120,
        "sets_min_per_muscle_day": 4,
    },
    TrainingGoal.ENDURANCE: {
        "sets_min": 2, "sets_max": 4,
        "reps_min": 12, "reps_max": 30,
        "rest_min_compound": 60, "rest_min_isolation": 45,
        "sets_min_per_muscle_day": 4,
    },
}


class PromptKey(models.TextChoices):
    ROUTINE_GENERATION = "routine_generation", "Generación de rutinas"
    PROGRESS_ANALYSIS = "progress_analysis", "Análisis de progreso"
    WEIGHT_ANALYSIS = "weight_analysis", "Análisis de peso"


PROMPT_VARIABLES = {
    PromptKey.ROUTINE_GENERATION: [
        "perfil", "objetivo", "dias_disponibles", "reparto", "programacion", "equipamiento",
        "lesiones", "candidatos", "metricas",
    ],
    PromptKey.PROGRESS_ANALYSIS: ["perfil", "metricas", "semanas", "rutina_actual"],
    PromptKey.WEIGHT_ANALYSIS: [
        "perfil", "objetivo", "peso_actual", "peso_anterior", "tendencia", "objetivo_semanal",
    ],
}


class PromptTemplate(models.Model):
    key = models.CharField("tipo", max_length=32, choices=PromptKey.choices, db_index=True)
    name = models.CharField("nombre", max_length=120)
    system_prompt = models.TextField("instrucciones de sistema")
    user_template = models.TextField(
        "plantilla del mensaje",
        help_text="Plantilla de Django. Las variables disponibles aparecen debajo.",
    )
    version = models.PositiveSmallIntegerField("versión", default=1)
    is_active = models.BooleanField("activa", default=True)
    created_at = models.DateTimeField("creada", auto_now_add=True)

    class Meta:
        verbose_name = "prompt"
        verbose_name_plural = "prompts"
        ordering = ["key", "-version"]
        constraints = [
            models.UniqueConstraint(fields=["key", "version"], name="unique_prompt_version")
        ]

    def __str__(self):
        return f"{self.get_key_display()} v{self.version}"

    def save(self, *args, **kwargs):
        with transaction.atomic():
            super().save(*args, **kwargs)
            if self.is_active:
                PromptTemplate.objects.filter(key=self.key).exclude(pk=self.pk).update(
                    is_active=False
                )

    @property
    def available_variables(self) -> list[str]:
        return PROMPT_VARIABLES.get(self.key, [])

    def clean(self):
        for field in ("system_prompt", "user_template"):
            try:
                Template(getattr(self, field) or "")
            except TemplateSyntaxError as exc:
                raise ValidationError({field: f"Error de sintaxis en la plantilla: {exc}"}) from exc


class VectorStore(models.Model):
    name = models.CharField("nombre", max_length=120)
    description = models.TextField("descripción", blank=True)
    openai_vector_store_id = models.CharField(
        "id en OpenAI", max_length=64, blank=True, help_text="Se rellena al crearlo en OpenAI."
    )
    is_active = models.BooleanField("activo", default=True)
    created_at = models.DateTimeField("creado", auto_now_add=True)

    class Meta:
        verbose_name = "almacén vectorial"
        verbose_name_plural = "almacenes vectoriales"
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def is_ready(self) -> bool:
        return bool(self.openai_vector_store_id)


class DocumentStatus(models.TextChoices):
    PENDING = "pending", "Pendiente"
    INDEXING = "indexing", "Indexando"
    INDEXED = "indexed", "Indexado"
    FAILED = "failed", "Fallido"


class KnowledgeDocument(models.Model):
    vector_store = models.ForeignKey(
        VectorStore, verbose_name="almacén", related_name="documents", on_delete=models.CASCADE
    )
    title = models.CharField("título", max_length=200)
    file = models.FileField("archivo", upload_to="knowledge/")
    openai_file_id = models.CharField("id de archivo en OpenAI", max_length=64, blank=True)
    status = models.CharField(
        "estado", max_length=16, choices=DocumentStatus.choices,
        default=DocumentStatus.PENDING, db_index=True,
    )
    error = models.TextField("error", blank=True)
    attributes = models.JSONField(
        "atributos", default=dict, blank=True,
        help_text="Metadatos para filtrar en la búsqueda. Máximo 16 claves.",
    )
    uploaded_by = models.ForeignKey(
        "accounts.User", verbose_name="subido por", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="+",
    )
    created_at = models.DateTimeField("subido", auto_now_add=True)

    class Meta:
        verbose_name = "documento"
        verbose_name_plural = "documentos"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class GenerationKind(models.TextChoices):
    ROUTINE = "routine", "Rutina"
    PROGRESS = "progress", "Análisis de progreso"
    WEIGHT = "weight", "Análisis de peso"
    TEST = "test", "Prueba de configuración"


class GenerationStatus(models.TextChoices):
    OK = "ok", "Correcta"
    ERROR = "error", "Error"
    REFUSED = "refused", "Rechazada por el modelo"


class AIGeneration(models.Model):
    user = models.ForeignKey(
        "accounts.User", verbose_name="usuario", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="ai_generations",
    )
    kind = models.CharField("tipo", max_length=16, choices=GenerationKind.choices, db_index=True)
    provider = models.CharField("proveedor", max_length=16)
    model = models.CharField("modelo", max_length=64)
    prompt_rendered = models.TextField("prompt enviado", blank=True)
    raw_response = models.TextField("respuesta cruda", blank=True)
    parsed_output = models.JSONField("salida validada", null=True, blank=True)
    request_params = models.JSONField(
        "lo que se pidió",
        default=dict,
        blank=True,
        help_text="El reparto semanal que pidió la persona, para poder contrastarlo con la salida.",
    )
    input_tokens = models.PositiveIntegerField("tokens de entrada", default=0)
    output_tokens = models.PositiveIntegerField("tokens de salida", default=0)
    latency_ms = models.PositiveIntegerField("latencia (ms)", default=0)
    status = models.CharField(
        "estado", max_length=16, choices=GenerationStatus.choices, default=GenerationStatus.OK
    )
    error = models.TextField("error", blank=True)
    created_at = models.DateTimeField("fecha", auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "generación"
        verbose_name_plural = "generaciones"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "kind", "-created_at"])]

    def __str__(self):
        return f"{self.get_kind_display()} — {self.created_at:%Y-%m-%d %H:%M}"
