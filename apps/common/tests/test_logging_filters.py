import logging

from config.logging_filters import REDACTED, SensitiveDataFilter, redact

CLAVE_OPENAI = "sk-proj-AbCdEfGhIjKlMnOpQrStUvWxYz0123456789"
CLAVE_ANTHROPIC = "sk-ant-api03-AbCdEfGhIjKlMnOpQrStUvWxYz0123456789"
CLAVE_GOOGLE = "AIzaSyAbCdEfGhIjKlMnOpQrStUvWxYz0123456"


def registro(mensaje, *args, exc_info=None):
    return logging.LogRecord(
        name="prueba", level=logging.ERROR, pathname=__file__, lineno=1,
        msg=mensaje, args=args, exc_info=exc_info,
    )


class TestQueSeRedacta:
    def test_las_tres_formas_de_clave(self):
        for clave in (CLAVE_OPENAI, CLAVE_ANTHROPIC, CLAVE_GOOGLE):
            limpio = redact(f"fallo al conectar con {clave}")

            assert clave not in limpio
            assert REDACTED in limpio

    def test_el_mensaje(self):
        record = registro(f"no se pudo usar {CLAVE_OPENAI}")

        SensitiveDataFilter().filter(record)

        assert CLAVE_OPENAI not in record.msg

    def test_los_argumentos(self):
        record = registro("fallo con %s", CLAVE_OPENAI)

        SensitiveDataFilter().filter(record)

        assert CLAVE_OPENAI not in str(record.args)

    def test_los_argumentos_con_nombre(self):
        record = registro("fallo con %(clave)s", {"clave": CLAVE_ANTHROPIC})

        SensitiveDataFilter().filter(record)

        assert CLAVE_ANTHROPIC not in str(record.args)


class TestElTraceback:
    def _con_excepcion(self):
        try:
            raise ValueError(f"401 unauthorized para {CLAVE_OPENAI}")
        except ValueError:
            import sys

            return registro("error inesperado al probar la configuración", exc_info=sys.exc_info())

    def test_la_clave_no_sobrevive_en_el_rastro(self):
        record = self._con_excepcion()

        SensitiveDataFilter().filter(record)

        assert CLAVE_OPENAI not in (record.exc_text or "")
        assert REDACTED in record.exc_text

    def test_lo_que_sí_hace_falta_para_depurar_se_queda(self):
        record = self._con_excepcion()

        SensitiveDataFilter().filter(record)

        assert "ValueError" in record.exc_text
        assert "401 unauthorized" in record.exc_text

    def test_el_formateador_no_lo_vuelve_a_escribir_sin_redactar(self):
        record = self._con_excepcion()
        SensitiveDataFilter().filter(record)

        salida = logging.Formatter("%(message)s").format(record)

        assert CLAVE_OPENAI not in salida

    def test_sin_excepcion_no_inventa_nada(self):
        record = registro("todo bien")

        SensitiveDataFilter().filter(record)

        assert record.exc_text is None
