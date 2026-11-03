# La anatomía del mapa corporal

Los 89 trazados de `paths.py` **no son originales**. Vienen de
[`vulovix/body-muscles`](https://github.com/vulovix/body-muscles), publicado bajo **Apache License
2.0**, © 2024 Ivan Vulović.

Se eligió esa y no la alternativa MIT más conocida
([`HichamELBSI/react-native-body-highlighter`](https://github.com/HichamELBSI/react-native-body-highlighter))
porque aquella **no separa los dorsales**: los mete dentro de `upper-back`. En una aplicación de
gimnasio el dorsal es el objetivo de todo tirón del catálogo, y no poder distinguirlo del trapecio
habría vaciado de sentido la mitad del mapa. Esta trae además serrato anterior y glúteo medio, que
son los otros dos que faltaban.

**De openGym no hay nada**, ni aquí ni en ningún otro sitio del proyecto: es AGPL v3 y eso
contaminaría la licencia de todo lo demás.

## Qué pide Apache-2.0 y dónde se cumple

| Obligación | Dónde |
|---|---|
| Conservar la licencia | `LICENSE`, íntegra y sin tocar |
| Conservar la atribución | `NOTICE`, tal como lo publica el proyecto original |
| Dejar constancia de los cambios | esta sección |

**Los cambios.** Se extraen únicamente los campos `path` de
`src/data/muscles.{front,back}.ts` y se convierten a una tupla de Python. **No se usa nada del
renderizador TypeScript** (`src/BodyChart.ts`): el SVG lo arma una plantilla de Django, y el
coloreado, la interacción, la accesibilidad y el mapeo región → músculo son propios y están en
`__init__.py`, `apps/workouts/taxonomy.py` y `templates/workouts/_body_map.html`.

Los trazados en sí no se han modificado: ni un número. El sistema de coordenadas es el del
original — la vista frontal ocupa `x` 0–35 y la dorsal `x` 37–72, sobre un alto de 93.

## Regenerar `paths.py`

Los datos se comitean a propósito: igual que las fuentes, producción no debe necesitar red ni
herramientas para renderizar una pantalla.

```bash
curl -sS "https://raw.githubusercontent.com/vulovix/body-muscles/HEAD/src/data/muscles.front.ts" -o /tmp/muscles.front.ts
curl -sS "https://raw.githubusercontent.com/vulovix/body-muscles/HEAD/src/data/muscles.back.ts"  -o /tmp/muscles.back.ts
# …y también LICENSE y NOTICE, por si cambiaron.

python - <<'PY'
import re, pathlib, textwrap

# Algunas entradas llevan un comentario `//` entre `view:` y `path:`; sin quitarlo se pierden ocho
# regiones (las del pecho, los oblicuos y el serrato) sin que nada avise.
COMENTARIO = re.compile(r"^[ \t]*//.*$", re.M)
ENTRADA = re.compile(
    r'id:\s*"([^"]+)",\s*name:\s*"([^"]+)",\s*view:\s*ViewSide\.(FRONT|BACK),\s*path:\s*"([^"]+)"'
)

regiones = []
for cara in ("front", "back"):
    texto = COMENTARIO.sub("", pathlib.Path(f"/tmp/muscles.{cara}.ts").read_text(encoding="utf-8"))
    declarados = len(re.findall(r'^\s*id:\s*"', texto, re.M))
    encontradas = ENTRADA.findall(texto)
    assert len(encontradas) == declarados, f"{cara}: {len(encontradas)} de {declarados}"
    regiones += encontradas

cuerpo = [
    f'    ("{rid}", "{nombre}", "{vista.lower()}",\n'
    + "\n".join(f'     "{linea}"' for linea in textwrap.wrap(d, 96))
    + "),"
    for rid, nombre, vista, d in regiones
]
# …y se escribe `paths.py` con su cabecera. Ver el historial de git para la forma exacta.
PY
```

Después, `pytest apps/workouts/tests/test_bodymap.py`: hay tests que exigen que **cada** región
tenga destino y que **cada** músculo de `MUSCLE_ES` esté pintado o declarado sin región. Si el
original añade o renombra una región, ahí es donde salta.
