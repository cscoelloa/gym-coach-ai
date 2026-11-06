# Iconos de la aplicación

`icono.svg` es el dibujo maestro: placa casi negra (`#111113`) con la mancuerna de la marca en lima
(`#c3f53c`), el mismo trazo que `Placa` en `frontend/src/ds/Marca.tsx`, y un halo lima suave. Los
PNG se generan a partir de él; no hay script en el repositorio.

Cómo rehacerlos: pintar el SVG en un navegador a cada tamaño y hacer una captura sin fondo (por
ejemplo con Playwright: `page.setContent(svg)` y `page.screenshot({ omitBackground: true })`). El
glifo se centra en (12, 12) de su caja de 24 y se escala con `translate(256 − 12·escala)`.

| Archivo | Tamaño | Variante |
|---|---|---|
| `icon-512.png`, `icon-192.png` | 512, 192 | esquinas redondeadas (`rx` 112 sobre 512), escala 15, trazo 2,4 |
| `icon-maskable-512.png` | 512 | a sangre, sin redondeo, escala 12: el glifo cabe en la zona segura del 80 % |
| `apple-touch-icon.png` | 180 | a sangre y opaco: iOS redondea él solo |
| `favicon.png` | 32 | redondeado, trazo 3,2 para que se lea en pequeño |
| `atajo-entrenar.png`, `atajo-plan.png`, `atajo-peso.png` | 96 | redondeados, escala 11, trazo 2, con los glifos `entrenar`, `plan` y `bascula` de `Icono.tsx` |

iOS guarda el icono de una aplicación ya instalada: para ver uno nuevo hay que quitarla de la
pantalla de inicio y volver a añadirla.
