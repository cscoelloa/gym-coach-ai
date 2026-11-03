# Avisos de terceros

El código de este proyecto se distribuye bajo la **licencia MIT** (ver [`LICENSE`](LICENSE)). Lo que
sigue son las piezas de terceros, cada una con su licencia.

## Catálogo de ejercicios

Los datos del catálogo (nombres, clasificación, instrucciones en 10 idiomas) proceden de
[**hasaneyldrm/exercises-dataset**](https://github.com/hasaneyldrm/exercises-dataset) y se usan bajo
la **licencia MIT**. **No están en este repositorio**: se descargan aparte en
`vendor/exercises-dataset` y se importan con `python manage.py import_catalog`.

## Material visual (imágenes y animaciones)

Las fotos y los GIF de los ejercicios son:

```
© Gym visual — https://gymvisual.com/
```

**No están cubiertos por la licencia MIT del dataset.** El repositorio de origen los redistribuye con
permiso, únicamente a resolución 180×180, y advierte de forma explícita:

> *"Reuse is governed by Gym visual's Terms & Conditions; obtain your own license there before
> reusing the media."*

Consecuencias para este proyecto:

- La atribución se guarda en cada ejercicio (`Exercise.attribution`) y **se muestra junto al material
  visual**. No es decorativa: mantenerla intacta es condición de la licencia.
- Las imágenes se sirven **a 180×180**, sin reescalar ni recortar, que es la resolución bajo la que se
  concedió el permiso.
- Para uso personal, académico o de portafolio no hay fricción. **Antes de publicar esto como
  producto hay que obtener licencia propia en gymvisual.com.**

El material visual está desacoplado en dos campos del modelo (`image` y `animation`), así que
sustituirlo por otro conjunto sería volver a importar, no reescribir la aplicación.

Contexto completo de la decisión: `.docs/01-decisions.md`, ADR-007.

## Mapa corporal

Las siluetas del mapa muscular (`apps/workouts/bodymap/`) proceden de
[**vulovix/body-muscles**](https://github.com/vulovix/body-muscles), © 2024 Ivan Vulović, bajo la
**licencia Apache 2.0**. Su `LICENSE` y su `NOTICE` van junto a los archivos, como pide esa licencia.
