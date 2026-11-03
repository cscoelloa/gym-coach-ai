# Arquitectura

> Este archivo describe **cómo es el proyecto hoy**. El *por qué* de cada decisión está en
> `01-decisions.md`, y las reglas que se cumplen en todo cambio, en `07-reglas.md`.

## Las dos mitades

Django sirve **una sola plantilla** —la cáscara— y una API. Todo lo que se ve lo pinta React
(ADR-047). No queda ninguna pantalla renderizada por una plantilla.

```
navegador
   │
   ├─ GET /cualquier-pantalla/  ──►  Django  ──►  templates/spa.html
   │                                              (cáscara: <div id="root"> + {% vite %})
   │
   └─ GET/POST /api/…           ──►  Django REST Framework  ──►  servicios  ──►  BD
                                     sesión por cookie (ADR-046)
```

- **El bundle lo construye Vite** y lo sirve Django bajo `/static/spa/`.
  `apps/common/vite.py` lee `frontend/dist/.vite/manifest.json` para saber qué archivo con hash
  toca poner, y lo enlaza **por el nombre de Vite**, sin el segundo hash de `collectstatic`
  (ADR-060). En desarrollo, con `VITE_DEV_SERVER_URL` puesto, apunta a `:5173` con HMR.
- **El sistema de diseño es un solo archivo**, `assets/app.css` («Aire», ADR-061), que compila
  `@tailwindcss/vite` dentro del bundle. No hay CSS comiteado. El tema lo resuelve
  `static/js/theme.js` antes de pintar: sigue al del sistema salvo que se fuerce uno.
- **`/admin/` de Django sigue existiendo** como red de seguridad del panel de gestión (ADR-048).


## Interacción de usuario (ADR-051)

El data router de React conserva las URLs de Django y permite bloquear salidas con un borrador
pendiente. `CambiosPendientes` coordina el editor y Cuenta, y pregunta con `Confirmacion` —un panel
de la aplicación, no `window.confirm` (ADR-053)—; `beforeunload` protege las recargas.
El editor mantiene el borrador únicamente en memoria y manda la lista completa al guardar.
`RoutineSerializer` valida y guarda nombre, descripción y ejercicios dentro de una transacción;
omitir `exercises` mantiene el comportamiento de la API anterior.

`Cabecera`, `Panel` y las listas compactas unifican las pantallas.

**El marco (ADR-062)** es `ds/AppShell.tsx`:
- **Barra superior translúcida.** Lleva el «atrás», el título de la pantalla cuando el grande ya
  no se ve, y en el teléfono la campana y la inicial que abre Cuenta. `Cabecera` publica su
  título en `lib/marco.tsx`, y un `IntersectionObserver` decide cuándo repetirlo arriba.
- **«Atrás»** vuelve por el historial si lo hay y, si no, al padre de la pantalla, que sale de
  `ds/navegacion.ts`.
- **Barra de pestañas** abajo en el teléfono y **barra lateral** desde `lg`.

Fuera de ese marco quedan dos casos:
- **El modo foco** (entrenar) no lleva marco: ni barras ni Cuenta.
- **Gestión** no lleva barra de pestañas en el teléfono.

## Mapa de carpetas

```
PROJECT_GYM/
├── .docs/                      # la documentación: decisiones, arquitectura, IA, reglas…
├── config/                     # settings/, urls.py, celery.py, wsgi.py
├── apps/
│   ├── common/                 # la cáscara de la SPA, el lector del manifiesto de Vite, la PWA
│   ├── api/                    # TODA la superficie HTTP: recursos, pantallas, IA y gestión
│   ├── accounts/               # User personalizado, perfil, exportación y borrado (RGPD)
│   ├── workouts/               # catálogo, rutinas, programas, sesiones, series, mapa corporal
│   ├── bodyweight/             # registro de peso corporal
│   ├── metrics/                # el catálogo de métricas y los resúmenes de Inicio y Progreso
│   ├── aiassist/               # config de IA, prompts, RAG, generación, análisis
│   └── notifications/          # bandeja in-app + email
├── assets/app.css              # tokens y componentes visuales compartidos. LA fuente.
├── frontend/
│   ├── src/
│   │   ├── App.tsx             # compone las rutas de los módulos con su guarda (ADR-069)
│   │   ├── modulos/            # uno por funcionalidad: api.ts, pantallas, piezas y tests
│   │   │   ├── index.ts        # RUTAS: las de todos los módulos
│   │   │   └── <modulo>/       # inicio, entrenar, plan, ejercicios, progreso, peso, perfil,
│   │   │                       # ia, notificaciones, acceso, gestion, estilos
│   │   ├── ds/                 # el sistema de diseño: nunca importa de un módulo
│   │   ├── lib/                # infraestructura: caché, PWA, tema, descanso, avisos push…
│   │   ├── api/                # lo transversal: cliente, tipos, sesión, avisos, mapa corporal
│   │   └── rutas.ts            # qué URL sirve la SPA (se compara con config/urls.py)
│   └── e2e/                    # recorridos de Playwright
├── templates/spa.html          # la única plantilla que queda
├── static/                     # fonts/, pwa/, js/theme.js
├── media/exercises/            # JPG y GIF importados (180×180)
├── Dockerfile                  # la imagen del alojamiento en casa (ADR-070); Railway usa Railpack
├── despliegue/casa/            # compose, Caddyfile y plantilla del .env para el PC + Tailscale
└── vendor/exercises-dataset/   # clon del dataset — ignorado por git
```

**Al mover o añadir una pantalla hay que tocar tres sitios**: el `index.ts` de su módulo,
`config/urls.py` y `frontend/src/rutas.ts`. Los comparan dos tests:
`apps/common/tests/test_rutas_de_la_spa.py` (Django ↔ `rutas.ts`) y `frontend/src/modulos/rutas.test.ts`
(`rutas.ts` ↔ los módulos). Ver ADR-069.

## Modelo de datos

```
User ──┬── Program ──── ScheduleEntry (7, uno por día) ──► Routine ──── RoutineExercise ──► Exercise
       │                                                      │                               │
       ├── WorkoutSession ──────────────────────────────────►─┘                               │
       │        │                                                                             │
       │        └── SetLog ──────────────────────────────────────────────────────────────────►┘
       │
       ├── BodyWeightEntry
       ├── Notification
       ├── UserMetricPreference ──► Metric
       └── AIGeneration ──► Program / Routine (si la generación se aceptó)

Exercise ──┬──► MuscleGroup            (target_muscle, FK)
           └──► MuscleGroup            (secondary_muscles, M2M)
```

**Detalles que importan:**

- **La rutina es una plantilla, no una semana** (ADR-028). `Routine` tiene sus ejercicios, y
  `ScheduleEntry` dice qué rutina va en cada día del programa. Eso es lo que permite asignar
  «Empuje» al lunes **y** al jueves sin describirla dos veces — antes eran dos listas que se
  separaban en cuanto tocabas una.
- Un día con `routine=None` **es** descanso. No hay un `is_rest_day` aparte que pudiera
  contradecir a la asignación.
- `Program.is_active`: solo uno a la vez. `activate()` desactiva los demás en la misma
  transacción; con dos activos, la semana que se enseña dependería del `order_by` de quien
  preguntara.
- `RoutineExercise` guarda el objetivo (`target_sets`, `target_reps_min/max`, `rest_seconds`);
  `SetLog` guarda lo que realmente pasó. **La comparación entre ambos es de dónde sale el análisis
  de progreso** — sin esa separación no habría nada que analizar.
- `SetLog` apunta a `Exercise` directamente, no a `RoutineExercise`: media sesión se improvisa.
  El `set_number` **lo pone el servidor** (`SetLogViewSet.perform_create`).
- `Exercise.external_id` es el id del dataset (`"0001"`). Es la clave que hace idempotente al
  importador y la que devuelve la IA al generar rutinas.
- `Exercise` es el **único** modelo que mezcla filas públicas (`is_global=True`) con filas de
  alguien (`created_by`). Por eso se consulta siempre con `visible_to(user)` (ADR-026).
- `AIProviderConfig` y `PromptTemplate`: una fila activa a la vez, garantizado en `save()`.

## Capa de API

Todo lo que habla HTTP vive en `apps/api/`, repartido por lo que responde:

| Archivo | Qué sirve |
|---|---|
| `views.py` | los recursos: rutinas, programas, días, series, peso, avisos, métricas |
| `auth.py` | sesión, registro, contraseña, cuenta (exportar y borrar) |
| `pantallas.py` | lo que pide **una pantalla entera**: `/inicio/`, `/plan/`, `/progreso/`, `/mapa-corporal/` |
| `ia.py` | generar, previsualizar, aceptar, descartar, analizar |
| `gestion.py` | el panel de staff, todo con `IsAdminUser` (ADR-048) |

**Dos clases base imponen lo que no se puede olvidar:** `OwnedModelViewSet` filtra por
`request.user` —recurso ajeno da **404, no 403**— y `VistaDeGestion` exige `IsAdminUser`. Las dos
tienen un test que recorre el router entero, no una lista escrita a mano.

**Un endpoint de pantalla no calcula nada.** `/api/progreso/` llama a `apps/metrics/summary.py`;
`/api/entrenamientos/{id}/foco/` llama a `apps/workouts/focus.py`. La aritmética vive en Python y
en un solo sitio.

## Capa de IA

```
vista de la API  o  tarea Celery
   │
   ▼
servicio (routine_generator | progress_analyzer | weight_analyzer)
   │
   ├──► apps/metrics/services.py    cálculos deterministas, con su cobertura
   ├──► PromptTemplate              prompt editable desde el panel de gestión
   ├──► catálogo de candidatos      lista cerrada de external_id
   │
   ▼
factory.get_provider()  ──►  AIProviderConfig activa (descifra la API key)
   │
   ▼
LLMProvider (interfaz)
   ├── AnthropicProvider   supports_rag = False
   ├── OpenAIProvider      supports_rag = True   ← file_search
   └── GoogleProvider      supports_rag = False
   │
   ▼
ProviderResult { parsed, raw_text, input_tokens, output_tokens, latency_ms }
   │
   ▼
validación Pydantic  →  transacción en BD  →  AIGeneration (auditoría)
```

Ningún servicio importa `anthropic`, `openai` ni `google-genai`. Todo pasa por la factoría.

## Recorrido: generar una rutina

1. La pantalla pide `GET /api/ia/generar/`: cuántas generaciones quedan, los días del perfil y si
   hay equipamiento declarado.
2. `POST /api/ia/generar/` → `generate_routine()`. Reúne el contexto: perfil (con la **edad**, no
   la fecha de nacimiento), objetivo, equipamiento, lesiones y las métricas con su cobertura.
3. **Selecciona candidatos**: filtra el catálogo por el equipamiento disponible, reparte por zona
   del cuerpo y arma una lista de como mucho 200 entradas. Sin candidatos lanza `NoCandidates`,
   que la API traduce a un 409 con «revisa tu perfil» — y **no llama al modelo**.
4. Renderiza la `PromptTemplate` de clave `routine_generation`. La entrada libre va envuelta en
   `<peticion_usuario>`, declarada como dato y no como instrucción.
5. `factory.get_provider()` devuelve el adaptador de la config activa. Si `supports_rag` y hay
   `VectorStore` activos, se le pasan sus IDs.
6. El proveedor devuelve un `RoutinePlan` validado. Si algún `external_id` no está entre los
   candidatos, se rechaza y se reintenta —hasta **tres** intentos— con una corrección **apuntada
   al fallo que hubo**, no con la misma instrucción genérica.
7. **Previsualización**: se devuelve la propuesta con los ejercicios ya resueltos contra el
   catálogo. **No se ha creado nada.**
8. `POST .../aceptar/` → `apply_plan()`: crea `Program` + 7 `ScheduleEntry` + las `Routine` con
   sus `RoutineExercise`, **en una transacción**, y desactiva los otros programas.
9. La `AIGeneration` queda con tokens, latencia y respuesta cruda — **visible solo para staff**,
   nunca por la API de usuario.

## Recorrido: entrenar

1. `POST /api/entrenamientos/` con la rutina (o sin ella, para un entrenamiento libre). La fecha y
   `started_at` los pone el servidor.
2. `GET .../foco/?ejercicio=N` devuelve qué toca: el ejercicio, sus filas de serie con los valores
   ya propuestos —lo de la serie anterior de hoy, o lo de la última vez—, la mejor marca y la
   sugerencia de progresión. **El índice va en la URL** para que «atrás» y recargar funcionen.
3. `POST /api/series/` registra una serie. El número lo pone el servidor.
4. `POST .../finalizar/` marca la hora y devuelve el **resumen de cierre** (ADR-049): duración,
   tonelaje, récords batidos y músculos trabajados.

## Recorrido: análisis de progreso

Lo dispara el beat semanal de Celery o la persona desde `/ia/analisis/`.

1. `apps/metrics/services.py::for_ai()` calcula las métricas marcadas como `send_to_ai`, **cada
   una con su cobertura**.
2. Esos números —no el historial crudo— van al prompt `progress_analysis`.
3. El LLM devuelve un `ProgressAnalysis`: patrones, ejercicios estancados, recomendaciones,
   cambios propuestos y **`data_caveats`**: lo que no se puede afirmar porque faltan datos.
4. Se crea una `Notification` y se envía el correo.
5. Los cambios propuestos **no se aplican solos**: se listan con un enlace al plan.

## Recorrido: análisis de peso

Lo dispara una señal `post_save` de `BodyWeightEntry`.

1. `weight_analyzer` calcula la media móvil de 7 días y el ritmo real en kg/semana.
2. Se contrasta con `goal` y `weekly_weight_change_target_kg`.
3. El LLM redacta el mensaje y la recomendación (`WeightAnalysis`).
4. Si hay desviación, se crea una `Notification` de tipo `weight_off_track`.

Al prompt va la **edad calculada**, no la fecha de nacimiento.

## Tareas Celery

| Tarea | Disparador |
|---|---|
| `index_knowledge_document(doc_id)` | subida de un documento al RAG |
| `run_weekly_progress_analysis()` | beat semanal |
| `analyze_new_bodyweight(entry_id)` | señal `post_save` de `BodyWeightEntry` |
| `send_notification_email(notification_id)` | creación de una notificación |

## PWA

**Abre sin conexión; los datos, nunca de caché** (ADR-063). `/manifest.webmanifest` y `/sw.js`
los sirven vistas de `apps/common/pwa.py`, las dos **desde la raíz**:
- el alcance de un service worker es su propia ruta;
- el manifiesto necesita que las URL de los iconos pasen por `static()` para salir con su hash.

```
apps/common/pwa.py      manifiesto, versión del build, lista de precarga, vista de /sw.js
apps/common/sw.js       el service worker; la vista le pone delante la configuración
frontend/src/lib/pwa.ts       registro, «hay una versión nueva», borrar cachés al salir
frontend/src/lib/cache.ts     la caché de TanStack: mutaciones que no esperan a la red
frontend/src/lib/conexion.ts  useEnLinea(), sobre onlineManager
frontend/src/lib/instalar.ts  beforeinstallprompt en Chrome; los pasos en iOS
```

**Qué guarda el service worker.**
- La cáscara, pedida a `/entrar/` sin credenciales. No lleva datos de nadie, y lo comprueba un
  test.
- Los archivos del build, sacados del manifiesto de Vite.
- `theme.js` y los iconos.

Todo va en la caché `gym-<versión>`, y la versión es la huella del build. `/api/`, `/admin/` y
`/media/` no los toca.

**Cómo atiende las peticiones.**
- Una navegación va primero a la red; sin red, se sirve la cáscara guardada.
- Los estáticos salen primero de la caché.

**Cómo se actualiza.** La versión nueva se instala y **espera**: la página enseña «Hay una versión
nueva» y solo se aplica al pulsar «Actualizar».

**Al cerrar sesión** se borran las cachés.

**Interruptor de emergencia:** `PWA_OFFLINE=False`.
