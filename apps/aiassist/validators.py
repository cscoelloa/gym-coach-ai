import zipfile
from pathlib import Path, PureWindowsPath

import filetype
from django.conf import settings
from django.core.exceptions import ValidationError

EXPECTED_MIMES = {
    ".pdf": {"application/pdf"},
    ".docx": {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/zip",
    },
}

TEXT_EXTENSIONS = {".txt", ".md"}

DOCX_MARKER = "word/document.xml"

SNIFF_BYTES = 8192


def safe_filename(name: str) -> str:
    cleaned = PureWindowsPath(name or "").name.replace("\x00", "")
    return cleaned or "documento"


def validate_knowledge_document(uploaded_file) -> None:
    _validate_size(uploaded_file)
    extension = _validate_extension(uploaded_file)
    _validate_contents(uploaded_file, extension)


def _validate_size(uploaded_file) -> None:
    limit = settings.RAG_MAX_UPLOAD_BYTES
    if uploaded_file.size > limit:
        raise ValidationError(
            f"El archivo pesa {uploaded_file.size / 1_048_576:.1f} MB y el máximo son "
            f"{limit / 1_048_576:.0f} MB."
        )
    if uploaded_file.size == 0:
        raise ValidationError("El archivo está vacío.")


def _validate_extension(uploaded_file) -> str:
    extension = Path(safe_filename(uploaded_file.name)).suffix.lower()
    allowed = settings.RAG_ALLOWED_EXTENSIONS
    if extension not in allowed:
        raise ValidationError(
            f"Extensión «{extension or 'sin extensión'}» no admitida. "
            f"Se aceptan: {', '.join(allowed)}."
        )
    return extension


def _validate_contents(uploaded_file, extension: str) -> None:
    head = _read_head(uploaded_file)
    detected = filetype.guess(head)
    detected_mime = detected.mime if detected else None

    if extension in TEXT_EXTENSIONS:
        if detected_mime is not None:
            raise ValidationError(
                f"El archivo dice ser {extension} pero su contenido es {detected_mime}."
            )
        _validate_is_text(head, extension)
        return

    expected = EXPECTED_MIMES[extension]
    if detected_mime not in expected:
        raise ValidationError(
            f"El contenido del archivo no corresponde a un {extension}: se esperaba "
            f"{' o '.join(sorted(expected))} y se encontró "
            f"{detected_mime or 'un formato desconocido'}."
        )

    if extension == ".docx":
        _validate_is_docx(uploaded_file)


def _validate_is_text(head: bytes, extension: str) -> None:
    try:
        head.decode("utf-8")
    except UnicodeDecodeError as exc:
        if exc.reason != "unexpected end of data":
            raise ValidationError(
                f"El archivo {extension} no es texto UTF-8 válido."
            ) from exc


def _validate_is_docx(uploaded_file) -> None:
    uploaded_file.seek(0)
    try:
        with zipfile.ZipFile(uploaded_file) as archive:
            names = archive.namelist()
    except zipfile.BadZipFile as exc:
        raise ValidationError("El archivo .docx está corrupto.") from exc
    finally:
        uploaded_file.seek(0)

    if DOCX_MARKER not in names:
        raise ValidationError(
            "El archivo es un zip pero no un documento de Word: no contiene "
            f"«{DOCX_MARKER}»."
        )


def _read_head(uploaded_file) -> bytes:
    uploaded_file.seek(0)
    head = uploaded_file.read(SNIFF_BYTES)
    uploaded_file.seek(0)
    return head
