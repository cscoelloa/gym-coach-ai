from django.contrib import admin, messages
from django.utils.html import format_html

from .forms import KnowledgeDocumentForm
from .models import (
    AIGeneration,
    AIProviderConfig,
    DocumentStatus,
    GenerationKind,
    GenerationStatus,
    KnowledgeDocument,
    PromptTemplate,
    VectorStore,
)
from .providers import ProviderError, get_provider
from .rag import RAGError, create_vector_store, store_summary
from .schemas import ConnectionTest
from .tasks import index_knowledge_document


@admin.register(AIProviderConfig)
class AIProviderConfigAdmin(admin.ModelAdmin):
    list_display = ("provider", "effective_model", "masked_key", "is_active", "updated_at")
    list_filter = ("provider", "is_active")
    actions = ["test_configuration"]

    fieldsets = (
        (None, {"fields": ("provider", "model", "api_key", "is_active")}),
        ("Parámetros", {"fields": ("max_tokens", "effort", "timeout_seconds")}),
    )

    @admin.display(description="API key")
    def masked_key(self, obj):
        return obj.masked_api_key

    @admin.action(description="Probar configuración (hace una llamada real)")
    def test_configuration(self, request, queryset):
        for config in queryset:
            try:
                provider = get_provider(config)
                result = provider.generate_structured(
                    system="Responde en español.",
                    user="Di que la conexión funciona.",
                    schema=ConnectionTest,
                )
            except ProviderError as exc:
                AIGeneration.objects.create(
                    kind=GenerationKind.TEST, provider=config.provider,
                    model=config.effective_model, status=GenerationStatus.ERROR, error=str(exc),
                )
                self.message_user(request, f"{config}: {exc}", level=messages.ERROR)
            except Exception as exc:  # noqa: BLE001 - el admin nunca debe caerse por esto
                self.message_user(
                    request, f"{config}: error inesperado — {exc}", level=messages.ERROR
                )
            else:
                AIGeneration.objects.create(
                    kind=GenerationKind.TEST, provider=config.provider,
                    model=config.effective_model,
                    input_tokens=result.input_tokens, output_tokens=result.output_tokens,
                    latency_ms=result.latency_ms,
                )
                self.message_user(
                    request,
                    f"{config}: correcto — {result.latency_ms} ms, "
                    f"{result.input_tokens}+{result.output_tokens} tokens.",
                    level=messages.SUCCESS,
                )


@admin.register(PromptTemplate)
class PromptTemplateAdmin(admin.ModelAdmin):
    list_display = ("key", "name", "version", "is_active", "created_at")
    list_filter = ("key", "is_active")
    readonly_fields = ("variables_help",)

    fieldsets = (
        (None, {"fields": ("key", "name", "version", "is_active")}),
        ("Contenido", {"fields": ("variables_help", "system_prompt", "user_template")}),
    )

    @admin.display(description="Variables disponibles")
    def variables_help(self, obj):
        if not obj or not obj.available_variables:
            return "Guarda primero eligiendo un tipo para ver sus variables."
        etiquetas = " ".join(f"<code>{{{{ {name} }}}}</code>" for name in obj.available_variables)
        return format_html(
            "{}<p style='margin-top:.5rem'>La entrada del usuario ya llega delimitada como dato; "
            "no quites esa envoltura.</p>",
            format_html(etiquetas),
        )


class KnowledgeDocumentInline(admin.TabularInline):
    model = KnowledgeDocument
    extra = 0
    fields = ("title", "file", "status", "error")
    readonly_fields = ("status", "error")
    show_change_link = True


@admin.register(VectorStore)
class VectorStoreAdmin(admin.ModelAdmin):
    list_display = ("name", "openai_vector_store_id", "documents_summary", "is_active")
    list_filter = ("is_active",)
    readonly_fields = ("openai_vector_store_id",)
    inlines = [KnowledgeDocumentInline]
    actions = ["create_in_openai"]

    @admin.display(description="documentos")
    def documents_summary(self, obj):
        resumen = store_summary(obj)
        if not resumen["total"]:
            return "—"
        texto = f"{resumen['indexed']}/{resumen['total']} indexados"
        if resumen["failed"]:
            texto += f" · {resumen['failed']} fallidos"
        return texto

    @admin.action(description="Crear en OpenAI")
    def create_in_openai(self, request, queryset):
        for store in queryset:
            if store.openai_vector_store_id:
                self.message_user(
                    request, f"«{store}» ya existe en OpenAI.", level=messages.INFO
                )
                continue
            try:
                remote_id = create_vector_store(store)
            except RAGError as exc:
                self.message_user(request, f"«{store}»: {exc}", level=messages.ERROR)
            else:
                self.message_user(
                    request, f"«{store}» creado en OpenAI ({remote_id}).", level=messages.SUCCESS
                )


@admin.register(KnowledgeDocument)
class KnowledgeDocumentAdmin(admin.ModelAdmin):
    form = KnowledgeDocumentForm
    list_display = ("title", "vector_store", "status", "created_at")
    list_filter = ("status", "vector_store")
    readonly_fields = ("openai_file_id", "status", "error", "uploaded_by", "created_at")
    search_fields = ("title",)
    actions = ["reindex"]

    def save_model(self, request, obj, form, change):
        if not obj.uploaded_by_id:
            obj.uploaded_by = request.user
        nuevo_archivo = not change or "file" in form.changed_data
        if nuevo_archivo:
            obj.status = DocumentStatus.PENDING
            obj.error = ""
        super().save_model(request, obj, form, change)

        if nuevo_archivo:
            index_knowledge_document.delay(obj.pk)
            self.message_user(
                request, f"«{obj}» se está indexando en segundo plano.", level=messages.INFO
            )

    @admin.action(description="Volver a indexar")
    def reindex(self, request, queryset):
        for document in queryset:
            index_knowledge_document.delay(document.pk)
        self.message_user(
            request, f"{queryset.count()} documento(s) encolados.", level=messages.INFO
        )


@admin.register(AIGeneration)
class AIGenerationAdmin(admin.ModelAdmin):
    list_display = (
        "created_at", "kind", "provider", "model", "user", "status", "tokens", "latency_ms"
    )
    list_filter = ("kind", "provider", "status", "created_at")
    search_fields = ("user__username", "model")
    date_hierarchy = "created_at"

    readonly_fields = [f.name for f in AIGeneration._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    @admin.display(description="tokens")
    def tokens(self, obj):
        return f"{obj.input_tokens}+{obj.output_tokens}"
