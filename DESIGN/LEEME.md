# DESIGN/

`forja-design-system.html` y `forja-pantallas.html` son **histórico**: el sistema de diseño
«Forja» que trajo el usuario en septiembre de 2026 y que se aplicó con ADR-044. Se conservan
porque ADR-044 los cita y porque explican de dónde salen los nombres de las utilidades.

**Ya no son la referencia.** Desde ADR-061 el sistema es «Aire», y su referencia viva es:

- `assets/app.css`: los tokens, la escala y las utilidades. Es el único sitio donde se edita.
- `/estilos/`, la guía de estilos de la aplicación (requiere sesión). Pinta cada pieza en los dos
  temas, con el conmutador arriba.

Los colores de estos dos archivos son los de Forja y no coinciden con los de la aplicación.
