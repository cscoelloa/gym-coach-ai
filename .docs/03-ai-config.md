# Configuración de la IA

Todo lo de este documento se administra desde `/admin/` y **solo para `is_staff`**. Nada de esto se
expone por la API ni se renderiza a usuarios normales.

## `AIProviderConfig`

Una sola fila activa a la vez (validado en `clean()`).

| Campo | Notas |
|---|---|
| `provider` | `anthropic` · `openai` · `google` |
| `model` | id del modelo; ver la tabla de abajo |
| `api_key` | `EncryptedTextField` sobre MultiFernet. En el admin se muestra enmascarada |
| `max_tokens` | tope de salida. **Lo fija el admin, nunca el usuario** — es control de gasto |
| `effort` | solo aplica a los proveedores que lo soportan |
| `timeout_seconds` | |
| `is_active` | |

Acción del admin **"Probar configuración"**: hace una llamada real mínima y reporta éxito o el error
concreto. Es la forma de validar una key sin esperar a que falle una generación.

`base_url` **no es configurable**. Dejar que el admin apunte los SDK a un host arbitrario abriría un
SSRF; los proveedores tienen endpoints fijos.

## Particularidades por proveedor

| Proveedor | Modelo por defecto | Salida estructurada | RAG |
|---|---|---|---|
| Anthropic | `claude-opus-5` | `client.messages.parse(output_format=<Pydantic>)` | no |
| OpenAI | — | Responses API + structured outputs | **sí** (`file_search`) |
| Google | — | `response_mime_type="application/json"` + `response_schema` | no |

**Anthropic, detalles que hacen fallar si se ignoran:**

- `thinking={"type": "adaptive"}`.
- **No pasar `temperature`, `top_p` ni `budget_tokens`** — devuelven 400 en este modelo.
- `max_tokens` en torno a 16000 si no se usa streaming.
- Comprobar `stop_reason == "refusal"` **antes** de leer `content`: en una negativa el contenido
  viene vacío y el código que indexa `content[0]` revienta.

## `PromptTemplate`

Lo que el admin edita para cambiar el comportamiento de la IA sin tocar código.

| Campo | Notas |
|---|---|
| `key` | `routine_generation` · `progress_analysis` · `weight_analysis` |
| `system_prompt` | instrucciones de sistema |
| `user_template` | plantilla de Django; las variables disponibles están documentadas en el `help_text` |
| `version`, `is_active` | permite volver atrás si una edición empeora los resultados |

**Regla al editar prompts:** la entrada del usuario ya llega envuelta en `<user_notes>` desde el
servicio. No quitar esa envoltura ni la instrucción que declara ese bloque como datos y no como
instrucciones.

## RAG

Solo funciona cuando el proveedor activo es **OpenAI** (ver ADR-005). Con Anthropic o Google las
rutinas se generan sin el contexto de los libros: no es un fallo, es la decisión tomada.

> ⚠️ **El RAG necesita una API key de OpenAI aunque el proveedor activo sea Claude o Gemini.**
> La configuración activa decide quién *genera*; los almacenes vectoriales viven siempre en OpenAI.
> `rag.get_openai_client()` busca una `AIProviderConfig` de OpenAI **esté activa o no**. Si no hay
> ninguna, lo dice con un mensaje explícito en vez de fallar de forma opaca.

### Todo esto se hace desde `/gestion/` → IA → Documentos (ADR-055)

Crear el almacén, crearlo en OpenAI, subir documentos, reintentar los fallidos y borrarlos. El
`/admin/` sigue estando como red de seguridad, pero ya no hace falta pasar por él.

Tres cosas que conviene saber antes de tocarlo:

- **Las extensiones y el tope los sirve el servidor** (`GET /api/gestion/documentos/limites/`),
  leídos de `RAG_ALLOWED_EXTENSIONS` y `RAG_MAX_UPLOAD_BYTES`. Si se admite un formato nuevo, se
  cambia ahí y el formulario se entera solo.
- **Subir no espera al troceado.** La petición sube el archivo, lo asocia al almacén y devuelve
  (`rag.start_indexing`); el documento queda en `indexing`. El estado final lo trae
  `rag.refresh_status()`, que el listado consulta solo de los que están a medias, y el panel
  repregunta cada cuatro segundos mientras quede alguno. **El panel no necesita Celery**: la tarea
  `index_knowledge_document` —que sí espera, con `upload_and_poll`— es la del admin.

  No es un detalle de estilo. Con `upload_and_poll` dentro de la petición, subir un PDF de verdad
  dejaba el navegador esperando minutos hasta rendirse con un *broken pipe* (ADR-055): el
  documento acababa indexado, pero quien lo subió solo veía una conexión rota.
- **Borrar borra también en OpenAI.** Si solo se borrara la fila local, el libro seguiría
  contestando a las búsquedas desde el otro lado.

### `VectorStore`
Se crea en OpenAI con **"Crear en OpenAI"**, desde el panel o desde el admin: llama a la API y
guarda el `openai_vector_store_id` devuelto. Es idempotente: si ya existe, no lo vuelve a crear.
**Hasta que existe allí no admite documentos**, porque no hay dónde indexarlos.

### `KnowledgeDocument`
Ciclo de vida:

```
pending ──► indexing ──► indexed
                   └───► failed (con el error guardado, re-indexable a mano)
```

La tarea `index_knowledge_document` sube el archivo, lo adjunta al store y sondea hasta `completed`
o `failed`.

Límites de la API que hay que respetar:

- 512 MB y 5M tokens por archivo (el proyecto pone un tope propio más bajo, 50 MB).
- Formatos: `.pdf`, `.docx`, `.txt`, `.md`.
- Troceado por defecto: 800 tokens con 400 de solape (configurable entre 100 y 4096, con solape no
  mayor que la mitad del trozo).
- `attributes` (máx. 16 claves) permite filtrar por metadatos en la búsqueda.

La tarea de Celery reintenta con espera creciente hasta tres veces: los fallos de indexado suelen ser
temporales (límite de tasa, servicio ocupado). Agotados los reintentos, el documento queda en
`failed` **con el motivo guardado**, visible en el admin sin tener que ir a mirar a OpenAI, y con
una acción «Volver a indexar».

### Validación de subida

Solo `is_staff`, tamaño acotado, nombre saneado contra *path traversal* y **contenido real
comprobado**. Este último punto tiene un matiz que conviene conocer, porque el enfoque ingenuo de
«los magic bytes deben coincidir con la extensión» rechaza archivos legítimos:

| Extensión | Qué detectan los magic bytes | Cómo se valida |
|---|---|---|
| `.pdf` | `application/pdf` | Coincidencia directa |
| `.docx` | OOXML o `application/zip` — un .docx **es** un zip | Debe contener `word/document.xml` |
| `.txt`, `.md` | **Nada**: el texto plano no tiene firma | Que no sea ningún binario y decodifique en UTF-8 |

Un `.exe` renombrado se rechaza en los tres casos, y un zip cualquiera renombrado a `.docx`
también: sin mirar dentro, pasaría el filtro y se enviaría a indexar basura.

## Esquemas de salida

En `apps/aiassist/schemas.py` (Pydantic). Cada adaptador los traduce a su mecanismo nativo de salida
estructurada; **el parseo nunca es "extraer JSON de un texto libre"**.

| Esquema | Devuelve |
|---|---|
| `RoutinePlan` | 7 días, cada uno con sus ejercicios por `external_id`, series, reps, RPE y descanso |
| `ProgressAnalysis` | ejercicios estancados, patrones, recomendaciones, cambios propuestos |
| `WeightAnalysis` | tendencia, ritmo kg/semana, si va acorde al objetivo, mensaje y recomendación |

`RoutinePlan` exige que cada `external_id` pertenezca a la lista de candidatos de esa petición. Uno
fuera de lista se rechaza y se reintenta una vez con el error como feedback. Esto es a la vez calidad
de datos y defensa contra prompt injection (ADR-008 y ADR-010).

## La programación del entrenamiento (ADR-056)

Series, repeticiones, descansos y volumen mínimo por músculo **no los decide el modelo**: los
decide una fila de `ProgrammingRules` por objetivo de entrenamiento —hipertrofia, fuerza,
resistencia—, que se ajusta en `/gestion/` → IA → **Programación**. El prompt enseña esos mismos
números (`{{ programacion }}`) y la validación los exige; si el plan no cumple, se reintenta con
el número concreto.

| | Hipertrofia | Fuerza | Resistencia |
|---|---|---|---|
| Series por ejercicio | 3-4 | 3-6 | 2-4 |
| Repeticiones (banda) | 6-20 | 3-8 | 12-30 |
| Descanso compuesto / aislamiento | 120 / 90 s | 180 / 120 s | 60 / 45 s |
| Series por músculo y día | 6 | 4 | 4 |

Tres cosas que conviene saber antes de tocarlo:

- **El objetivo de entrenamiento no es el del perfil.** `accounts.Goal` es Volumen / Definición /
  Mantenimiento, que es peso corporal: se puede entrenar para hipertrofia estando en déficit. El
  de entreno se elige en el formulario de generar, en cada generación.
- **Las repeticiones son una banda, no un número por tipo de ejercicio.** Dentro de 6-20 caben
  8-12 en un press y 12-20 en un curl. Lo que sí distingue compuesto de aislamiento es el
  descanso, y ahí la diferencia es real. Compuesto = dos o más músculos secundarios.
- **El mínimo por músculo se acota a lo posible**: `(ejercicios // músculos) × series_min`. Subir
  mucho los mínimos desde el panel puede agotar los tres intentos de la generación.

**Y lo que el RAG no hace.** `file_search` puede mejorar qué ejercicios elige y cómo justifica el
plan, pero es una herramienta que el modelo decide usar y no rellena el campo `sets`. Los números
salen de aquí.

**Lo que sí cuesta.** Adjuntar `file_search` multiplica por cinco lo que OpenAI reserva del límite
por minuto (TPM): con el mismo prompt de 4.000 tokens, 3.632 reservados sin la herramienta y
18.501 con ella. Por eso los libros van **solo en el primer intento** de cada generación; los
reintentos corrigen números y no necesitan volver a buscar. Si aparecen `429 Too Many Requests`,
el camino es espaciar las generaciones o subir de nivel en OpenAI — **no** bajar `max_tokens`, que
está medido y no influye en la reserva.

## El reparto semanal (ADR-054)

Lo que la persona elige día a día en `/ia/generar/` —músculos, énfasis y número exacto de
ejercicios— no es una sugerencia: entra en el prompt como la variable `{{ reparto }}` y **se
comprueba contra el plan devuelto**. Si el lunes pide tríceps y no hay ningún ejercicio cuyo
músculo objetivo sea el tríceps, la respuesta se rechaza y se reintenta con ese fallo concreto.

Se valida en dos momentos y por motivos distintos:

| Cuándo | Qué se mira | Si falla |
|---|---|---|
| Antes de llamar al modelo (`services/split.py`) | Que el reparto se pueda entrenar: días, músculos que existen **y se pueden hacer con su material**, tope de ejercicios, y **48 h** para el mismo músculo | 400 con código `reparto` o `descanso`. No gasta cupo ni dinero |
| Con la respuesta (`validate_plan`) | Días exactos, recuento exacto, un ejercicio **primario** por músculo pedido, el énfasis por encima del resto, sin repetidos y sin repetir músculo en días seguidos | Reintento con la corrección apuntada, hasta `MAX_ATTEMPTS` |

La regla de recuperación es **48 h para el mismo músculo**, con excepción de abdominales,
oblicuos, gemelos y antebrazos. La semana se trata como un ciclo: domingo y lunes son
consecutivos.

Editar el prompt y quitar el bloque `<reparto>` no relaja la validación: el plan se seguiría
comprobando contra lo pedido y el modelo se quedaría sin saber qué se le pide. Si se cambia una
cosa hay que cambiar la otra.

## Auditoría — `AIGeneration`

Cada llamada deja una fila: usuario, tipo, proveedor, modelo, prompt renderizado, respuesta cruda,
salida parseada, tokens de entrada y salida, latencia, estado y error.

Sirve para tres cosas: depurar por qué una generación salió mal, auditar el gasto, y contar llamadas
en ventana de tiempo para los límites de tasa.

**`prompt_rendered` y `raw_response` son solo para staff.** No se exponen por la API ni se renderizan
a usuarios.

## Límites de tasa

| Superficie | Límite |
|---|---|
| Generación de rutina | 5/hora y 20/día por usuario |
| Análisis de progreso bajo demanda | 3/hora por usuario |

Se cuentan sobre `AIGeneration`. Aquí el límite es control de abuso **y** de gasto: cada llamada
cuesta dinero real.
