from rest_framework import serializers

from apps.accounts.models import User
from apps.aiassist.models import (
    AIGeneration,
    AIProviderConfig,
    DocumentStatus,
    KnowledgeDocument,
    ProgrammingRules,
    PromptTemplate,
    VectorStore,
)
from apps.aiassist.services import programacion
from apps.aiassist.validators import validate_knowledge_document
from apps.metrics.models import Metric


class ProveedorSerializer(serializers.ModelSerializer):
    api_key = serializers.CharField(write_only=True, required=False, allow_blank=False)
    masked_api_key = serializers.CharField(read_only=True)
    effective_model = serializers.CharField(read_only=True)
    has_usable_key = serializers.BooleanField(read_only=True)
    provider_label = serializers.CharField(source="get_provider_display", read_only=True)

    class Meta:
        model = AIProviderConfig
        fields = (
            "id", "provider", "provider_label", "model", "effective_model",
            "api_key", "masked_api_key", "has_usable_key",
            "max_tokens", "effort", "timeout_seconds", "is_active",
            "created_at", "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")

    def validate(self, datos):
        if self.instance is None and not datos.get("api_key"):
            raise serializers.ValidationError({"api_key": ["Hace falta una clave."]})
        return datos


class PromptSerializer(serializers.ModelSerializer):
    key_label = serializers.CharField(source="get_key_display", read_only=True)
    available_variables = serializers.ListField(child=serializers.CharField(), read_only=True)

    class Meta:
        model = PromptTemplate
        fields = (
            "id", "key", "key_label", "name", "system_prompt", "user_template",
            "version", "is_active", "available_variables", "created_at",
        )
        read_only_fields = ("created_at",)

    def validate(self, datos):
        instancia = PromptTemplate(**{**self._actuales(), **datos})
        instancia.pk = self.instance.pk if self.instance else None
        instancia.clean()
        return datos

    def _actuales(self) -> dict:
        if self.instance is None:
            return {}
        return {
            campo: getattr(self.instance, campo)
            for campo in ("key", "name", "system_prompt", "user_template", "version", "is_active")
        }


class AlmacenSerializer(serializers.ModelSerializer):
    is_ready = serializers.BooleanField(read_only=True)
    documentos = serializers.SerializerMethodField()

    class Meta:
        model = VectorStore
        fields = (
            "id", "name", "description", "openai_vector_store_id", "is_ready",
            "is_active", "documentos", "created_at",
        )
        read_only_fields = ("openai_vector_store_id", "created_at")

    def get_documentos(self, obj) -> dict:
        return {
            "total": getattr(obj, "n_total", 0),
            "indexados": getattr(obj, "n_indexados", 0),
            "fallidos": getattr(obj, "n_fallidos", 0),
        }


class DocumentoSerializer(serializers.ModelSerializer):
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    subido_por = serializers.CharField(source="uploaded_by.username", read_only=True, default=None)
    almacen = serializers.CharField(source="vector_store.name", read_only=True)

    class Meta:
        model = KnowledgeDocument
        fields = (
            "id", "vector_store", "almacen", "title", "file", "status", "status_label",
            "error", "attributes", "subido_por", "created_at",
        )
        read_only_fields = ("status", "error", "created_at")

    def validate_file(self, archivo):
        validate_knowledge_document(archivo)
        return archivo


class GeneracionListaSerializer(serializers.ModelSerializer):
    usuario = serializers.CharField(source="user.username", read_only=True, default=None)
    kind_label = serializers.CharField(source="get_kind_display", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = AIGeneration
        fields = (
            "id", "usuario", "kind", "kind_label", "provider", "model",
            "status", "status_label", "input_tokens", "output_tokens", "latency_ms",
            "error", "created_at",
        )


class GeneracionDetalleSerializer(GeneracionListaSerializer):
    class Meta(GeneracionListaSerializer.Meta):
        fields = (
            *GeneracionListaSerializer.Meta.fields,
            "prompt_rendered", "raw_response", "parsed_output",
        )


class UsuarioSerializer(serializers.ModelSerializer):
    CAMPOS_DE_SALUD = (
        "birth_date", "height_cm", "target_weight_kg", "weekly_weight_change_target_kg",
        "sex", "injuries_notes",
    )

    entrenamientos = serializers.IntegerField(read_only=True, default=0)
    rutinas = serializers.IntegerField(read_only=True, default=0)
    generaciones = serializers.IntegerField(read_only=True, default=0)
    bloqueado = serializers.BooleanField(read_only=True, default=False)

    class Meta:
        model = User
        fields = (
            "id", "username", "email", "first_name", "is_active", "is_staff",
            "date_joined", "last_login",
            "entrenamientos", "rutinas", "generaciones", "bloqueado",
        )
        read_only_fields = (
            "username", "email", "first_name", "date_joined", "last_login",
        )


class MetricaDeGestionSerializer(serializers.ModelSerializer):
    category_label = serializers.CharField(read_only=True)
    en_paneles = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Metric
        fields = (
            "id", "key", "label", "description", "unit", "category", "category_label",
            "chart", "is_active", "send_to_ai", "default_visible", "en_paneles",
        )
        read_only_fields = ("key", "label", "description", "unit", "category", "chart")


class ProgramacionSerializer(serializers.ModelSerializer):
    goal_label = serializers.CharField(source="get_goal_display", read_only=True)
    resumen = serializers.SerializerMethodField()

    class Meta:
        model = ProgrammingRules
        fields = (
            "id", "goal", "goal_label", "sets_min", "sets_max", "reps_min", "reps_max",
            "rest_min_compound", "rest_min_isolation", "sets_min_per_muscle_day", "resumen",
        )
        read_only_fields = ("goal",)

    def get_resumen(self, obj) -> str:
        return programacion.resumen(programacion.reglas_de(obj.goal))

    def validate(self, datos):
        instancia = ProgrammingRules(**{**self._actuales(), **datos})
        instancia.pk = self.instance.pk if self.instance else None
        instancia.clean()
        return datos

    def _actuales(self) -> dict:
        if self.instance is None:
            return {}
        return {
            campo: getattr(self.instance, campo)
            for campo in ("goal", "sets_min", "sets_max", "reps_min", "reps_max",
                          "rest_min_compound", "rest_min_isolation", "sets_min_per_muscle_day")
        }


ESTADOS_PROBLEMATICOS = (DocumentStatus.FAILED,)
