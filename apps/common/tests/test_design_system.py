import re
from pathlib import Path

from django.conf import settings

CSS = Path(settings.BASE_DIR, "assets", "app.css")
FUENTES = Path(settings.BASE_DIR, "static", "fonts")

CLARO = ':root,\n:root[data-theme="light"]'
OSCURO = ':root[data-theme="dark"]'


def fuente() -> str:
    return CSS.read_text(encoding="utf-8")


def bloque(selector: str) -> str:
    texto = fuente()
    encontrado = re.search(rf"^{re.escape(selector)}\s*\{{", texto, re.M)
    assert encontrado, f"no hay ningún bloque `{selector}` en assets/app.css"
    abre = encontrado.end() - 1
    return texto[abre + 1 : texto.index("}", abre)]


def utilidades() -> list[tuple[str, str]]:
    texto = re.sub(r"/\*.*?\*/", "", fuente(), flags=re.S)
    salida = []

    for cabecera in re.finditer(r"@utility\s+([^\s{]+)\s*\{", texto):
        profundidad, i = 1, cabecera.end()
        while profundidad and i < len(texto):
            profundidad += {"{": 1, "}": -1}.get(texto[i], 0)
            i += 1
        salida.append((cabecera.group(1), texto[cabecera.end() : i - 1]))

    return salida


class TestLosDosTemasDeclaranLoMismo:
    NOMBRE = re.compile(r"^\s*(--[a-z0-9-]+)\s*:", re.M)

    def tokens(self, selector: str) -> set[str]:
        return set(self.NOMBRE.findall(bloque(selector)))

    def test_el_tema_oscuro_define_los_mismos_tokens_que_el_claro(self):
        claro = self.tokens(CLARO)
        oscuro = self.tokens(OSCURO)

        faltan = claro - oscuro
        sobran = oscuro - claro

        assert not faltan, "tokens sin valor en el tema oscuro:\n" + "\n".join(sorted(faltan))
        assert not sobran, "tokens solo del tema oscuro:\n" + "\n".join(sorted(sobran))

    def test_los_dos_temas_declaran_su_color_scheme(self):
        assert "color-scheme: light" in bloque(CLARO)
        assert "color-scheme: dark" in bloque(OSCURO)

    def test_el_claro_es_el_predeterminado(self):
        assert re.search(r"^:root,\s*$", fuente(), re.M), "falta el bloque `:root,`"
        assert "--surface-000: #f2f2f7" in bloque(CLARO), "`:root` no lleva el fondo claro"


class TestNingunaUtilidadEscribeUnColorEnCrudo:
    HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b")

    PERMITIDAS: set[str] = set()

    def test_las_utilidades_usan_tokens(self):
        encontradas = utilidades()

        assert len(encontradas) > 100, f"solo {len(encontradas)} utilidades parseadas"

        culpables = [
            f"{nombre}: {crudo}"
            for nombre, cuerpo in encontradas
            if nombre not in self.PERMITIDAS
            for crudo in self.HEX.findall(cuerpo)
        ]

        assert not culpables, "colores en crudo dentro de @utility:\n" + "\n".join(culpables)


class TestElContrasteSeCalcula:
    PARES = [
        ("ink", "surface-000", 4.5, "texto principal sobre el fondo"),
        ("ink", "surface-100", 4.5, "texto principal sobre una tarjeta"),
        ("ink", "surface-inset", 4.5, "la cifra dentro de un campo numérico"),
        ("ink-muted", "surface-100", 4.5, "texto secundario"),
        ("ink-subtle", "surface-100", 4.5, "etiquetas y texto terciario"),
        ("primary", "surface-000", 4.5, "un enlace sobre el fondo"),
        ("primary", "surface-100", 4.5, "un enlace dentro de una tarjeta"),
        ("primary", "surface-200", 4.5, "un enlace o un icono dentro de una superficie elevada"),
        ("on-primary", "primary-fill", 4.5, "el texto del botón primario"),
        ("on-primary", "primary-hover", 4.5, "el texto del botón primario al pasar por encima"),
        ("primary", "primary-soft", 4.5, "badge de récord, fila activa y el descanso"),
        ("success", "success-soft", 4.5, "badge de completada y la sugerencia de progresión"),
        ("warning", "warning-soft", 4.5, "badge de aviso"),
        ("danger", "danger-soft", 4.5, "badge de bajada y el botón de peligro"),
        ("data", "data-soft", 4.5, "badge informativo"),
        ("danger", "surface-100", 4.5, "el error de un campo"),
        ("ink-subtle", "surface-000", 4.5, "una etiqueta suelta sobre el fondo"),
        ("ink-subtle", "surface-200", 4.5, "el recuento dentro de un chip"),
        ("line-strong", "surface-000", 3.0, "el borde de un control sobre el fondo"),
        ("line-strong", "surface-100", 3.0, "el borde de un control dentro de una tarjeta"),
        ("focus", "surface-000", 3.0, "el anillo de foco sobre el fondo"),
        ("focus", "surface-100", 3.0, "el anillo de foco dentro de una tarjeta"),
        ("data", "surface-100", 4.5, "la serie de una gráfica y el texto de un dato"),
        ("warning", "surface-100", 3.0, "la línea de meta de una gráfica"),
        ("surface-000", "success", 3.0, "la marca de serie hecha sobre su círculo"),
        ("ink", "primary-soft", 4.5, "el título de una cabecera sobre su halo; la fila activa"),
        ("ink-muted", "primary-soft", 4.5, "la entradilla de una cabecera sobre su halo"),
        ("ink", "data-soft", 4.5, "el título de una cabecera de datos"),
        ("ink-muted", "data-soft", 4.5, "la entradilla de una cabecera de datos"),
        ("ink", "surface-200", 4.5, "un chip o un botón secundario"),
        ("ink", "surface-300", 4.5, "la opción elegida de un control segmentado"),
        ("ink-muted", "surface-000", 4.5, "la entradilla bajo el título de una pantalla"),
        ("ink-muted", "surface-200", 4.5, "un estado vacío o un badge neutro"),
        ("success", "surface-100", 4.5, "el texto de una confirmación o un chip hecho"),
        ("primary-edge", "surface-100", 3.0, "el borde de un relleno lima dentro de una tarjeta"),
        ("primary-edge", "surface-000", 3.0, "el borde de un relleno lima sobre el fondo"),
        ("primary", "track", 3.0, "el arco de progreso sobre su pista"),
        ("data", "track", 3.0, "una celda llena del calendario frente a una vacía"),
        ("ink", "glass-solid", 4.5, "una pestaña cuando el cristal es opaco"),
        ("primary", "glass-solid", 4.5, "la pestaña elegida cuando el cristal es opaco"),
        ("surface-100", "danger", 4.5, "el número de avisos sin leer"),
        ("primary-fill", "brand-plate", 3.0, "la mancuerna sobre la placa de la marca"),
    ]

    @staticmethod
    def luminancia(color: str) -> float:
        canales = [int(color.lstrip("#")[i : i + 2], 16) / 255 for i in (0, 2, 4)]
        lineal = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in canales]
        return 0.2126 * lineal[0] + 0.7152 * lineal[1] + 0.0722 * lineal[2]

    @classmethod
    def contraste(cls, frente: str, fondo: str) -> float:
        claro, oscuro = sorted((cls.luminancia(frente), cls.luminancia(fondo)), reverse=True)
        return (claro + 0.05) / (oscuro + 0.05)

    def tokens(self, selector: str) -> dict[str, str]:
        patron = r"^\s*--([a-z0-9-]+)\s*:\s*(#[0-9a-fA-F]{6})\b"
        return dict(re.findall(patron, bloque(selector), re.M))

    def comprobar(self, selector: str, tema: str):
        paleta = self.tokens(selector)
        assert paleta, f"ningún token de color en {tema}"

        fallos = []
        for frente, fondo, umbral, para_que in self.PARES:
            if frente not in paleta or fondo not in paleta:
                fallos.append(f"token ausente en {tema}: {frente} o {fondo}")
                continue
            medido = self.contraste(paleta[frente], paleta[fondo])
            if medido < umbral:
                fallos.append(
                    f"{tema}: {frente} sobre {fondo} da {medido:.2f}:1, "
                    f"por debajo de {umbral} — {para_que}"
                )

        assert not fallos, "\n".join(fallos)

    def test_el_tema_claro(self):
        self.comprobar(CLARO, "claro")

    def test_el_tema_oscuro(self):
        self.comprobar(OSCURO, "oscuro")


class TestLasFuentesEstanDondeDiceElCss:
    def test_cada_font_face_apunta_a_un_woff2_que_existe(self):
        rutas = re.findall(r'url\("\.\./static/fonts/([^"]+)"\)', fuente())

        assert rutas, "ningún @font-face en assets/app.css"

        faltan = [r for r in rutas if not (FUENTES / r).is_file()]
        assert not faltan, "archivos de fuente que no existen:\n" + "\n".join(faltan)

    def test_no_queda_ninguna_fuente_sin_usar(self):
        nombradas = set(re.findall(r'url\("\.\./static/fonts/([^"]+)"\)', fuente()))
        en_disco = {ruta.name for ruta in FUENTES.glob("*.woff2")}
        assert en_disco <= nombradas, "fuentes sin usar: " + ", ".join(sorted(en_disco - nombradas))

    def test_no_se_carga_ninguna_fuente_remota(self):
        texto = fuente()
        assert "fonts.googleapis.com" not in texto
        assert "fonts.gstatic.com" not in texto


def codigo_del_frontend() -> list[Path]:
    raiz = Path(settings.BASE_DIR)
    return [
        archivo
        for archivo in [
            *raiz.glob("frontend/src/**/*.ts"),
            *raiz.glob("frontend/src/**/*.tsx"),
        ]
        if "tests" not in archivo.parts and ".test." not in archivo.name
    ]


class TestNingunComponenteNombraUnTokenQueYaNoExiste:
    RETIRADOS = [
        re.compile(
            r"\b(?:bg|text|border|fill|stroke|ring|outline|from|via|to|accent|divide|decoration|"
            r"placeholder|caret|shadow)-(?:on-)?(?:ember|steel)\b"
        ),
        re.compile(
            r"\b(?:bg|text|border|fill|stroke|ring|outline|from|via|to|divide|decoration|"
            r"shadow)-accent(?:-soft|-strong|-deep)?\b"
        ),
        re.compile(r"var\(--(?:accent|data-strong|bar)\b"),
        re.compile(r"\b(?:hero-calido|card-calida|card-teal|bar-glass)\b"),
    ]

    def test_no_queda_ninguna_clase_con_el_nombre_viejo(self):
        raiz = Path(settings.BASE_DIR)
        archivos = [*raiz.glob("frontend/src/**/*.ts"), *raiz.glob("frontend/src/**/*.tsx")]
        archivos += [*raiz.glob("apps/**/*.py"), CSS]
        assert len(archivos) > 50, "no se ha encontrado el código del frontend"

        culpables = [
            f"{archivo.relative_to(raiz)}: {nombre}"
            for archivo in archivos
            if "tests" not in archivo.parts
            for patron in self.RETIRADOS
            for nombre in patron.findall(archivo.read_text(encoding="utf-8"))
        ]
        assert not culpables, "clases o tokens retirados:\n" + "\n".join(culpables)


class TestElTextoSobreLaAccion:
    def test_quien_escribe_sobre_la_accion_pinta_tambien_su_relleno(self):
        culpables = [
            nombre
            for nombre, cuerpo in utilidades()
            if "on-primary" in cuerpo
            and "primary-fill" not in cuerpo
            and "relleno-accion" not in cuerpo
        ]

        assert not culpables, "texto de la acción sin su relleno lima:\n" + "\n".join(culpables)

    def test_los_componentes_no_escriben_el_texto_de_la_accion_por_su_cuenta(self):
        culpables = [
            str(archivo.name)
            for archivo in codigo_del_frontend()
            if "text-on-primary" in archivo.read_text(encoding="utf-8")
        ]

        assert not culpables, "`text-on-primary` suelto en:\n" + "\n".join(culpables)


class TestElCristal:
    def cuerpo(self, nombre: str) -> str:
        cuerpos = dict(utilidades())
        assert nombre in cuerpos, f"no existe `@utility {nombre}`"
        return cuerpos[nombre]

    def test_la_receta_tiene_safari_y_sus_respaldos(self):
        cristal = self.cuerpo("glass")

        assert "-webkit-backdrop-filter" in cristal, "Safari necesita el prefijo"
        assert "@supports not" in cristal, "sin respaldo donde no hay backdrop-filter"
        assert "prefers-reduced-transparency" in cristal
        assert "prefers-contrast: more" in cristal, "iOS solo respeta «Aumentar contraste»"

    def test_solo_el_cristal_y_el_borde_de_la_barra_desenfocan(self):
        desenfocan = {
            nombre
            for nombre, cuerpo in utilidades()
            if "backdrop-filter" in cuerpo or "backdrop-blur" in cuerpo
        }

        assert desenfocan <= {"glass", "app-bar"}, "desenfoque fuera del cristal: " + ", ".join(
            sorted(desenfocan - {"glass", "app-bar"})
        )


class TestLaLimaNoEsTinta:
    TINTA = re.compile(
        r"(?:\btext-primary-fill\b|\b(?:color|stroke|fill)\s*:\s*var\(--primary-fill\))"
    )
    PERMITIDAS = {"brand-mark"}

    def test_las_utilidades_no_escriben_con_el_relleno_lima(self):
        culpables = [
            nombre
            for nombre, cuerpo in utilidades()
            if nombre not in self.PERMITIDAS and self.TINTA.search(cuerpo)
        ]

        assert not culpables, "la lima de relleno usada como tinta en:\n" + "\n".join(culpables)

    def test_los_componentes_tampoco(self):
        culpables = [
            str(archivo.name)
            for archivo in codigo_del_frontend()
            if self.TINTA.search(archivo.read_text(encoding="utf-8"))
        ]

        assert not culpables, "la lima de relleno usada como tinta en:\n" + "\n".join(culpables)


class TestLasClasesConstruidasExisten:
    @staticmethod
    def union(archivo: str, tipo: str) -> set[str]:
        ruta = Path(settings.BASE_DIR, "frontend", "src", "ds", archivo)
        texto = ruta.read_text(encoding="utf-8")
        declaracion = re.search(rf"export type {tipo} = ([^;]+);", texto)
        assert declaracion, f"no encuentro `{tipo}` en {archivo}"
        return set(re.findall(r'"([a-z]+)"', declaracion.group(1)))

    @staticmethod
    def en_linea(prefijo: str) -> set[str]:
        declarada = re.search(rf'@source inline\("{prefijo}-\{{([^}}]+)\}}"\)', fuente())
        assert declarada, f"no hay `@source inline` para `{prefijo}-*`"
        return set(declarada.group(1).split(","))

    def test_cada_tono_de_badge_se_genera(self):
        assert self.union("Badge.tsx", "TonoDeBadge") <= self.en_linea("badge")

    def test_cada_tamano_de_la_animacion_de_un_ejercicio_se_genera(self):
        assert self.union("MediaDeEjercicio.tsx", "TamanoDeMedia") <= self.en_linea("ex-figure")

    def test_cada_variante_y_tamano_de_boton_se_genera(self):
        construidas = self.union("Button.tsx", "VarianteDeBoton") | (
            self.union("Button.tsx", "TamanoDeBoton") - {"md"}
        )
        assert construidas <= self.en_linea("btn")
