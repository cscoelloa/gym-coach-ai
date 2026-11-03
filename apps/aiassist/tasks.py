import logging

from celery import shared_task

from .models import DocumentStatus, KnowledgeDocument
from .rag import RAGError, index_document

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(RAGError,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def index_knowledge_document(self, document_id: int) -> str:
    try:
        document = KnowledgeDocument.objects.get(pk=document_id)
    except KnowledgeDocument.DoesNotExist:
        logger.info("El documento %s ya no existe; no se indexa.", document_id)
        return "missing"

    index_document(document)
    return DocumentStatus.INDEXED


@shared_task
def analyze_new_bodyweight(entry_id: int) -> str:
    from apps.bodyweight.models import BodyWeightEntry

    from .services.weight_analyzer import analyze_weight, notify_weight, should_analyze

    try:
        entry = BodyWeightEntry.objects.select_related("user").get(pk=entry_id)
    except BodyWeightEntry.DoesNotExist:
        return "missing"

    procede, motivo = should_analyze(entry.user)
    if not procede:
        logger.info("No se analiza el peso de %s: %s", entry.user, motivo)
        return "skipped"

    try:
        generation = analyze_weight(entry.user)
    except Exception as exc:  # noqa: BLE001 - una tarea de fondo no debe tumbar nada
        logger.warning("Falló el análisis de peso de %s: %s", entry.user, exc)
        return "failed"

    notify_weight(generation)
    return "analyzed"


@shared_task
def run_progress_analysis(user_id: int) -> str:
    from apps.accounts.models import User

    from .services.progress_analyzer import NotEnoughData, analyze_progress, notify_progress

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return "missing"

    try:
        generation = analyze_progress(user)
    except NotEnoughData:
        return "not-enough-data"
    except Exception as exc:  # noqa: BLE001
        logger.warning("Falló el análisis de progreso de %s: %s", user, exc)
        return "failed"

    notify_progress(generation)
    return "analyzed"


@shared_task
def run_weekly_progress_analysis() -> str:
    from django.db.models import Count

    from apps.accounts.models import User

    from .services.progress_analyzer import MIN_SESSIONS

    candidatos = (
        User.objects.filter(is_active=True)
        .annotate(total=Count("sessions"))
        .filter(total__gte=MIN_SESSIONS)
        .values_list("pk", flat=True)
    )

    for user_id in candidatos:
        run_progress_analysis.delay(user_id)

    return f"encolados:{len(candidatos)}"
