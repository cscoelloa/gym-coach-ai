import io
import zipfile

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.aiassist.validators import safe_filename, validate_knowledge_document

PDF = b"%PDF-1.4\n" + b"contenido de un pdf" * 20
EXE = b"MZ\x90\x00" + b"\x00" * 200
TEXTO = b"Principios de hipertrofia.\nVolumen, intensidad y frecuencia.\n"


def subir(nombre: str, contenido: bytes) -> SimpleUploadedFile:
    return SimpleUploadedFile(nombre, contenido)


def docx_valido() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("word/document.xml", "<w:document/>")
        archive.writestr("[Content_Types].xml", "<Types/>")
    return buffer.getvalue()


def zip_cualquiera() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("notas.txt", "esto no es un documento de Word")
    return buffer.getvalue()


class TestNombreDeArchivo:
    @pytest.mark.parametrize(
        "entrada,esperado",
        [
            ("../../../settings.py", "settings.py"),
            ("..\\..\\.env", ".env"),
            ("C:\\Windows\\system32\\drivers\\etc\\hosts", "hosts"),
            ("/etc/passwd", "passwd"),
            ("carpeta/archivo.pdf", "archivo.pdf"),
            ("libro.pdf", "libro.pdf"),
        ],
    )
    def test_descarta_los_componentes_de_ruta(self, entrada, esperado):
        assert safe_filename(entrada) == esperado

    def test_quita_bytes_nulos(self):
        assert "\x00" not in safe_filename("libro\x00.pdf")

    def test_un_nombre_vacio_no_deja_el_archivo_sin_nombre(self):
        assert safe_filename("") == "documento"


class TestFormatosAdmitidos:
    def test_acepta_un_pdf_de_verdad(self):
        validate_knowledge_document(subir("libro.pdf", PDF))

    def test_acepta_texto_plano(self):
        validate_knowledge_document(subir("apuntes.txt", TEXTO))
        validate_knowledge_document(subir("apuntes.md", TEXTO))

    def test_acepta_un_docx_de_verdad(self):
        validate_knowledge_document(subir("guia.docx", docx_valido()))

    def test_rechaza_extensiones_no_admitidas(self):
        with pytest.raises(ValidationError, match="no admitida"):
            validate_knowledge_document(subir("hoja.xlsx", PDF))


class TestContenidoReal:
    def test_un_exe_renombrado_a_pdf_no_cuela(self):
        with pytest.raises(ValidationError, match="no corresponde"):
            validate_knowledge_document(subir("libro.pdf", EXE))

    def test_un_exe_renombrado_a_txt_tampoco(self):
        with pytest.raises(ValidationError, match="su contenido es"):
            validate_knowledge_document(subir("apuntes.txt", EXE))

    def test_un_zip_cualquiera_renombrado_a_docx_no_cuela(self):
        with pytest.raises(ValidationError, match="no un documento de Word"):
            validate_knowledge_document(subir("guia.docx", zip_cualquiera()))

    def test_un_pdf_renombrado_a_docx_no_cuela(self):
        with pytest.raises(ValidationError, match="no corresponde"):
            validate_knowledge_document(subir("guia.docx", PDF))

    def test_un_txt_que_no_es_utf8_se_rechaza(self):
        contenido = b"\xff\xfe\x00texto en otra codificacion" * 20
        with pytest.raises(ValidationError):
            validate_knowledge_document(subir("apuntes.txt", contenido))

    def test_un_caracter_multibyte_cortado_no_es_un_error(self):
        contenido = ("á" * 6000).encode()

        validate_knowledge_document(subir("apuntes.txt", contenido))


class TestTamano:
    def test_rechaza_lo_que_pase_del_limite(self, settings):
        settings.RAG_MAX_UPLOAD_BYTES = 1024

        with pytest.raises(ValidationError, match="máximo"):
            validate_knowledge_document(subir("libro.pdf", PDF + b"0" * 2048))

    def test_rechaza_un_archivo_vacio(self):
        with pytest.raises(ValidationError, match="vacío"):
            validate_knowledge_document(subir("libro.pdf", b""))
