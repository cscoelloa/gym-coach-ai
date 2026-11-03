# Gym Coach AI

Aplicación de gimnasio donde planificas tu semana de entrenamiento, registras lo que realmente
levantas y una IA te dice cuándo has dejado de progresar. Se instala en el teléfono como una
aplicación (PWA) y funciona también sin conexión.

**Stack:** Django 5.2 + Django REST Framework · PostgreSQL · Celery + Redis · React 19 +
TypeScript + Vite + TanStack Query + Tailwind CSS v4 · SDKs de Anthropic, OpenAI y Google Gemini.

## El problema que resuelve

Quien entrena en serio acaba llevando su rutina en una libreta o una hoja de cálculo. Eso sirve para
*anotar*, pero no para *detectar*. Hay dos cosas que nadie ve a tiempo:

- **El estancamiento silencioso.** Llevas nueve semanas con el mismo peso en press de banca. No
  suena ninguna alarma, y un día te das cuenta de que llevas dos meses igual.
- **La deriva respecto al objetivo.** Dices que estás en volumen, pero llevas tres semanas perdiendo
  200 g cada una. La báscula te da un número suelto; nadie te dice la tendencia.

Las dos se pueden detectar con los datos que ya estás anotando. Lo que falta es que alguien los
mire.

## Qué hace

- **Rutinas reutilizables** («Empuje», «Tirón», «Pierna») que **asignas a los días de la semana**.
  La misma rutina puede ir en dos días: se edita una vez y cambian los dos.
- **Modo foco para entrenar:**
  - un ejercicio a la vez, con su animación;
  - lo que levantaste la última vez y la progresión sugerida;
  - botones −/+ para no abrir el teclado.
- **Un descanso que no se pierde.** Lo guarda el servidor, así que sigue aunque cierres la
  aplicación, y **un aviso push** te avisa cuando acaba.
- **Peso corporal** con una gráfica de tendencia sobre media móvil.
- **12 métricas** de fuerza, volumen, constancia y composición corporal, configurables por usuario.
  Cada una dice cuántos datos tiene detrás.
- **Generación de rutinas con IA**, fundamentada en literatura de hipertrofia mediante RAG. La
  rutina se previsualiza y no se guarda nada hasta que la aceptas.
- **Análisis de progreso con IA**: detecta estancamientos, propone cambios y avisa en la bandeja de
  notificaciones.
- **PWA instalable**: tema claro, oscuro o el del sistema, y abre sin conexión. Nunca guarda tus
  datos en el teléfono, solo la aplicación.
- **API REST** con sesión por cookie para la web y JWT para un futuro cliente móvil.

## Requisitos

| Herramienta | Versión | Para qué |
|---|---|---|
| Python | **3.11** | Django 5.2 todavía no admite 3.14 |
| Node.js | 22 | construir el frontend |
| Docker y Docker Compose | cualquiera reciente | PostgreSQL 16 y Redis 7 en desarrollo |
| Git | — | clonar el catálogo de ejercicios |

## Puesta en marcha (desarrollo)

```bash
# 1. Código y entorno de Python
git clone https://github.com/cscoelloa/gym-coach-ai.git
cd gym-coach-ai
python3.11 -m venv .venv            # Windows: py -3.11 -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

# 2. El catálogo de ejercicios (repositorio externo; no va en este repo)
git clone https://github.com/hasaneyldrm/exercises-dataset.git vendor/exercises-dataset

# 3. Configuración: copiar la plantilla y generar las dos claves
cp .env.example .env                  # Windows: copy .env.example .env
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
#   → la primera en SECRET_KEY y la segunda en FIELD_ENCRYPTION_KEYS

# 4. Base de datos, Redis y datos iniciales
docker compose up -d                                             # PostgreSQL en :55432 y Redis en :6380
python manage.py migrate
python manage.py import_catalog --source vendor/exercises-dataset   # 1324 ejercicios
python manage.py sync_metrics                                       # el catálogo de métricas
python manage.py seed_prompts                                       # los prompts por defecto
python manage.py createsuperuser                                    # tu cuenta (es staff)

# 5. El frontend. Sin el bundle construido no hay aplicación.
npm --prefix frontend ci
npm --prefix frontend run build

# 6. Arrancar
python manage.py runserver            # http://localhost:8000
```

En desarrollo, las tareas de Celery se ejecutan dentro del propio proceso
(`CELERY_TASK_ALWAYS_EAGER=True`), así que no hace falta un worker. Para probar los avisos push o el
análisis programado, pon esa variable a `False` y arranca `celery -A config worker -l info` y
`celery -A config beat -l info` en otras dos terminales.

Para recargar en caliente mientras tocas el frontend: `npm --prefix frontend run dev` y
`VITE_DEV_SERVER_URL=http://localhost:5173` en el `.env`.

### Ver la aplicación con datos

```bash
python manage.py seed_demo
```

Crea el usuario **`demo`** (contraseña `DemoGym-2026-Segura`) con doce semanas de historial: tres
rutinas repartidas en cuatro días, 37 entrenamientos y 62 registros de peso. Está construido a
propósito con **un ejercicio estancado** y **un peso que se aparta del objetivo**, para que el
análisis tenga algo que encontrar.

## Configuración

Todo se configura por variables de entorno en `.env`. [`.env.example`](.env.example) explica cada
una y cómo generarla.

| Variable | Obligatoria | Qué es |
|---|---|---|
| `SECRET_KEY` | sí | La clave de Django |
| `FIELD_ENCRYPTION_KEYS` | sí | Claves Fernet con las que se cifran en la base de datos las API keys de la IA. Admite varias para rotarlas |
| `DATABASE_URL` | sí | La conexión a PostgreSQL |
| `REDIS_URL` | sí | El broker de Celery |
| `ALLOWED_HOSTS` | sí | Los dominios desde los que se sirve la aplicación |
| `SITE_URL` | en producción | El origen con el que se construyen los enlaces de los correos y los avisos |
| `CSRF_TRUSTED_ORIGINS` | en producción | El mismo origen, con `https://` |
| `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY`, `VAPID_SUBJECT` | no | Los avisos push. Las tres o ninguna; sin ellas el aviso se apaga y todo lo demás funciona |
| `EMAIL_HOST` y compañía | no | El correo saliente. Sin él, los correos salen en la consola |
| `MEDIA_STORAGE` | no | Dónde vive `media/` en producción: `r2` (Cloudflare R2, por defecto) o `disco` |

### La IA

**El código no trae ninguna API key.** Con una cuenta de staff, ve a **Gestión → IA**
(`/gestion/ia/`):

1. elige el proveedor (Anthropic, OpenAI o Google Gemini) y el modelo;
2. pega tu clave, que se guarda cifrada y nunca se vuelve a mostrar entera;
3. pulsa **«Probar conexión»**, que hace una llamada real y te dice si funciona.

En la misma pantalla están los prompts, las reglas de programación por objetivo y los documentos
del RAG.

> El RAG necesita una clave de **OpenAI aunque el proveedor activo sea otro**: los almacenes
> vectoriales viven ahí. Detalle en [`.docs/03-ai-config.md`](.docs/03-ai-config.md).

## Tests y calidad

```bash
pytest                                        # el backend (requiere el bundle construido)
npm --prefix frontend run test                # los componentes (vitest)
npm --prefix frontend run e2e                 # recorridos en el navegador (Playwright)
ruff check .                                  # lint
bandit -q -c pyproject.toml -r apps config    # análisis estático de seguridad
pip-audit --strict                            # dependencias vulnerables
```

El CI (`.github/workflows/ci.yml`) ejecuta todo eso más `manage.py check --deploy`. Además corre
cada semana aunque nadie toque el código, porque las vulnerabilidades se publican solas.

## Despliegue

Hay dos caminos documentados, y la configuración de los dos está en el repo.

**En tu propio PC, para uso personal** ([`despliegue/casa/`](despliegue/casa/), ADR-070). Docker
Compose levanta PostgreSQL, Redis, la web, el worker, beat y Caddy, solo en `127.0.0.1`. El teléfono
entra por **Tailscale Serve** con HTTPS válido, sin abrir ningún puerto a internet. Cuesta $0.

```bash
sh scripts/casa.sh preparar <tu-pc>.<tu-tailnet>.ts.net [tu-correo]   # genera el .env con secretos
sh scripts/casa.sh subir                # construye la imagen y arranca
sh scripts/casa.sh catalogo             # importa el catálogo
sh scripts/casa.sh admin                # crea tu cuenta
tailscale serve --bg http://127.0.0.1:8080
```

También incluye `respaldo`, `restaurar` y `certificado`, este último para los antivirus que
inspeccionan el HTTPS.

**En una PaaS** (Railway: `railway.toml`, `railpack.json`, `Procfile`). Tres procesos (web, worker
y beat), con PostgreSQL y Redis gestionados y `media/` en Cloudflare R2.

Los dos caminos, paso a paso, están en [`.docs/05-runbook.md`](.docs/05-runbook.md).

## Estructura

```text
apps/                 # las apps de Django: api, accounts, workouts, metrics, aiassist, bodyweight…
config/               # settings (base, dev, prod), urls y Celery
frontend/src/
├── modulos/          # una carpeta por funcionalidad: su api.ts, pantallas, piezas y tests
├── ds/               # el sistema de diseño en componentes
└── lib/              # infraestructura: PWA, tema, descanso, avisos push…
assets/app.css        # el sistema de diseño: tokens, escala y utilidades
templates/spa.html    # la única plantilla: la cáscara de la SPA
despliegue/casa/      # Docker Compose, Caddy y plantilla del .env para el PC
.docs/                # la documentación
```

## Documentación

| Archivo | Para qué |
|---|---|
| [`00-vision.md`](.docs/00-vision.md) | Qué es y para quién |
| [`01-decisions.md`](.docs/01-decisions.md) | Cada decisión con su razón, en formato ADR |
| [`02-architecture.md`](.docs/02-architecture.md) | Carpetas, modelo de datos y recorridos |
| [`03-ai-config.md`](.docs/03-ai-config.md) | Proveedores, prompts y RAG |
| [`05-runbook.md`](.docs/05-runbook.md) | Comandos, despliegue y diagnóstico |
| [`06-security.md`](.docs/06-security.md) | Modelo de amenazas y controles |
| [`07-reglas.md`](.docs/07-reglas.md) | Las reglas que se cumplen en todo cambio |

## Decisiones de diseño que conviene conocer

- **La aritmética se hace en Python, no en el LLM.** Las métricas (1RM estimado, volumen por grupo
  muscular, pendientes de progresión, tendencia de peso) se calculan en `apps/metrics/` y están
  cubiertas por tests. El modelo recibe números ya hechos y los interpreta. Un número mal sumado
  por un modelo no se detecta en revisión; uno mal sumado en Python lo caza un test.
- **La IA no inventa ejercicios.** Recibe una lista cerrada de identificadores del catálogo y tiene
  que elegir de ahí. Si devuelve uno que no existe, se rechaza y se reintenta pasándole el error.
  Es a la vez calidad de datos y la defensa principal contra la *prompt injection*.
- **El cálculo determinista decide si se llama al modelo.** Solo se analiza con IA cuando el ritmo
  real se aparta del objetivo. Y si todo va bien no se avisa: un aviso que dice «todo correcto»
  enseña a ignorar la campana.
- **Los datos de salud no salen de donde deben.**
  - La sesión va en una cookie `HttpOnly`, nunca en `localStorage`.
  - El service worker nunca guarda respuestas de la API.
  - A la IA se le manda la edad, no la fecha de nacimiento.
  - Ningún queryset sin filtrar por usuario, y ante lo ajeno se responde 404.

## Licencia

El código se distribuye bajo la **[licencia MIT](LICENSE)**. El material de terceros mantiene la
suya ([`NOTICE.md`](NOTICE.md)):

- **El catálogo de ejercicios**, de
  [`hasaneyldrm/exercises-dataset`](https://github.com/hasaneyldrm/exercises-dataset), es MIT y se
  descarga aparte.
- **Las imágenes y animaciones de los ejercicios son © Gym Visual.** **No están en este
  repositorio** ni las cubre su licencia: llegan con el dataset, redistribuidas con permiso solo a
  180×180 y con su atribución. Para uso personal, académico o de portafolio no hay problema; **para
  publicarlo como producto hay que obtener licencia propia en [gymvisual.com](https://gymvisual.com/).**
- **El mapa corporal**, de [`vulovix/body-muscles`](https://github.com/vulovix/body-muscles), es
  Apache 2.0 y lleva su `LICENSE` y su `NOTICE` en `apps/workouts/bodymap/`.

### Sobre el diseño de las pantallas

Algunos patrones de interfaz están **inspirados en
[openGym](https://github.com/DuarteSantos8/openGym)**: la tira de la semana, las filas de día, los
tiles de cifras, el calendario de actividad y el modo foco. Son disposiciones funcionales y comunes
en las aplicaciones de fitness. openGym es **AGPL v3**, así que conviene ser explícito: **no se ha
copiado nada de su código, ni sus iconos, ni sus textos**. Todo está reimplementado desde cero, y
el sistema de diseño propio («Aire», ADR-061) usa otra paleta. Razonado en el ADR-022.
