import logging

import openai
from django.utils import timezone

from .models import AIProviderConfig, DocumentStatus, KnowledgeDocument, Provider, VectorStore

logger = logging.getLogger(__name__)

MAX_FILE_BYTES = 512 * 1024 * 1024
MAX_ATTRIBUTE_KEYS = 16

DEFAULT_CHUNK_TOKENS = 800
DEFAULT_CHUNK_OVERLAP = 400


class RAGError(Exception):
    pass


def get_openai_client() -> openai.OpenAI:
    config = (
        AIProviderConfig.objects.filter(provider=Provider.OPENAI)
        .order_by("-is_active", "-updated_at")
        .first()
    )
    if config is None:
        raise RAGError(
            "El RAG necesita una configuración de OpenAI, aunque el proveedor activo sea otro: "
            "los almacenes vectoriales viven en OpenAI. Créala en /admin/ → Configuraciones de IA."
        )
    if not config.has_usable_key:
        raise RAGError(
            "La API key de OpenAI no se puede descifrar con las claves actuales. "
            "Vuelve a pegarla en /admin/."
        )
    return openai.OpenAI(api_key=config.api_key, timeout=float(config.timeout_seconds))


def create_vector_store(store: VectorStore) -> str:
    if store.openai_vector_store_id:
        return store.openai_vector_store_id

    client = get_openai_client()
    try:
        remote = client.vector_stores.create(name=store.name)
    except openai.APIError as exc:
        raise RAGError(f"No se pudo crear el almacén en OpenAI: {exc}") from exc

    store.openai_vector_store_id = remote.id
    store.save(update_fields=["openai_vector_store_id"])
    logger.info("Almacén vectorial creado en OpenAI: %s", remote.id)
    return remote.id


def delete_vector_store(store: VectorStore) -> None:
    if not store.openai_vector_store_id:
        return
    client = get_openai_client()
    try:
        client.vector_stores.delete(vector_store_id=store.openai_vector_store_id)
    except openai.APIError as exc:
        raise RAGError(f"No se pudo borrar el almacén en OpenAI: {exc}") from exc


def index_document(document: KnowledgeDocument) -> None:
    store = document.vector_store
    if not store.openai_vector_store_id:
        create_vector_store(store)

    _mark(document, DocumentStatus.INDEXING)

    try:
        client = get_openai_client()
        with document.file.open("rb") as handle:
            remote = client.vector_stores.files.upload_and_poll(
                vector_store_id=store.openai_vector_store_id,
                file=(document.file.name.rsplit("/", 1)[-1], handle),
                attributes=_clean_attributes(document),
            )
    except (openai.APIError, RAGError, OSError) as exc:
        _mark(document, DocumentStatus.FAILED, error=str(exc))
        logger.warning("Falló el indexado del documento %s: %s", document.pk, exc)
        raise RAGError(str(exc)) from exc

    if remote.status == "completed":
        document.openai_file_id = remote.id
        _mark(document, DocumentStatus.INDEXED)
        return

    detail = getattr(getattr(remote, "last_error", None), "message", "") or remote.status
    _mark(document, DocumentStatus.FAILED, error=detail)
    raise RAGError(f"OpenAI no pudo indexar el documento: {detail}")


def start_indexing(document: KnowledgeDocument) -> None:
    store = document.vector_store
    if not store.openai_vector_store_id:
        create_vector_store(store)

    _mark(document, DocumentStatus.INDEXING)

    try:
        client = get_openai_client()
        with document.file.open("rb") as handle:
            subido = client.files.create(
                file=(document.file.name.rsplit("/", 1)[-1], handle), purpose="assistants"
            )
        client.vector_stores.files.create(
            store.openai_vector_store_id,
            file_id=subido.id,
            attributes=_clean_attributes(document),
        )
    except (openai.APIError, RAGError, OSError) as exc:
        _mark(document, DocumentStatus.FAILED, error=str(exc))
        logger.warning("Falló la subida del documento %s: %s", document.pk, exc)
        raise RAGError(str(exc)) from exc

    document.openai_file_id = subido.id
    _mark(document, DocumentStatus.INDEXING)


_ESTADOS = {
    "completed": DocumentStatus.INDEXED,
    "failed": DocumentStatus.FAILED,
    "cancelled": DocumentStatus.FAILED,
}


def refresh_status(document: KnowledgeDocument) -> str:
    if document.status != DocumentStatus.INDEXING or not document.openai_file_id:
        return document.status

    try:
        remoto = get_openai_client().vector_stores.files.retrieve(
            document.openai_file_id, vector_store_id=document.vector_store.openai_vector_store_id
        )
    except (openai.APIError, RAGError) as exc:
        logger.info("No se pudo consultar el estado de %s: %s", document.pk, exc)
        return document.status

    nuevo = _ESTADOS.get(remoto.status)
    if nuevo is None:
        return document.status

    detalle = getattr(getattr(remoto, "last_error", None), "message", "") or ""
    _mark(document, nuevo, error=detalle if nuevo == DocumentStatus.FAILED else "")
    return nuevo


def delete_document(document: KnowledgeDocument) -> None:
    if not document.openai_file_id:
        return

    client = get_openai_client()
    store_id = document.vector_store.openai_vector_store_id

    try:
        if store_id:
            client.vector_stores.files.delete(
                document.openai_file_id, vector_store_id=store_id
            )
        client.files.delete(document.openai_file_id)
    except openai.NotFoundError:
        logger.info("El archivo %s ya no existía en OpenAI.", document.openai_file_id)
    except openai.APIError as exc:
        raise RAGError(f"No se pudo borrar el documento en OpenAI: {exc}") from exc


def _clean_attributes(document: KnowledgeDocument) -> dict:
    attributes = {"title": document.title[:256]}
    for key, value in (document.attributes or {}).items():
        if len(attributes) >= MAX_ATTRIBUTE_KEYS:
            break
        attributes[str(key)[:64]] = str(value)[:256]
    return attributes


def _mark(document: KnowledgeDocument, status: str, *, error: str = "") -> None:
    document.status = status
    document.error = error
    document.save(update_fields=["status", "error", "openai_file_id"])


def search(query: str, vector_store_ids: list[str], *, max_results: int = 10) -> list[dict]:
    if not vector_store_ids:
        return []

    client = get_openai_client()
    results = []
    for store_id in vector_store_ids:
        try:
            response = client.vector_stores.search(
                vector_store_id=store_id, query=query, max_num_results=max_results
            )
        except openai.APIError as exc:
            raise RAGError(f"Falló la búsqueda en {store_id}: {exc}") from exc

        for item in response.data:
            results.append({
                "score": item.score,
                "filename": getattr(item, "filename", ""),
                "attributes": getattr(item, "attributes", {}) or {},
                "text": "\n".join(
                    part.text for part in item.content if getattr(part, "type", "") == "text"
                ),
            })

    results.sort(key=lambda item: item["score"], reverse=True)
    return results[:max_results]


def reindex_pending(limit: int = 50) -> int:
    pending = KnowledgeDocument.objects.filter(
        status__in=[DocumentStatus.PENDING, DocumentStatus.FAILED]
    )[:limit]

    done = 0
    for document in pending:
        try:
            index_document(document)
        except RAGError:
            continue
        done += 1
    return done


def store_summary(store: VectorStore) -> dict:
    documents = store.documents.all()
    return {
        "total": documents.count(),
        "indexed": documents.filter(status=DocumentStatus.INDEXED).count(),
        "failed": documents.filter(status=DocumentStatus.FAILED).count(),
        "checked_at": timezone.now(),
    }
