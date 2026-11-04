import logging

from axes.models import AccessAttempt
from django.conf import settings
from django.db.models import Case, Count, Exists, IntegerField, OuterRef, Q, When
from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.aiassist import rag
from apps.aiassist.models import (
    AIGeneration,
    AIProviderConfig,
    DocumentStatus,
    GenerationKind,
    GenerationStatus,
    KnowledgeDocument,
    ProgrammingRules,
    PromptTemplate,
    TrainingGoal,
    VectorStore,
)
from apps.aiassist.providers import ProviderError, get_provider
from apps.aiassist.schemas import ConnectionTest
from apps.aiassist.services import prompts as servicio_prompts
from apps.metrics.models import Metric
from apps.workouts.models import Exercise, MuscleGroup
from apps.workouts.taxonomy import BodyPart, Equipment

from .gestion_serializers import (
    AlmacenSerializer,
    DocumentoSerializer,
    GeneracionDetalleSerializer,
    GeneracionListaSerializer,
    MetricaDeGestionSerializer,
    ProgramacionSerializer,
    PromptSerializer,
    ProveedorSerializer,
    UsuarioSerializer,
)
from .paginacion import Paginacion

logger = logging.getLogger(__name__)

DIAS_DE_RESUMEN = 7


class VistaDeGestion(viewsets.GenericViewSet):
    permission_classes = [IsAdminUser]
    pagination_class = None


class ProveedorViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin,
    mixins.UpdateModelMixin, mixins.DestroyModelMixin, VistaDeGestion,
):
    queryset = AIProviderConfig.objects.all()
    serializer_class = ProveedorSerializer

    @action(detail=True, methods=["post"])
    def probar(self, request, pk=None):
        config = self.get_object()

        try:
            proveedor = get_provider(config)
            resultado = proveedor.generate_structured(
                system="Responde en español.",
                user="Di que la conexión funciona.",
                schema=ConnectionTest,
            )
        except ProviderError as exc:
            AIGeneration.objects.create(
                kind=GenerationKind.TEST, provider=config.provider,
                model=config.effective_model, status=GenerationStatus.ERROR, error=str(exc),
            )
            return Response(
                {"ok": False, "detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY
            )
        except Exception as exc:  # noqa: BLE001 - probar una clave no puede tumbar el panel
            logger.exception("Error inesperado al probar la configuración %s", config.pk)
            return Response(
                {"ok": False, "detail": f"Error inesperado: {exc}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        AIGeneration.objects.create(
            kind=GenerationKind.TEST, provider=config.provider, model=config.effective_model,
            input_tokens=resultado.input_tokens, output_tokens=resultado.output_tokens,
            latency_ms=resultado.latency_ms,
        )
        return Response({
            "ok": True,
            "latencia_ms": resultado.latency_ms,
            "tokens": resultado.input_tokens + resultado.output_tokens,
            "modelo": config.effective_model,
        })


class PromptViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin,
    mixins.UpdateModelMixin, VistaDeGestion,
):
    queryset = PromptTemplate.objects.all()
    serializer_class = PromptSerializer

    @action(detail=True, methods=["post"])
    def vista_previa(self, request, pk=None):
        prompt = self.get_object()
        contexto = {variable: f"«{variable}»" for variable in prompt.available_variables}
        contexto.update(request.data.get("contexto") or {})

        try:
            system, mensaje = servicio_prompts.render(prompt, contexto)
        except Exception as exc:  # noqa: BLE001 - la plantilla la escribe una persona
            return Response(
                {"detail": f"No se pudo renderizar: {exc}"}, status=status.HTTP_400_BAD_REQUEST
            )

        return Response({
            "system": system,
            "mensaje": mensaje,
            "variables": prompt.available_variables,
            "desconocidas": sorted(
                marca
                for marca in _variables_usadas(prompt)
                if marca not in prompt.available_variables
            ),
        })


def _variables_usadas(prompt: PromptTemplate) -> set[str]:
    import re

    encontradas = set()
    for texto in (prompt.system_prompt, prompt.user_template):
        for marca in re.findall(r"\{\{\s*([a-zA-Z_][\w.]*)", texto or ""):
            encontradas.add(marca.split(".")[0])
    return encontradas


class AlmacenViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin,
    mixins.UpdateModelMixin, mixins.DestroyModelMixin, VistaDeGestion,
):
    serializer_class = AlmacenSerializer

    def get_queryset(self):
        return VectorStore.objects.annotate(
            n_total=Count("documents"),
            n_indexados=Count(
                "documents", filter=Q(documents__status=DocumentStatus.INDEXED)
            ),
            n_fallidos=Count("documents", filter=Q(documents__status=DocumentStatus.FAILED)),
        ).order_by("name")

    @action(detail=True, methods=["post"])
    def crear_en_openai(self, request, pk=None):
        almacen = self.get_object()
        if almacen.is_ready:
            return Response(
                {"detail": "Este almacén ya existe en OpenAI."},
                status=status.HTTP_409_CONFLICT,
            )

        try:
            identificador = rag.create_vector_store(almacen)
        except rag.RAGError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        return Response({"openai_vector_store_id": identificador})


class ProgramacionViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, VistaDeGestion
):
    serializer_class = ProgramacionSerializer

    def get_queryset(self):
        puesto = Case(
            *[When(goal=goal, then=indice) for indice, goal in enumerate(TrainingGoal.values)],
            output_field=IntegerField(),
        )
        return ProgrammingRules.objects.annotate(_puesto=puesto).order_by("_puesto")


class DocumentoViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin,
    mixins.DestroyModelMixin, VistaDeGestion,
):
    serializer_class = DocumentoSerializer

    def get_queryset(self):
        queryset = KnowledgeDocument.objects.select_related("vector_store", "uploaded_by")
        if almacen := self.request.query_params.get("almacen"):
            queryset = queryset.filter(vector_store_id=almacen)
        if estado := self.request.query_params.get("estado"):
            queryset = queryset.filter(status=estado)
        return queryset

    def list(self, request, *args, **kwargs):
        for documento in self.get_queryset().filter(status=DocumentStatus.INDEXING):
            rag.refresh_status(documento)
        return super().list(request, *args, **kwargs)

    def perform_create(self, serializer):
        documento = serializer.save(
            uploaded_by=self.request.user, status=DocumentStatus.PENDING, error=""
        )
        self._empezar(documento)

    @staticmethod
    def _empezar(documento) -> None:
        try:
            rag.start_indexing(documento)
        except rag.RAGError as exc:
            logger.warning("No se pudo empezar a indexar %s: %s", documento.pk, exc)

    def perform_destroy(self, instance):
        rag.delete_document(instance)
        instance.delete()

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except rag.RAGError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

    @action(detail=False)
    def limites(self, request):
        return Response({
            "extensiones": settings.RAG_ALLOWED_EXTENSIONS,
            "max_bytes": settings.RAG_MAX_UPLOAD_BYTES,
        })

    @action(detail=True, methods=["post"])
    def reindexar(self, request, pk=None):
        documento = self.get_object()
        documento.status = DocumentStatus.PENDING
        documento.error = ""
        documento.save(update_fields=["status", "error"])

        try:
            rag.start_indexing(documento)
        except rag.RAGError as exc:
            documento.refresh_from_db()
            return Response(
                {"detail": str(exc), "estado": documento.status},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        documento.refresh_from_db()
        return Response(DocumentoSerializer(documento).data)


class GeneracionViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, VistaDeGestion):
    serializer_class = GeneracionListaSerializer
    pagination_class = Paginacion

    def get_serializer_class(self):
        return (
            GeneracionDetalleSerializer
            if self.action == "retrieve"
            else GeneracionListaSerializer
        )

    def get_queryset(self):
        queryset = AIGeneration.objects.select_related("user")
        parametros = self.request.query_params
        if tipo := parametros.get("tipo"):
            queryset = queryset.filter(kind=tipo)
        if estado := parametros.get("estado"):
            queryset = queryset.filter(status=estado)
        if usuario := parametros.get("usuario"):
            queryset = queryset.filter(user__username__icontains=usuario)
        return queryset

    @action(detail=False, methods=["get"])
    def resumen(self, request):
        desde = timezone.now() - timezone.timedelta(days=DIAS_DE_RESUMEN)
        recientes = AIGeneration.objects.filter(created_at__gte=desde)

        por_tipo = (
            recientes.values("kind")
            .annotate(
                total=Count("id"),
                errores=Count("id", filter=Q(status=GenerationStatus.ERROR)),
            )
            .order_by("kind")
        )
        etiquetas = dict(GenerationKind.choices)

        return Response({
            "dias": DIAS_DE_RESUMEN,
            "total": recientes.count(),
            "errores": recientes.filter(status=GenerationStatus.ERROR).count(),
            "tokens": sum(
                fila["input_tokens"] + fila["output_tokens"]
                for fila in recientes.values("input_tokens", "output_tokens")
            ),
            "por_tipo": [
                {
                    "tipo": fila["kind"],
                    "etiqueta": etiquetas.get(fila["kind"], fila["kind"]),
                    "total": fila["total"],
                    "errores": fila["errores"],
                }
                for fila in por_tipo
            ],
        })


class UsuarioViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin,
                     mixins.UpdateModelMixin, VistaDeGestion):
    serializer_class = UsuarioSerializer

    def get_queryset(self):
        intentos = AccessAttempt.objects.filter(
            username=OuterRef("username"), failures_since_start__gte=_tope_de_intentos()
        )
        queryset = User.objects.annotate(
            entrenamientos=Count("sessions", distinct=True),
            rutinas=Count("routines", distinct=True),
            generaciones=Count("ai_generations", distinct=True),
            bloqueado=Exists(intentos),
        ).order_by("-date_joined")
        if buscado := self.request.query_params.get("buscar"):
            queryset = queryset.filter(
                Q(username__icontains=buscado) | Q(email__icontains=buscado)
            )
        return queryset

    @action(detail=True, methods=["post"])
    def desbloquear(self, request, pk=None):
        usuario = self.get_object()
        borrados, _ = AccessAttempt.objects.filter(username=usuario.username).delete()
        logger.info("Desbloqueada la cuenta %s por %s", usuario.username, request.user.username)
        return Response({"desbloqueado": True, "intentos_borrados": borrados})


def _tope_de_intentos() -> int:
    from django.conf import settings

    return getattr(settings, "AXES_FAILURE_LIMIT", 5)


def _cuentas_bloqueadas() -> int:
    return (
        AccessAttempt.objects.filter(failures_since_start__gte=_tope_de_intentos())
        .values("username")
        .distinct()
        .count()
    )


class MetricaDeGestionViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, VistaDeGestion
):
    serializer_class = MetricaDeGestionSerializer

    def get_queryset(self):
        return Metric.objects.annotate(
            en_paneles=Count(
                "preferences", filter=Q(preferences__is_visible=True), distinct=True
            )
        ).order_by("category", "order")


class CatalogoView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        globales = Exercise.objects.filter(is_global=True)
        etiquetas_zona = dict(BodyPart.choices)
        etiquetas_material = dict(Equipment.choices)

        def reparto(campo, etiquetas):
            filas = globales.values(campo).annotate(n=Count("id")).order_by("-n")
            return [
                {"valor": f[campo], "etiqueta": etiquetas.get(f[campo], f[campo]), "n": f["n"]}
                for f in filas
            ]

        return Response({
            "total": globales.count(),
            "propios": Exercise.objects.filter(is_global=False).count(),
            "con_imagen": globales.exclude(image="").count(),
            "musculos": MuscleGroup.objects.count(),
            "por_zona": reparto("body_part", etiquetas_zona),
            "por_material": reparto("equipment", etiquetas_material),
        })


class ResumenView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        desde = timezone.now() - timezone.timedelta(days=DIAS_DE_RESUMEN)
        activa = AIProviderConfig.objects.filter(is_active=True).first()
        recientes = AIGeneration.objects.filter(created_at__gte=desde)

        return Response({
            "dias": DIAS_DE_RESUMEN,
            "proveedor": (
                {
                    "nombre": activa.get_provider_display(),
                    "modelo": activa.effective_model,
                    "clave_usable": activa.has_usable_key,
                }
                if activa
                else None
            ),
            "generaciones": {
                "total": recientes.count(),
                "errores": recientes.filter(status=GenerationStatus.ERROR).count(),
            },
            "documentos": {
                "total": KnowledgeDocument.objects.count(),
                "fallidos": KnowledgeDocument.objects.filter(
                    status=DocumentStatus.FAILED
                ).count(),
                "pendientes": KnowledgeDocument.objects.filter(
                    status__in=[DocumentStatus.PENDING, DocumentStatus.INDEXING]
                ).count(),
            },
            "usuarios": {
                "total": User.objects.count(),
                "nuevos": User.objects.filter(date_joined__gte=desde).count(),
                "bloqueados": _cuentas_bloqueadas(),
            },
            "metricas": {
                "activas": Metric.objects.filter(is_active=True).count(),
                "total": Metric.objects.count(),
            },
        })
