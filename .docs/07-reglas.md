# Reglas del proyecto

Lo que se cumple en todo cambio. Cada regla tiene su razón; no son ceremonia. Las decisiones que
las originaron están en [`01-decisions.md`](01-decisions.md).

## El frontend es una SPA en React sobre `/api/`

Django sirve **una sola plantilla** —`templates/spa.html`, la cáscara— y la API. Todo lo que se ve
lo pinta React (ADR-046, ADR-047).

- Qué URL existen está en `SPA_URLS` / `SPA_URLS_PUBLICAS` en `config/urls.py`.
- **El frontend va por módulos** (ADR-069): `frontend/src/modulos/<funcionalidad>/`, cada uno con
  su `api.ts`, sus pantallas, sus piezas y sus tests. `ds/` (diseño), `lib/` (infraestructura) y
  `api/` (lo transversal) son compartidos y **nunca importan de un módulo**. Entre módulos solo se
  importa por su `index.ts` o su `api.ts`. Una pantalla solo compone: cada zona es un componente.
- **Añadir una pantalla toca tres sitios:** el `index.ts` de su módulo, `config/urls.py` y
  `frontend/src/rutas.ts`. Los comparan dos tests, uno en Python y otro en vitest.
- **El sistema de diseño es un solo archivo**, `assets/app.css`, que compila Vite dentro del
  bundle. Los componentes de `frontend/src/ds/` consumen sus clases. Nada de CSS-in-JS, ni CSS
  comiteado, ni binario standalone.
- **La validación y la aritmética se quedan en Python.** El cliente no repite las reglas de
  contraseña ni recalcula métricas: las pide y las pinta.

## Convenciones

- **El código va sin comentarios ni docstrings** (ADR-073). El porqué de cada decisión vive en
  `01-decisions.md` y en esta documentación.
  - Solo se escriben los que hacen algo: `# noqa`, `# nosec`, `# type: ignore`,
    `// @ts-expect-error`, `/// <reference>`, los shebang y la marca `/*__CONFIG__*/` de
    `apps/common/sw.js`, que lee `apps/common/pwa.py`.
  - Un comentario que el código lee necesita un test que falle si desaparece.
- **Las apps viven bajo `apps/`.** Nada de apps en la raíz.
- **Ningún SDK de IA se instancia fuera de `apps/aiassist/providers/`.** Los servicios piden un
  proveedor a `factory.get_provider()` y hablan con la interfaz `LLMProvider`, nunca con
  `anthropic`, `openai` o `google-genai` directamente. Así, añadir un proveedor es un archivo y no
  una búsqueda por todo el código.
- **La aritmética de progreso vive en Python, no en los prompts ni en el cliente.**
  - Está en `apps/metrics/`: `summary.py` para Inicio y Progreso, `catalog/` para las métricas y
    `loads.py` para el tonelaje.
  - Y en `apps/workouts/`: `focus.py` para entrenar e `history.py` para la última vez y la
    progresión.
  - El LLM recibe métricas ya calculadas e interpreta; no se le pide que sume volúmenes ni que
    calcule un 1RM. Un número mal sumado por un modelo no se detecta en revisión; uno mal sumado en
    Python lo pilla un test.
  - **Un endpoint de pantalla tampoco calcula**: llama a esas funciones y serializa.
- **Los ejercicios vienen del catálogo importado.** La IA **elige** de una lista de candidatos por
  `external_id`; no inventa ejercicios.
- **Con el modelo por defecto de Anthropic no se pasan `temperature`, `top_p` ni `budget_tokens`**:
  el proveedor devuelve 400 (ver `03-ai-config.md`).

## Reglas de seguridad no negociables

El detalle y el modelo de amenazas están en [`06-security.md`](06-security.md).

- **Nunca `|safe` ni `mark_safe` sobre texto generado por la IA o escrito por un usuario.** Django
  autoescapa por defecto y ahí se queda. Si hace falta markdown, pasa por `bleach` con una lista
  de lo permitido. **En React, la misma regla: nunca `dangerouslySetInnerHTML`.** El texto de la IA
  y el del usuario se renderizan como texto, y punto.
- **Ningún queryset sin filtrar por `request.user`.** Nada de `get_object_or_404(Routine, pk=pk)` a
  secas: un IDOR aquí expone el historial médico-deportivo de otra persona.
  - Ante un recurso ajeno se devuelve **404, no 403**: un 403 confirma que el recurso existe.
  - Cada endpoint nuevo parte de `OwnedModelViewSet` (`apps/api/views.py`) y lleva su test de
    aislamiento.
- **La sesión de la web va en una cookie `HttpOnly`, nunca un token en `localStorage`** (ADR-046).
  Un script inyectado lee `localStorage`; la cookie no.
  - Todo lo que modifica datos manda `X-CSRFToken`.
  - Entrar y registrarse, donde todavía no hay sesión que autenticar, llevan `csrf_protect`
    explícito, porque `APIView` viene envuelta en `csrf_exempt`.
- **El service worker nunca guarda `/api/`, y la caché de TanStack no se persiste** (ADR-063). La
  aplicación instalada abre sin red porque guarda la cáscara y el build, y nada más: ni una
  respuesta con el peso o el historial de alguien se queda en un teléfono que puede ser compartido.
  Por lo mismo, `templates/spa.html` no lleva ningún dato del usuario.
- **Las API keys no se loguean, no se renderizan y no entran en un prompt.** Están cifradas con
  MultiFernet en la base de datos y la gestión las muestra enmascaradas.
- **Toda entrada de usuario entra al prompt delimitada como dato** (`<user_notes>…</user_notes>`),
  nunca concatenada al system prompt. La delimitación es la primera barrera. La defensa real
  contra la prompt injection es que la salida está restringida por esquema y que el LLM no tiene
  herramientas con efectos secundarios.
- **Peso, altura, sexo, fecha de nacimiento y lesiones son datos de salud.** No aparecen en logs ni
  en mensajes de error, y a la IA se le manda la edad calculada, no la fecha de nacimiento.

## Al cambiar algo estructural

Se añade una entrada en [`01-decisions.md`](01-decisions.md) **sin reescribir las antiguas**: si una
decisión cambia, la vieja se marca como sustituida y la nueva explica por qué.
