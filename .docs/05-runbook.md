# Runbook

## Puesta en marcha desde cero

```bash
# 1. Dependencias — Python 3.11 (Django 5.2 no soporta 3.14)
py -3.11 -m venv .venv
.venv\Scripts\activate            # Windows
pip install -r requirements-dev.txt

# 2. Catálogo de ejercicios (repo externo, ignorado por git)
git clone https://github.com/hasaneyldrm/exercises-dataset.git vendor/exercises-dataset

# 3. Configuración
copy .env.example .env            # y rellenar los valores
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
#   → pegar en FIELD_ENCRYPTION_KEYS
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
#   → pegar en SECRET_KEY

# 4. Infraestructura
docker compose up -d              # postgres + redis

# 5. Base de datos
python manage.py migrate
python manage.py import_catalog --source vendor/exercises-dataset
python manage.py sync_metrics     # sin esto, Progreso y su catálogo de métricas salen vacíos
python manage.py createsuperuser

# 6. Frontend en React — OBLIGATORIO, no es opcional (ADR-047)
npm --prefix frontend ci
npm --prefix frontend run build

# 7. Arrancar (tres terminales)
python manage.py runserver
celery -A config worker -l info
celery -A config beat -l info
```

> **El paso 6 no es opcional.** `frontend/dist/` está en `.gitignore`, y sin bundle **no hay
> aplicación**: la cáscara responde con `ImproperlyConfigured` y `pytest` falla en los tests que
> la recorren. El mensaje dice qué ejecutar.
>
> El CSS también sale de ahí: lo compila `@tailwindcss/vite` dentro del bundle desde
> `assets/app.css`. Ya no hay binario standalone ni CSS comiteado (Fase 10).

## Frontend en React (Vite)

**La mudanza terminó.** Django sirve una sola plantilla —`templates/spa.html`, la cáscara— y la
API; todo lo que se ve lo pinta React (ADR-046, ADR-047). `SPA_URLS` en `config/urls.py` sigue
siendo el registro de qué URL existen, y ahora son todas.

```bash
# Trabajando en el frontend: dos terminales y recarga en caliente.
#   1) poner VITE_DEV_SERVER_URL=http://localhost:5173 en `.env`
npm --prefix frontend run dev     # :5173 — sirve los módulos
python manage.py runserver        # :8000 — sirve la cáscara, la sesión y la API

# Tipos y tests de componente
npm --prefix frontend run lint
npm --prefix frontend run test

# Recorridos completos en un navegador de verdad (Chrome ya instalado, no descarga nada). En una
# máquina sin Chrome, con Edge: `PLAYWRIGHT_CHANNEL=msedge npm --prefix frontend run e2e`.
# «el panel de gestión» necesita un proveedor de IA configurado en /gestion/ia/; en una base de
# datos recién creada falla por eso, no por el código.
# La cuenta `e2e` tiene el cupo normal de la API (1000 peticiones al día). Tres o cuatro pasadas
# seguidas lo agotan y todo empieza a fallar con 429: el contador vive en la caché en memoria, así
# que basta con reiniciar `runserver`. **Y que sea el que escucha**: en Windows dos `runserver` pueden
# quedarse a la vez en el 8000, y Playwright le habla al primero que se abrió —reiniciar el otro no
# cambia nada—. `netstat -ano | findstr :8000` dice cuántos hay.
# La cuenta de pruebas se crea una vez; es idempotente.
python frontend/e2e/usuario.py
# El servidor tiene que estar levantado **con el entorno virtual activado**: el `webServer` de
# `playwright.config.ts` arranca `python` a secas, y si no es el del venv no encuentra Django.
# Con uno ya escuchando en :8000, `reuseExistingServer` lo aprovecha.
python manage.py runserver 8000 --noreload --skip-checks
npm --prefix frontend run e2e

# Antes de comitear, y para probar contra lo que se despliega de verdad:
#   quitar VITE_DEV_SERVER_URL del `.env` y construir.
npm --prefix frontend run build
```

**Quitar `VITE_DEV_SERVER_URL` antes de dar nada por bueno.** El servidor de desarrollo esconde
justo los fallos que rompen en producción: el orden de carga de la hoja de estilos, las rutas con
hash y el prefijo `base`. Por eso el modo lo decide esa variable y no `DEBUG` — se puede depurar
el bundle construido con `DEBUG=True`.

Con la variable puesta, `dev.py` le abre la CSP a `:5173` (módulos, websocket de HMR y fuentes).
Esa apertura **no existe en producción**, donde `script-src` se queda en `'self'` sin excepciones.

El bundle **no se comitea**, al revés que el CSS: ahora hay un paso de Node en CI y en el
despliegue (`railway.toml` + `railpack.json`; `nixpacks.toml` para Nixpacks), así que comitear el artefacto solo serviría para que se quedara
viejo. `frontend/dist` entra en `STATICFILES_DIRS` bajo el prefijo `spa/`, que es el mismo que
declara `base` en `vite.config.ts`: los dos tienen que coincidir, porque es la ruta con la que el
propio bundle se pide sus trozos y ahí Django no puede intervenir.

**Los recorridos de Playwright son la única comprobación que ve lo que ve el navegador.** Tres
cosas que ningún test de servidor ni de jsdom puede afirmar, y las tres fallan sin romper la
página: que la CSP no bloquee nada, que la hoja de estilos y las fuentes con hash lleguen (sin
ellas la aplicación se ve «casi bien», con la tipografía de respaldo y las cifras sin alinear) y
que la PWA sea instalable —manifiesto servido con su tipo, iconos que existen y service worker
registrado—. Por eso recogen los errores de consola y **fallan si hay uno solo**.

**La sesión se abre una sola vez por pasada** (`e2e/acceso.setup.ts`, proyecto `acceso`) y los dos
proyectos de navegador arrancan con la cookie ya puesta. No es velocidad: con cada recorrido
entrando por su cuenta eran una treintena de inicios de sesión por pasada, y `POST
/api/auth/session/` tiene un límite de 60 a la hora —bajo a propósito, porque ahí se comprueba una
contraseña—, así que **la segunda ejecución dentro de la misma hora fallaba entera**, y con el
síntoma más confuso que hay: la pantalla de acceso otra vez, como si la sesión no se abriera.

Dos recorridos van aparte y tienen que seguir yendo aparte:

- **«entrar lleva a Inicio»** limpia las cookies y teclea las credenciales: es el que comprueba el
  formulario, y con sesión puesta no vería ni el formulario.
- **«salir cierra la sesión»** abre **una sesión suya** antes de cerrarla. `logout()` invalida la
  sesión en el servidor, así que cerrar la compartida deja sin ella a todo lo que venga después.
  Eso ya pasó: escritorio pasaba entero y móvil —que corre detrás— fallaba entero.

### Al añadir una pantalla

Hay que tocar **tres** sitios, y si se olvida uno no falla nada evidente:

1. `frontend/src/modulos/<modulo>/index.ts` — la ruta en la lista `rutas` del módulo: URL,
   pantalla y acceso (`publica`, `privada`, `foco` o `staff`). Si es un módulo nuevo, se suma
   también en `modulos/index.ts`.
2. `config/urls.py` — la URL a `spa` (o a `spa_publica`), en `SPA_URLS`.
3. `frontend/src/rutas.ts` — la URL en `RUTAS_DE_LA_SPA`, que es lo que hace que los enlaces de la
   barra naveguen dentro de la aplicación en vez de recargar la página.

Los sitios 2 y 3 los compara `apps/common/tests/test_rutas_de_la_spa.py`, y el 1 y el 3
`frontend/src/modulos/rutas.test.ts` (ADR-069).

## Estilos (Tailwind v4)

`assets/app.css` es **la fuente y lo único que se edita**. Lo compila Vite dentro del bundle:

```bash
# Mientras se trabaja: el servidor de desarrollo recompila el CSS al guardar, igual que el JS.
npm --prefix frontend run dev

# Antes de comitear, contra lo que se despliega de verdad:
npm --prefix frontend run build
```

**Ya no hay binario standalone ni CSS comiteado.** Existieron mientras Django renderizaba
plantillas: el mismo archivo se compilaba dos veces —el binario para `static/css/app.css` y Vite
para el bundle— y el artefacto comiteado tenía su job de CI para que no se quedara viejo
(ADR-019). Con la última plantilla se fueron los tres: el binario, el CSS y el job. Si esto
cambia y no se reconstruye, no hay bundle — no hay forma de que se separen.

`@source "../apps"` **sigue haciendo falta** aunque no quede HTML: `Notification.badge_class`
devuelve el nombre de la clase desde Python y viaja por la API hasta React. Sin escanear ahí, esas
insignias se quedan sin estilo y **ningún test lo ve**: el marcado es correcto, lo que falta es la
regla.

Para revisar el sistema entero —color, tipografía y los doce componentes en sus estados, en los dos
temas— está **`/estilos/`** (requiere sesión). Lleva el conmutador de tema arriba a propósito: la
mitad de los errores de un sistema con dos temas solo aparecen al cambiar de uno a otro. Es el sitio
donde comprobar que un cambio en `assets/app.css` no ha roto nada, sin recorrer las 33 plantillas.

El contraste de la paleta no se juzga a ojo: lo calcula `TestElContrasteSeCalcula`
(`apps/common/tests/test_design_system.py`) sobre los valores del propio archivo, con los umbrales
de WCAG 2.2. Al tocar un color, `pytest apps/common/tests/test_design_system.py` dice qué par se
ha quedado corto.

### El tema

Sigue al del sistema salvo que la persona fuerce uno desde Cuenta (ADR-061). `static/js/theme.js`
lo resuelve antes de pintar y por eso se carga **sin `defer` y antes del bundle**; moverlo o
añadirle `defer` devuelve el destello de tema equivocado en cada carga. Deja dos atributos en
`<html>`: `data-theme` (lo que se pinta, `light`/`dark`) y `data-theme-pref` (lo elegido,
`system`/`light`/`dark`). La preferencia vive en `localStorage["gym-tema"]`.

Al añadir un token hay que añadirlo **en los dos bloques**, `:root,:root[data-theme="light"]` y
`:root[data-theme="dark"]`. Uno que falte en uno de los dos no se ve hasta que alguien conmuta; lo
comprueba `apps/common/tests/test_design_system.py`.

**Colores fuera del CSS.** `theme.js`, `spa.html`, el manifiesto (`apps/common/pwa.py`), el
generador de iconos, los respaldos de `ds/grafica/tema.ts` y la página sin conexión de
`apps/common/sw.js` escriben hex literales, porque ahí no llegan las variables. Al cambiar un
token hay que cambiarlos también; `TestLosColoresDeLaMarcaSonTokens` falla si se olvida uno.

### El mapa corporal

Los 89 trazados de la anatomía están vendorizados en `apps/workouts/bodymap/` y vienen de
`vulovix/body-muscles` (Apache-2.0). De dónde salen, qué obliga esa licencia y cómo regenerarlos:
**`apps/workouts/bodymap/LEEME.md`**.

Qué región del dibujo es qué músculo se decide en `REGION_MUSCLE`, en `apps/workouts/taxonomy.py`.
**Todo el mapa habla en slugs**, con guion (`upper-back`), que es lo que guarda `MuscleGroup.slug`;
un destino escrito con espacios no encuentra nada y el músculo no se enciende nunca. Lo comprueban
los tests de `apps/workouts/tests/test_bodymap.py`, que exigen además que cada región tenga destino
y cada músculo tenga región o esté declarado sin ella.

Al añadir un nivel o una región nueva hay que acordarse del `@source inline("bm-{0,1,2,3,4}")` de
`assets/app.css`: esas clases se construyen en tiempo de ejecución y el escáner de Tailwind no las
ve.

### Las fuentes

Inter variable vive en `static/fonts/` porque la CSP declara `font-src: 'self'` y un enlace a
Google Fonts quedaría bloqueado. Son dos `.woff2` comiteados: `latin` (73 KB), que es el que se
descarga casi siempre, y `latin-ext` (133 KB), solo cuando hace falta. De dónde salen y cómo
regenerarlas: **`static/fonts/LEEME.md`**.

### Los iconos de la PWA

Son archivos comiteados en `static/pwa/`, dibujados con la geometría del icono «Entrenar» y los
colores `--primary-fill` y `--primary-hover` de `assets/app.css`. Si cambian esos colores, hay que
rehacer los iconos con cualquier editor gráfico y sustituirlos con los mismos nombres y tamaños.

## La PWA (ADR-063)

La aplicación **abre sin red**: el service worker (`apps/common/sw.js`, servido por
`apps/common/pwa.py` en `/sw.js`) guarda la cáscara y el build. Los datos nunca: `/api/` no lo
toca.

- **Solo con el bundle construido.** Con `VITE_DEV_SERVER_URL` el service worker no cachea, y el
  bundle no lo registra fuera del build (`import.meta.env.PROD`).
- **Depurarlo:** DevTools → Application → Service workers y Cache storage. La caché se llama
  `gym-<versión>`, y la versión es la de `<meta name="app-version">` en la cáscara. La casilla
  «Offline» de esa pestaña simula el sótano del gimnasio.
- **Probar una actualización:** con la aplicación abierta, `npm --prefix frontend run build`,
  recargar una vez —el navegador descarga el service worker nuevo y lo deja esperando— y debe
  aparecer «Hay una versión nueva». «Actualizar» recarga con la nueva.
- **Interruptor de emergencia:** si un despliegue dejara a alguien atascado en una versión vieja,
  `PWA_OFFLINE=False` en el entorno. `/sw.js` pasa a ser uno que no cachea, borra lo guardado y se
  activa en el acto. No hay que tocar código.
- **En un iPhone de verdad** —Playwright solo emula un Pixel—, al menos una vez por cambio grande:
  Safari → Compartir → «Añadir a pantalla de inicio»; abrir desde el icono y comprobar que no
  sale la barra de Safari, que la hora y la batería se leen sobre la barra superior, que las
  pestañas no quedan debajo de la barra de inicio y que en modo avión abre con «Sin conexión».

### El descanso y los avisos push (ADR-065, ADR-066)

El descanso lo guarda el servidor (`WorkoutSession.rest_ends_at`): salir del modo foco o recargar
lo encuentra donde iba. El aviso push de «descanso terminado» es opcional y **está apagado
mientras no haya claves VAPID**: sin ellas la aplicación no lo ofrece y no se encola nada.

**Generar las claves**, una vez por entorno:

```bash
.venv/Scripts/python -c "from py_vapid import Vapid; v = Vapid(); v.generate_keys(); \
from cryptography.hazmat.primitives import serialization as s; import base64; \
pub = v.public_key.public_bytes(s.Encoding.X962, s.PublicFormat.UncompressedPoint); \
priv = v.private_key.private_numbers().private_value.to_bytes(32, 'big'); \
b = lambda x: base64.urlsafe_b64encode(x).rstrip(b'=').decode(); \
print('VAPID_PUBLIC_KEY=' + b(pub)); print('VAPID_PRIVATE_KEY=' + b(priv))"
```

Y en el entorno, junto a las dos: `VAPID_SUBJECT=mailto:alguien@tu-dominio` (o una URL
`https://`). `prod.py` no arranca con solo una o dos de las tres. **Cambiar las claves invalida
todas las suscripciones**: cada navegador tendrá que volver a activarlas desde Cuenta.

**Probarlo en local.** Con `CELERY_TASK_ALWAYS_EAGER=True` (lo de desarrollo) la tarea se ejecuta
en el acto, ve que es pronto y no hace nada: hace falta un worker de verdad.

```bash
# .env: CELERY_TASK_ALWAYS_EAGER=False y las tres VAPID_*
docker compose up -d                                  # Redis
celery -A config worker -l info --pool=solo           # --pool=solo en Windows
npm --prefix frontend run build && python manage.py runserver
```

El push necesita el service worker, que solo se registra con el bundle construido, y un origen
seguro: `localhost` vale. Activar los avisos en Cuenta, registrar una serie, cerrar la pestaña y
esperar al final del descanso. El worker debe decir `avisar_fin_del_descanso … enviado`. Si dice
`cambiado`, el descanso se saltó o se alargó; si dice `caducado`, el worker llegó más de 2 minutos
tarde.

**En producción** el proceso `worker` del `Procfile` tiene que estar activo: sin él no hay avisos,
y nada más falla.

## Al actualizar desde una versión anterior

La migración `0003_rutinas_asignables_a_dias` **borra rutinas, días y ejercicios planificados**:
el modelo cambió y se eligió clean slate a propósito (ADR-028). Se conservan usuarios,
entrenamientos, series, pesos y el catálogo.

```bash
python manage.py migrate
python manage.py seed_demo --reset   # para volver a tener datos de demostración
```

## Comandos habituales

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py shell

pytest                                       # todos los tests
pytest apps/workouts/tests/test_metrics.py   # un módulo
pytest -k injection                          # por nombre

pip-audit                                    # vulnerabilidades en dependencias
bandit -q -c pyproject.toml -r apps config   # análisis estático de seguridad
#   El `-c pyproject.toml` es necesario: sin él bandit ignora `exclude_dirs` y reporta
#   como hallazgo cada `assert` de los tests.
```

## Catálogo de ejercicios

```bash
python manage.py import_catalog --source vendor/exercises-dataset
```

Es **idempotente**: crea o actualiza por `external_id`, así que se puede volver a lanzar cuando el
dataset upstream publique ejercicios nuevos (`git -C vendor/exercises-dataset pull` primero).

Valida contra `data/exercises.schema.json`. Si el formato upstream cambia, el comando **falla
ruidosamente** en lugar de importar datos a medias — eso es intencionado.

Resultado esperado: 1324 ejercicios, con su JPG y su GIF en `media/exercises/`.

## Catálogo de métricas

```bash
python manage.py sync_metrics
```

Vuelca el registro del código (`apps/metrics/catalog/`) a la tabla `Metric`. **Hay que ejecutarlo
cada vez que se añada o se cambie una métrica.** Es idempotente.

Dos comportamientos deliberados:

- **No pisa la configuración del admin** (`is_active`, `send_to_ai`, `default_visible`). Si cada
  sincronización las reactivara, desactivar una métrica no serviría de nada.
- **Desactiva en vez de borrar** las métricas que ya no existen en el código: borrarlas arrastraría
  por cascada las preferencias de todos los usuarios que las tuvieran elegidas.

Para añadir una métrica: escribir la función con `@metric(...)` en el módulo que corresponda de
`apps/metrics/catalog/`, ejecutar `sync_metrics` y añadirle su test.

## Prompts por defecto

```bash
python manage.py seed_prompts
```

Sin esto, la primera generación falla porque no hay ninguna plantilla activa. **No sobrescribe** lo
que ya exista: si cada ejecución pisara los cambios del admin, poder editarlos no serviría de nada.
Para forzar una versión nueva, `--force`.

Los prompts por defecto llevan la instrucción que declara `<datos_usuario>` y `<peticion_usuario>`
como datos y no como órdenes. **Al editarlos desde el admin, no quites esa parte.**

## Rotar la clave de cifrado

Las API keys de los proveedores están cifradas con MultiFernet, que descifra con cualquier clave de
la lista. Eso permite rotar sin parar el servicio:

```bash
# 1. Generar la clave nueva
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# 2. Ponerla LA PRIMERA en FIELD_ENCRYPTION_KEYS, conservando la vieja:
#    FIELD_ENCRYPTION_KEYS=<nueva>,<vieja>

# 3. Reiniciar la app y re-cifrar
python manage.py rotate_encryption_key

# 4. Ya se puede quitar la vieja de la lista y reiniciar
```

El orden importa: MultiFernet **cifra con la primera** y **descifra con cualquiera**. Si se pone la
nueva al final, no se cifra nada con ella.

`rotate_encryption_key --dry-run` dice cuántos valores se re-cifrarían sin tocar nada.

> **Trampa al copiar claves desde la terminal.** Las claves Fernet son base64 y **terminan en `=`**.
> Un `cut -d= -f2` las trunca y produce un desconcertante
> `ValueError: Fernet key must be 32 url-safe base64-encoded bytes`. Usa `cut -d= -f2-`.
> Una clave válida tiene **44 caracteres**.

### Si se retiró una clave antes de rotar

No se pierde nada y **el panel sigue funcionando**: leer un valor que no se puede descifrar no
revienta, devuelve un marcador. El listado del admin muestra
`(no se pudo descifrar: vuelve a pegar la clave)` y la factoría de proveedores se niega a construir
un cliente con un mensaje explícito.

Es deliberado: si cargar la fila lanzara una excepción, el admin daría error 500 y quedarías
bloqueado sin poder entrar a arreglarlo. La regla es **leer no es fatal, usar sí**.

Para recuperarse: restaurar la clave antigua en `FIELD_ENCRYPTION_KEYS` y rotar, o simplemente
volver a pegar la API key en `/admin/`.

## Configurar la IA

1. `/admin/` → **AI provider configs** → añadir.
2. Elegir proveedor y modelo, pegar la API key, marcar `is_active`.
   Solo puede haber una activa; el modelo lo valida.
3. Usar la acción **"Probar configuración"**: hace una llamada real mínima y reporta el error
   concreto si lo hay. Es la forma de validar una key sin esperar a que falle una generación.
4. Para el RAG (solo con OpenAI): **Vector stores** → crear → acción **"Crear en OpenAI"** →
   **Knowledge documents** → subir PDFs. El estado pasa a `indexed` cuando termina el indexado.

Recordatorio: con Anthropic o Google el RAG no se usa (ADR-005). No es un fallo.

## Diagnóstico

**Una generación falla.** Mirar `/admin/` → **AI generations**: guarda el prompt renderizado, la
respuesta cruda y el error. Solo visible para staff.

**El documento se queda en `pending`.** No hay worker de Celery corriendo, o Redis está caído.
Comprobar `docker compose ps` y la terminal del worker.

**`import_catalog` falla con error de validación.** El dataset upstream cambió de formato. Comparar
`vendor/exercises-dataset/data/exercises.schema.json` con lo que espera el importador.

**La sexta generación devuelve error de límite.** Es correcto: 5/hora por usuario (ver
`.docs/06-security.md`).

**Anthropic devuelve 400.** Casi siempre es haber pasado `temperature`, `top_p` o `budget_tokens`:
`claude-opus-5` los rechaza. Ver `.docs/03-ai-config.md`.

**`FATAL: la autentificación password falló para el usuario "gym"`, con los contenedores en
`healthy`.** No es un problema de credenciales: hay **otro** PostgreSQL escuchando en ese puerto y
gana la conexión desde `localhost`. Esta máquina de desarrollo tenía servicios nativos en 5432, 5433
y 5434, y un Redis en `[::1]:6379`.

Por eso el `docker-compose.yml` publica en puertos altos:

| Servicio | Puerto en el host | Puerto dentro de Docker |
|---|---|---|
| PostgreSQL | **55432** | 5432 |
| Redis | **6380** | 6379 |

Para comprobar quién ocupa un puerto antes de cambiarlo:

```bash
netstat -ano | grep LISTENING | grep ":55432 "
```

Si aparecen **dos** PID para el mismo puerto, uno es el proxy de Docker y el otro un servicio nativo:
el que se enlazó primero gana. Cambia el puerto del host en `docker-compose.yml` y en `DATABASE_URL`.

Para confirmar que el contenedor sí está bien por dentro:

```bash
docker compose exec db psql -U gym -d gym -c "select current_user, current_database();"
```

`REDIS_URL` usa `127.0.0.1` y no `localhost` a propósito: `localhost` puede resolver a `::1` primero
y acabar hablando con un Redis distinto.

## De `dev` a `main` (ADR-059)

Se trabaja y se empuja a **`dev`**. Cada push lanza `promover.yml`: el CI completo y, si pasa, un PR
`dev → main` que el propio workflow fusiona. `main` es lo que despliega Railway.

- **Una vez, en GitHub:** Settings → Actions → General → Workflow permissions → marcar *Allow
  GitHub Actions to create and approve pull requests*. Sin eso el job `promover` falla al abrir el
  PR, con un mensaje que lo dice.
- **No empujar a `main` a mano.** Separa las ramas y la siguiente promoción puede chocar. Si ya ha
  pasado: `git checkout dev && git merge origin/main`, resolver, empujar `dev`.
- Si el CI falla, no se promueve nada: se arregla en `dev` y se vuelve a empujar.

## En casa (Tailscale, ADR-070)

La aplicación corre en tu PC con Docker y el teléfono entra por `https://<pc>.<tailnet>.ts.net`.
Cuesta $0 y solo tus dispositivos llegan a ella. Es independiente del `docker-compose.yml` de
desarrollo, que tiene otro proyecto, otros volúmenes y otros puertos.

```text
teléfono ──HTTPS (tailnet)──▶ tailscale serve ──▶ 127.0.0.1:8080 caddy ─┬─ /media/ → volumen
                                                                         └─ web (gunicorn)
                          worker · beat · postgres · redis  (sin puertos publicados)
```

### Una vez

1. **Tailscale** en el PC y en el teléfono, con la misma cuenta (<https://tailscale.com/download>).
2. En la consola de Tailscale:
   - **DNS**: activar *MagicDNS* y *HTTPS Certificates*.
   - **Machines**: renombrar el PC (por ejemplo, `gym`) y, en su menú, **Disable key expiry**.
     Sin eso, cada 180 días hay que volver a iniciar sesión en el PC.
3. El catálogo en `vendor/exercises-dataset` (ver «Catálogo de ejercicios»).
4. Desde Git Bash, en la raíz del repositorio:

   ```bash
   sh scripts/casa.sh certificado    # solo si un antivirus inspecciona el HTTPS (ver abajo)
   sh scripts/casa.sh preparar gym.<tu-tailnet>.ts.net tu@correo.com   # el correo, para el push
   sh scripts/casa.sh subir          # construye la imagen y arranca los 6 contenedores
   sh scripts/casa.sh catalogo       # import_catalog + sync_metrics + seed_prompts
   sh scripts/casa.sh admin          # tu cuenta (es staff: ve la gestión)
   tailscale serve --bg http://127.0.0.1:8080
   ```

   `preparar` genera los secretos dentro de la imagen y los escribe en `despliegue/casa/.env`
   (ignorado por git) sin enseñarlos. Sin correo no hay avisos push, y todo lo demás funciona.
5. **Guarda una copia de `despliegue/casa/.env` fuera del PC.** Sin las `FIELD_ENCRYPTION_KEYS`
   que contiene, las claves de IA de un respaldo no se descifran.
6. En Windows:
   - Docker Desktop → Settings → General → *Start Docker Desktop when you sign in*. Los
     contenedores vuelven solos (`restart: unless-stopped`).
   - Configuración → Sistema → Energía: que **no se suspenda** enchufado. Un PC dormido es una
     aplicación caída.
   - `tailscale serve --bg` recuerda la configuración entre reinicios.
7. En el teléfono, con Tailscale conectado, abre la URL y entra. Para tenerla como aplicación:
   - **iPhone:** Safari → Compartir → *Añadir a pantalla de inicio*. Hace falta para el aviso push.
   - **Android:** Chrome → *Instalar aplicación*.
8. En la aplicación, **Gestión → IA**: la clave del proveedor y el modelo.

### Día a día

| Para | Orden |
|---|---|
| Ver si está todo arriba | `sh scripts/casa.sh estado` |
| Ver qué pasa | `sh scripts/casa.sh logs` (o `logs web`, `logs worker`) |
| Actualizar tras un `git pull` | `sh scripts/casa.sh subir`, que reconstruye y migra al arrancar |
| Parar | `sh scripts/casa.sh parar` (los datos se quedan en los volúmenes) |
| Respaldar la base de datos | `sh scripts/casa.sh respaldo` → `respaldos/gym-<fecha>.sql.gz`, conserva 14 |
| Respaldar fotos y documentos subidos | `sh scripts/casa.sh respaldo-media`, conserva 2 |
| Volver a un respaldo | `sh scripts/casa.sh restaurar respaldos/gym-<fecha>.sql.gz` (pide confirmación) |

**Respaldos automáticos:** Programador de tareas de Windows → *Crear tarea básica* → diaria →
programa `C:\Program Files\Git\bin\bash.exe`, argumentos `scripts/casa.sh respaldo` e *Iniciar
en* la carpeta del repositorio. La carpeta `respaldos/` está en el mismo disco: cópiala de vez en
cuando a otro sitio.

### Si algo falla

- **«certificate verify failed» / «unable to get local issuer certificate»** al construir, o la
  IA y el push fallan con errores SSL. Un antivirus o un proxy inspecciona el HTTPS y firma con
  una raíz que solo conoce Windows. En el PC donde se montó esto es **Norton** («Norton Web/Mail
  Shield Root»), y es también la razón por la que `pip-audit` falla en local.
  `sh scripts/casa.sh certificado` mira quién firma pypi.org, exporta esa raíz del almacén de
  Windows a `despliegue/casa/certificados/` (ignorado por git) y la imagen confía en ella al
  construir y en marcha. La alternativa es excluir Docker del análisis SSL del antivirus.
- **El teléfono no abre la URL.** Comprueba que Tailscale está conectado en los dos y que
  `tailscale serve status` muestra el proxy a `127.0.0.1:8080`. El primer acceso tarda unos
  segundos mientras se emite el certificado.
- **400 Bad Request.** El nombre del PC no coincide con `ALLOWED_HOSTS` del `.env`, por ejemplo
  porque lo renombraste después. Corrige `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` y `SITE_URL`, y
  vuelve a ejecutar `subir`.
- **Redirecciones en bucle.** Algo entre Tailscale y Django está quitando `X-Forwarded-Proto`. El
  `Caddyfile` tiene que conservar `trusted_proxies static private_ranges`.
- **`web` no pasa a *healthy*.** `sh scripts/casa.sh logs web`. Lo habitual es una variable que
  falta en el `.env`: `prod.py` no arranca a medias a propósito.
- **¿Cuánta RAM gasta?** Medido el 2026-11-03: unos **845 MB** los seis contenedores (web
  327 MB, worker 287, beat 168, Postgres 44, Caddy 15, Redis 6), más unos 750 MB de Docker
  Desktop y 125 MB de Tailscale en Windows.
  - El worker va con `--concurrency=2`. Sin él, Celery arranca un proceso por núcleo: 16 y
    1,6 GB en este PC.
  - La máquina virtual de Docker (`vmmemWSL`) tiene un **tope de 3 GB** en
    `%USERPROFILE%\.wslconfig` (`memory=3GB`, `autoMemoryReclaim=dropCache`). En reposo se queda
    en unos **2,1 GB**: sube al construir la imagen o al arrancar, y devuelve la caché a Windows
    tras un par de minutos sin actividad.
  - Para cambiar el tope: editar el archivo, cerrar Docker Desktop, `wsl --shutdown` y volver a
    abrir Docker Desktop. Los contenedores vuelven solos.
  - Si un `casa.sh subir` se queda corto de memoria, hay que subir el tope a 4 GB.
- **Probarlo sin Tailscale**, desde el propio PC:
  `curl -H "Host: <tu-host>" -H "X-Forwarded-Proto: https" http://127.0.0.1:8080/entrar/`.

## Despliegue (Railway)

Tres servicios desde el **mismo repositorio**, cada uno con su comando de arranque del `Procfile`:

| Servicio | Comando | Notas |
|---|---|---|
| `web` | `sh scripts/start-web.sh` | Migra, recolecta estáticos y arranca gunicorn. Ver abajo. |
| `worker` | `celery -A config worker -l info` | Sin esto la IA no procesa nada en segundo plano. |
| `beat` | `celery -A config beat -l info` | Sin esto no se dispara el análisis de progreso programado. |

En Railway: crear el proyecto desde el repo, y por cada fila de la tabla un **servicio nuevo**
apuntando al mismo repo, con ese comando como *Custom Start Command* (Railway detecta el `Procfile`
automáticamente para el primero; los otros dos hay que darlos de alta a mano con el comando).

### Construcción de React: Railpack y Nixpacks

Railway debe construir desde la **raíz del repositorio**, con `railway.toml` como archivo de
configuración. Este fija el builder `RAILPACK` y `sh scripts/build-frontend.sh` como Build Command.
`railpack.json` añade Node 22 al proveedor Python. No necesita un servicio separado para React.
El script instala también devDependencies aunque `NODE_ENV=production`, construye Vite y verifica
que el manifiesto y todos sus archivos existen. `nixpacks.toml` queda para plataformas Nixpacks.

En el servicio web, conservar **Start Command: `sh scripts/start-web.sh`**. Worker y beat conservan
sus propios comandos de la tabla. No poner `VITE_DEV_SERVER_URL` en producción. Si hay un
`RAILPACK_CONFIG_FILE` o una ruta de configuración Railway personalizados, deben apuntar a los
archivos nuevos; revisar estos ajustes si no aparecen los comandos del script en el build log.

Si aparece `No existe el manifiesto de Vite en /app/frontend/dist/.vite/manifest.json`, la imagen
no contiene el frontend. Subir estos archivos y **desplegar el commit nuevo**; reiniciar o volver
a desplegar la imagen antigua no basta. El build y el arranque deben imprimir
`Frontend verificado: manifiesto y archivos de Vite presentes.` antes de servir tráfico.
`collectstatic` por sí solo no demuestra que React se haya construido. Ver ADR-052.

### Variables de entorno obligatorias

Las mismas que en `.env.example`, más:

```
DJANGO_SETTINGS_MODULE=config.settings.prod
ALLOWED_HOSTS=tu-dominio.up.railway.app
CSRF_TRUSTED_ORIGINS=https://tu-dominio.up.railway.app
R2_ACCESS_KEY_ID=…
R2_SECRET_ACCESS_KEY=…
R2_BUCKET_NAME=…
R2_ENDPOINT_URL=https://<account_id>.r2.cloudflarestorage.com
R2_PUBLIC_DOMAIN=pub-…-.r2.dev
# Opcionales: sin ellas no hay avisos push de descanso (ADR-066). Las tres o ninguna.
VAPID_PUBLIC_KEY=…
VAPID_PRIVATE_KEY=…
VAPID_SUBJECT=mailto:…
```

`DATABASE_URL` y `REDIS_URL` los rellena Railway solo si añades sus plugins de Postgres y Redis al
proyecto — no hay que teclearlos. **`DJANGO_SETTINGS_MODULE` sí hay que ponerla**: `manage.py`
usa `config.settings.dev` por defecto (léase: sin `SECURE_SSL_REDIRECT`, sin cookies seguras, sin
exigir `ALLOWED_HOSTS`), y ese default solo queda pisado en el proceso web porque `config/wsgi.py`
lo fija a mano. Cualquier comando suelto ejecutado en el shell del contenedor arrancaría con `dev`
si la variable no está puesta a nivel de proyecto.

Las `R2_*` salen del dashboard de Cloudflare → R2 → crear un bucket → *Manage API Tokens* →
token con lectura/escritura sobre ese bucket. **Hay que habilitar el acceso público del bucket**
(o conectarle un dominio propio) para tener un `R2_PUBLIC_DOMAIN`: sin acceso público, las
imágenes seguirían dando error aunque el resto esté bien configurado.

### El primer despliegue, en orden

Desde el shell del contenedor (Railway → servicio `web` → *Shell*; ojo, esta imagen **no trae
`git`**, así que si `vendor/exercises-dataset` no está ya en el contenedor, bájalo con Python en
vez de `git clone`):

**Antes de nada**, comprueba que el shell tiene los settings de producción — no los hereda del
script de arranque (ver más abajo), y sin ellos `import_catalog` sube las imágenes al disco efímero:

```bash
echo "$DJANGO_SETTINGS_MODULE"      # tiene que decir config.settings.prod
export DJANGO_SETTINGS_MODULE=config.settings.prod   # si salió vacío
```

```bash
python manage.py migrate            # el script de arranque ya lo hace, pero el primero
                                     # conviene verlo a mano
python manage.py createsuperuser
python manage.py import_catalog --source vendor/exercises-dataset
python manage.py sync_metrics
python manage.py seed_prompts
```

Sin `seed_prompts`, la primera generación de rutina falla con «no hay ninguna plantilla activa».

### `media/` vive en Cloudflare R2, no en el contenedor

El disco de una PaaS como Railway es efímero: **cada redeploy lo borra**. Se probó primero con un
*Volume* de Railway, y funcionaba, pero tiene un límite que no vale la pena aceptar de entrada:
un Volume solo se monta en **una** instancia, así que el día que el servicio `web` tenga más de
una réplica deja de servir. R2 no tiene ese límite —y de paso no cobra por salida de datos, y sirve
las imágenes directo desde su CDN sin pasar por gunicorn— así que se migró ahí en vez de quedarse
con el Volume. Ver ADR-041.

`import_catalog` sube los archivos a través de `default_storage`, no escribiendo directo al disco:
por eso funciona igual en desarrollo (disco local) que en producción (R2) sin ninguna bandera que
elegir. Si el dataset cambia, correr `import_catalog` otra vez sube solo lo que falte —los nombres
son deterministas por `external_id`, así que no deja duplicados en el bucket.

### El shell de Railway NO hereda los settings de producción

El más caro de los tres fallos de este bloque, y el que menos lo parece.

`scripts/start-web.sh` hace `export DJANGO_SETTINGS_MODULE=config.settings.prod`, pero **ese export
vive solo dentro de ese proceso**. Al abrir el *Shell* del servicio se entra en un shell nuevo donde
la variable no está, y `manage.py` cae a su valor por defecto: `config.settings.dev`.

Correr ahí `python manage.py import_catalog` escribe las 1324 imágenes en el **disco efímero del
contenedor** en vez del bucket. El comando termina con «1324 actualizados» tan tranquilo, la base de
datos queda con las rutas correctas, y la aplicación sirve un **404 por cada imagen** porque en R2
no hay nada. La causa queda a un despliegue de distancia del síntoma.

Dos cosas lo evitan:

1. **Poner `DJANGO_SETTINGS_MODULE=config.settings.prod` como variable del servicio en Railway.** Es
   la solución de fondo: la heredan el web, el worker, el beat y el shell. Los `env` del `Procfile`
   quedan redundantes pero no estorban.
2. **`import_catalog` anuncia el destino antes de subir nada.** La primera línea dice
   `Los archivos van a: bucket «…» (https://pub-….r2.dev)` o `disco local, /app/media`. Si dice
   disco local en producción, hay que parar ahí.

Si ya pasó: relanza con los settings puestos delante del comando.

```bash
DJANGO_SETTINGS_MODULE=config.settings.prod \
  python manage.py import_catalog --source vendor/exercises-dataset
```

### La CSP tiene que permitir el dominio del bucket

Con `media/` en R2, las imágenes **dejan de ser del propio origen**: salen de
`https://<R2_PUBLIC_DOMAIN>/exercises/…`. `base.py` declara `img-src: 'self' data:`, así que sin
añadir ese dominio el navegador **bloquea las 1324 imágenes del catálogo**.

Es un fallo con muy mala pinta de diagnosticar: la aplicación responde 200 a todo, el HTML trae la
`<img>` con su `src` correcto, el archivo está en el bucket y se abre pegando la URL en el
navegador — y aun así no se ve ninguna imagen. La pista está solo en la consola del navegador,
como `Refused to load the image … because it violates the following Content Security Policy`.

Lo resuelve `config/settings/prod.py`, que rehace `CONTENT_SECURITY_POLICY` añadiendo
`https://{AWS_S3_CUSTOM_DOMAIN}` a `img-src`. **Copiando los tres niveles del diccionario, no
mutándolos**: `from .base import *` los deja apuntando al mismo objeto que `base.py` y un
`.append()` metería el dominio de R2 también en la CSP de desarrollo y de los tests. Lo comprueban
dos tests en `apps/common/tests/test_deploy.py`.

Si se cambia el dominio del bucket —por ejemplo al pasar del subdominio `r2.dev` a uno propio—
basta con cambiar `R2_PUBLIC_DOMAIN`: la CSP se arma a partir de esa variable.

**`R2_PUBLIC_DOMAIN` es un host, no una URL.** Los dos errores que se cometen con ella dan el mismo
síntoma —ninguna imagen— y `prod.py` los rechaza al arrancar en vez de tragárselos:

| Se pone | Qué pasa |
|---|---|
| `https://pub-abc.r2.dev` | django-storages le añade el esquema y sale `https://https://…`; el navegador descarta **toda** la fuente de la CSP con «contains an invalid source» |
| `<account_id>.r2.cloudflarestorage.com` | es el endpoint de la **API**, que exige peticiones firmadas: cada imagen daría 401 |
| `pub-abc.r2.dev` | correcto |

Que el endpoint y el dominio público se parezcan tanto es justo lo que hace fácil confundirlos: el
primero sale en *Settings → S3 API* y el segundo en *Settings → Public Development URL*, y hay que
pulsar **Enable** en el segundo para que exista.

### Por qué las imágenes del catálogo daban 404 aunque el archivo existiera

`config/urls.py` sirve `media/` con `static()`, pero **solo si `DEBUG=True`** — es la recomendación
oficial de Django, que no está pensada para producción. En `config/settings/prod.py` no había
ningún urlpattern equivalente, y el fallo **no se ve en desarrollo** porque ahí `DEBUG=True` lo
tapa. Con R2 el problema desaparece de otra forma: las imágenes ya no viven en absoluto en el disco
del contenedor, así que no hay ningún urlpattern que necesiten — `ImageField.url` apunta
directamente al dominio público del bucket.

### El timeout de gunicorn

`generate_routine()` llama al proveedor de IA **dentro** de la petición HTTP, con hasta tres
intentos. `scripts/start-web.sh` arranca gunicorn con `--timeout 120`; si se cambia el número de
intentos o el proveedor tarda más, hay que revisar este valor junto con `MAX_ATTEMPTS`.

## Al hacer un cambio estructural

Añadir una entrada en `.docs/01-decisions.md`, sin reescribir las antiguas (ver `.docs/07-reglas.md`).
