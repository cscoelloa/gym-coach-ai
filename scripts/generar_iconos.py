from pathlib import Path

from PIL import Image, ImageColor, ImageDraw

RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / "static" / "pwa"

PRIMARIO = "#1f5fe6"
PRIMARIO_HONDO = "#1a4fcc"
TINTA = "#ffffff"

ZONA_SEGURA = 0.8
SUPERMUESTREO = 4

DIBUJOS = {
    "mancuerna": [
        ("linea", (6.5, 6.5, 6.5, 17.5)),
        ("linea", (17.5, 6.5, 17.5, 17.5)),
        ("linea", (3, 9.5, 3, 14.5)),
        ("linea", (21, 9.5, 21, 14.5)),
        ("linea", (6.5, 12, 17.5, 12)),
    ],
    "calendario": [
        ("caja", (3, 4, 21, 21, 2)),
        ("linea", (3, 9, 21, 9)),
        ("linea", (8, 2, 8, 6)),
        ("linea", (16, 2, 16, 6)),
    ],
    "bascula": [
        ("caja", (3.5, 3.5, 20.5, 20.5, 4)),
        ("arco", (7.5, 7, 16.5, 16, 200, 340)),
        ("linea", (12, 11.5, 14, 9)),
    ],
}


def degradado(lado: int) -> Image.Image:
    claro, hondo = ImageColor.getrgb(PRIMARIO), ImageColor.getrgb(PRIMARIO_HONDO)
    medio = tuple((a + b) // 2 for a, b in zip(claro, hondo, strict=True))
    origen = Image.new("RGB", (2, 2))
    origen.putdata([claro, medio, medio, hondo])
    return origen.resize((lado, lado), Image.Resampling.BILINEAR)


def trazar(
    pincel: ImageDraw.ImageDraw, dibujo: str, x0: float, y0: float, escala: float, grosor: float
):
    ancho = max(1, round(grosor * escala))
    radio = ancho / 2

    def punto(x: float, y: float) -> tuple[float, float]:
        return x0 + x * escala, y0 + y * escala

    def remate(x: float, y: float):
        cx, cy = punto(x, y)
        pincel.ellipse([cx - radio, cy - radio, cx + radio, cy + radio], fill=TINTA)

    for tipo, datos in DIBUJOS[dibujo]:
        if tipo == "linea":
            ax, ay, bx, by = datos
            pincel.line([punto(ax, ay), punto(bx, by)], fill=TINTA, width=ancho)
            remate(ax, ay)
            remate(bx, by)
        elif tipo == "caja":
            ax, ay, bx, by, r = datos
            pincel.rounded_rectangle(
                [*punto(ax, ay), *punto(bx, by)], radius=r * escala, outline=TINTA, width=ancho
            )
        elif tipo == "arco":
            ax, ay, bx, by, desde, hasta = datos
            pincel.arc([*punto(ax, ay), *punto(bx, by)], desde, hasta, fill=TINTA, width=ancho)


def icono(
    lado: int,
    dibujo: str = "mancuerna",
    *,
    a_sangre: bool = False,
    proporcion: float = 0.62,
    grosor: float = 2.4,
) -> Image.Image:
    grande = lado * SUPERMUESTREO
    lienzo = Image.new("RGBA", (grande, grande), (0, 0, 0, 0))

    relleno = degradado(grande)
    if a_sangre:
        lienzo.paste(relleno, (0, 0))
    else:
        mascara = Image.new("L", (grande, grande), 0)
        ImageDraw.Draw(mascara).rounded_rectangle(
            [0, 0, grande - 1, grande - 1], radius=round(grande * 0.275), fill=255
        )
        lienzo.paste(relleno, (0, 0), mascara)

    tamano = grande * proporcion
    escala = tamano / 24
    inicio = (grande - tamano) / 2
    trazar(ImageDraw.Draw(lienzo), dibujo, inicio, inicio, escala, grosor)

    return lienzo.resize((lado, lado), Image.Resampling.LANCZOS)


def main() -> None:
    SALIDA.mkdir(parents=True, exist_ok=True)

    archivos = {
        "icon-192.png": icono(192),
        "icon-512.png": icono(512),
        "icon-maskable-512.png": icono(512, a_sangre=True, proporcion=ZONA_SEGURA * 0.62),
        "apple-touch-icon.png": icono(180, a_sangre=True, proporcion=0.56).convert("RGB"),
        "favicon.png": icono(32, proporcion=0.7, grosor=2.8),
        "atajo-entrenar.png": icono(96, "mancuerna", proporcion=0.58, grosor=2.2),
        "atajo-plan.png": icono(96, "calendario", proporcion=0.54, grosor=2.2),
        "atajo-peso.png": icono(96, "bascula", proporcion=0.56, grosor=2.2),
    }
    for nombre, imagen in archivos.items():
        imagen.save(SALIDA / nombre, "PNG", optimize=True)
        print(f"  {nombre}  {imagen.size[0]}×{imagen.size[1]}")

    print(f"Iconos en {SALIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
