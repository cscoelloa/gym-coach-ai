# Registro de decisiones

Formato ADR ligero: **Contexto → Decisión → Consecuencias**.

Las entradas antiguas **no se reescriben**. Si una decisión se revierte, se marca como
`SUSTITUIDA por ADR-NNN` y se añade una entrada nueva. El valor de este archivo está en poder
reconstruir por qué el proyecto es como es, incluidos los caminos que se descartaron.

---

## ADR-073 — El código va sin comentarios; el porqué vive en la documentación
**Fecha:** 2026-11-03 · **Estado:** aceptada · **Sustituye a ADR-021**

**Contexto.** El código acumulaba unas 4.800 líneas de comentarios y docstrings. Explicaban el
porqué de casi todo, con historia, anécdotas y alguna mención al usuario o a su PC. Al publicarlo
como repositorio abierto, el usuario pidió quitarlos **todos**. Se le ofrecieron dos alternativas,
acortarlos o quitar solo lo personal, y eligió quitarlos.

**Decisión.**

- **Ni comentarios ni docstrings** en Python, TypeScript/JSX, JavaScript, CSS, la plantilla de
  Django, shell, Dockerfile, Caddyfile, YAML, TOML, requirements y archivos de ignorar.
- **Se conservan solo los que hacen algo:**
  - los de las herramientas: `# noqa`, `# nosec`, `# type: ignore`, `// @ts-expect-error` y las
    directivas `/// <reference>`;
  - los shebang de los scripts;
  - la marca **`/*__CONFIG__*/`** de `apps/common/sw.js`, que `apps/common/pwa.py` sustituye por la
    configuración del build. Al quitarla, `test_pwa` falló en cinco tests: es un comentario que el
    código lee.
- **El porqué está en `.docs/`:** las decisiones en este registro, las reglas en `07-reglas.md` y
  la operación en el runbook.
- **No se tocan** los dos `.env` de ejemplo (`.env.example` y `despliegue/casa/env.ejemplo`): no
  son código, sino la documentación de cada variable, y el README remite a ellos.
- **`casa.sh`** imprimía su cabecera de comentarios como ayuda. Ahora la ayuda es un texto dentro
  del propio script.

**Cómo se comprobó que el programa no cambió:**

- **Python:** por archivo, el AST del resultado es idéntico al original sin sus cadenas-sentencia.
- **TypeScript/JSX/JS:** por archivo, el código reimpreso sin comentarios (con el compilador de
  TypeScript) es idéntico antes y después. Los comentarios se localizan como trivia del
  compilador, así que un `//` dentro de un texto o de JSX no se confunde.
- **El bundle de Vite:** el JS sale idéntico salvo los hashes de los nombres. El CSS pierde dos
  utilidades, `grid-cols-3` y `lg:grid`, que Tailwind generaba solo porque aparecían en
  comentarios; nada las usa.
- **Docker Compose:** la configuración resuelta es idéntica, tanto la de casa como la de
  desarrollo.
- Además pasan pytest, vitest, `tsc`, ruff y la validación de los YAML y TOML.

**Consecuencias.** El código es más corto y no arrastra historia, pero ya no se explica solo. El
porqué de una pieza rara hay que buscarlo en su ADR (`git log -S` ayuda a encontrarlo).

- **Lo nuevo se escribe sin comentarios.** Si algo necesita explicación, va a un ADR o a la
  documentación.
- Un comentario que el código lee, como `/*__CONFIG__*/`, necesita un test que falle si
  desaparece.

---

## ADR-071 — Las confirmaciones se van solas; los errores se quedan
**Fecha:** 2026-11-03 · **Estado:** aceptada

**Contexto.** El usuario, ya usando la aplicación en su iPhone, vio que las confirmaciones
«aparecen pero no desaparecen». Las ocho se pintaban con `mutation.isSuccess`, que sigue verdadero
hasta la siguiente mutación: «Peso registrado.» se quedaba en la pantalla para siempre, y al
volver a guardar no se notaba que había pasado algo nuevo.

Los ocho sitios eran Peso, Perfil, el editor de rutinas, las notas del cierre, y en la gestión de
la IA los prompts, la programación, la prueba del proveedor y la subida de documentos.

**Decisión.**

- **`ds/AvisoPasajero.tsx`** pinta el `Aviso` cuando cambia su `marca` y lo quita a los
  `duracion` ms. Su hook, `useUnRato`, sirve para las confirmaciones en línea («Guardado.» junto a
  un botón).
- **La marca es `mutation.isSuccess && mutation.submittedAt`**, que es distinta en cada envío: dos
  guardados seguidos vuelven a enseñar el aviso y reinician el tiempo.
- Si arranca otro envío, la confirmación vieja se quita en el mismo render: no puede convivir con
  «Guardando…».
- **4 s** para un «hecho». **10 s** para lo que trae algo que leer: la prueba del proveedor
  (latencia y tokens) y «Subido. El indexado va aparte…».
- Se desvanece al final (`aviso-pasajero`). Con «menos movimiento», desaparece sin animación.
- **Los errores no se tocan.** Siguen hasta que se corrigen: uno que se fuera solo dejaría a
  alguien sin saber por qué no se guardó.

**Consecuencias.** Es un `role="status"`: el lector de pantalla lo anuncia al aparecer, y que se
vaya después no quita nada que haga falta. El editor guarda `exitoEn` (una marca de tiempo) en
vez de un `exito` booleano. Una confirmación nueva se escribe con `AvisoPasajero`, no con
`{isSuccess && <Aviso>}`.

---

## ADR-072 — Las hojas abren con el foco en su título
**Fecha:** 2026-11-03 · **Estado:** aceptada · **Matiza ADR-051**

**Contexto.** En la captura del iPhone, la hoja «Organizar el día» se abría con un anillo azul
alrededor de la ✕. `showModal()` le da el foco al primer control, y el navegador lo trata como foco
de teclado aunque la hoja se haya abierto con el dedo. En la misma hoja:

- **«Guardar» y «Cancelar» salían con anchos distintos**, con un hueco a la derecha;
- **el estado vacío iba pegado a la lista**;
- **el día salía dos veces**, y más grande dentro que en el título.

**Decisión.**

- **`Panel` enfoca `[data-autofocus]` si existe y, si no, su título** (`<h2 tabIndex={-1}>`, sin
  anillo). El lector de pantalla anuncia el título y Enter no dispara ningún botón. Por eso
  `Confirmacion` ya no enfoca «Cancelar»: el título protege igual de una confirmación por
  accidente. El buscador de ejercicios conserva su `data-autofocus`.
- **Las acciones de una hoja se reparten la fila a partes iguales** (`flex: 1 1 0; min-width:
  fit-content`). Una etiqueta que no cabe baja a su propia línea en vez de partirse.
- **El día va en el título de la hoja** («Organizar el lunes»).
- **Sin rutinas, la hoja solo ofrece crear una**: ni radio ni «Guardar».

**Consecuencias.** La auditoría de dimensiones (que se ejecuta desde el temporal de la sesión)
añade dos comprobaciones: superficies pegadas a menos de 4 px y acciones desiguales dentro de una
hoja.

---

## ADR-070 — Alojamiento en casa: Docker en el PC del usuario, detrás de Tailscale
**Fecha:** 2026-11-03 · **Estado:** aceptada · **Convive con ADR-041 y ADR-052** (Railway sigue
documentado y funcionando)

**Contexto.** El usuario quiere usar la aplicación desde el teléfono, fuera de casa, pero **la va
a usar él solo**, y el precio de un servidor es el problema. Se investigó (noviembre de 2026):

- **Railway:** el plan Hobby cuesta $5 al mes con $5 de uso incluidos. Web, worker, beat, Postgres
  y Redis salen por unos $5–7 incluso con el modo *Serverless*, porque el worker de Celery consulta
  Redis sin parar y no se duerme nunca.
- **Render:** el Postgres gratuito se borra a los 30 días y no hay workers gratuitos.
- **Fly.io:** ya no tiene plan gratuito para cuentas nuevas.
- **Hetzner:** subió los precios dos veces en 2026 y no admite servidores nuevos.
- **Oracle Always Free:** recortó su plan a la mitad sin avisar y **reclama las VM ociosas**
  (CPU por debajo del 20 % durante 7 días), que es justo lo que es una aplicación con un usuario.

Se planteó también **separar el frontend y el backend en dos servidores**, y se descartó.

- Con dominios distintos, **Safari bloquea todas las cookies de terceros** (ITP, desde 2020),
  también con `SameSite=None; Secure`. La sesión `HttpOnly` de ADR-046 no llegaría a la API, y la
  PWA en el iPhone dejaría de funcionar.
- Las variantes que sí funcionan (subdominios del mismo dominio, o un proxy `/api` en el
  frontend) obligan a rehacer la cáscara, el service worker, la CSP, CORS y CSRF, y no ahorran
  nada: la API, el worker y la base de datos siguen costando lo mismo.

**Decisión.** La aplicación corre en el PC del usuario con Docker y se llega a ella por
**Tailscale Serve**, cuyo plan Personal es gratuito.

- **`Dockerfile`** de dos etapas: Node construye el bundle y Python 3.11 lo sirve con usuario sin
  privilegios. La web arranca con el mismo `scripts/start-web.sh` que Railway.
- **`despliegue/casa/compose.yml`**:
  - Postgres, Redis, web, worker, beat y Caddy.
  - **Postgres y Redis no publican puertos.**
  - **Caddy solo escucha en `127.0.0.1`.**
  - Todo con `restart: unless-stopped`.
- **`MEDIA_STORAGE=disco`** (nuevo en `prod.py`, `r2` por defecto). `media/` vive en un volumen y
  Caddy lo sirve desde el propio origen, así que la CSP no cambia.
- **Caddy confía en las cabeceras de Tailscale** (`trusted_proxies private_ranges`).
  `tailscale serve` termina el TLS, conserva el `Host` y añade `X-Forwarded-Proto: https`; se
  comprobó en su código (`ipn/ipnlocal/serve.go`). Con eso funciona `SECURE_PROXY_SSL_HEADER` sin
  que Caddy tenga que inventar la cabecera.
- **`scripts/casa.sh`** lo envuelve todo:
  - `preparar` genera el `.env` dentro de la imagen, sin que los secretos pasen por la pantalla;
  - `subir`, `catalogo`, `admin`, `respaldo` y `restaurar`.

**Consecuencias.**

- **$0 al mes.** Lo único que se paga es el uso de la API de IA.
- **Los datos de salud no salen a internet.** Solo llegan los dispositivos de la tailnet, y
  Postgres no está ni en la red de casa. Con un único usuario, además, dejan de ser urgentes la
  licencia comercial de Gym Visual (`NOTICE.md`) y el consentimiento de la LOPDP: no hay datos de
  terceros y no se publica como producto. **Si algún día se abre a más gente, se vuelven
  bloqueantes.**
- **El PC tiene que estar encendido** cuando se entrena: sin suspensión y con Docker Desktop
  arrancando al iniciar sesión. Si eso deja de ser aceptable, el camino es Railway, que sigue
  intacto.
- **El teléfono necesita la app de Tailscale.** La PWA se instala sobre `https://<pc>.<tailnet>.ts.net`,
  que lleva un certificado de Let's Encrypt; los avisos push salen hacia los servicios de Apple y
  Google y no necesitan entrar.
- **Norton inspecciona el HTTPS en este PC** y firma con una raíz que los contenedores no
  conocen: `pip`, `npm`, la IA y el push fallaban con «unable to get local issuer
  certificate». La imagen acepta raíces de más desde `despliegue/casa/certificados/` (las
  exporta `casa.sh certificado`) y todo el Python lee el almacén del sistema (`SSL_CERT_FILE`,
  `REQUESTS_CA_BUNDLE`, `PIP_CERT`) en vez del `certifi` de cada librería.
- **Los respaldos son responsabilidad del usuario**: `casa.sh respaldo` más una copia del `.env`
  fuera del PC. Sin las `FIELD_ENCRYPTION_KEYS`, las claves de IA de un respaldo no se descifran.
- Railway queda como está: `MEDIA_STORAGE` vale `r2` si no se pone, y un valor desconocido no
  arranca. Así no hay forma de caer en silencio al disco efímero de una PaaS.

---

## ADR-069 — El frontend, por módulos de funcionalidad; cada pantalla solo compone
**Fecha:** 2026-11-02 · **Estado:** aceptada · **Matiza ADR-047 y ADR-064**

**Contexto.** El usuario pidió hacer modular el frontend y mejorar la composición. El código estaba
organizado por capas técnicas, y eso dejaba tres problemas:

- **`pantallas/` era una carpeta plana** con más de treinta archivos: pantallas, hooks y
  subcomponentes mezclados. `api/` tenía la API de cada área lejos de sus pantallas, y `gestion/`
  era otra capa aparte.
- **`App.tsx` declaraba treinta rutas a mano.** Era el tercer sitio de «añadir una pantalla», y
  ningún test lo vigilaba: olvidarlo dejaba la pantalla en blanco.
- **Archivos grandes con varias responsabilidades:**

  | Archivo | Líneas |
  |---|---|
  | La gestión de la IA | 840 |
  | La guía de estilos | 659 |
  | El modo foco | 602 |
  | Progreso | 396 |
  | El editor de rutinas | 362 |
  | Perfil | 359 |
  | Peso | 334 |

**Decisión.**

1. **`modulos/<funcionalidad>/`**: inicio, entrenar, plan, ejercicios, progreso, peso, perfil, ia,
   notificaciones, acceso, gestion y estilos.
   - Cada módulo tiene su `api.ts`, sus pantallas, sus piezas y sus tests al lado.
   - Se movieron con `git mv`: el historial de cada archivo se conserva.

2. **Tres capas compartidas.**
   - `ds/`: el sistema de diseño, con los estados de carga y error (`ds/estados.tsx`) y la
     paginación común.
   - `lib/`: la infraestructura.
   - `api/`: solo lo transversal, que son el cliente, los tipos, la sesión, los avisos sin leer y
     el mapa corporal.

   **`ds/` y `lib/` nunca importan de un módulo.** Los tipos que pinta un componente de `ds/` (el
   calendario, la configuración de series, las opciones de filtro) viven en ese componente, y la
   API del módulo los reexporta. Es el mismo criterio que ya seguían las gráficas.

3. **La puerta de un módulo es su `index.ts`.**
   - Exporta las rutas del módulo y lo que comparte con otros. Por ejemplo, lo que toca hoy, que
     Inicio comparte con Entrenar.
   - Entre módulos solo se importa a través de `index.ts` o de `api.ts`, nunca de un archivo
     interno.

4. **Cada módulo declara sus rutas** (`RutaDeModulo` en `modulos/tipos.ts`): URL, pantalla y
   acceso (`publica`, `privada`, `foco` o `staff`).
   - `modulos/index.ts` las reúne, y `App.tsx` solo las compone con su guarda.
   - **`modulos/rutas.test.ts` las compara con `RUTAS_DE_LA_SPA`.** Con `test_rutas_de_la_spa.py`,
     los tres sitios de añadir una pantalla quedan vigilados.

5. **Gestión, IA y estilos se descargan al abrirlos** (`perezosa`, en un trozo por módulo).
   - Son 73 kB menos en el bundle principal.
   - El service worker precarga esos trozos igual que el resto (ADR-063), así que siguen abriendo
     sin red.
   - El marco de gestión lo pone su propio módulo, para no arrastrarlo al bundle de todos.

6. **Una pantalla solo compone.**
   - Cada zona es un componente de la carpeta del módulo. Por ejemplo, el modo foco se reparte en
     `AvanceDelEntreno`, `TarjetaDelEjercicio`, `SeriesDelEjercicio`, `BarraDeRegistrar` y sus
     hojas.
   - Los hooks controladores de ADR-064 exportan su tipo (`Entreno`, `ControlDelEditor`) para que
     las piezas los reciban tipados.
   - El contenido de cada pestaña es un panel (`PanelDe…`) o una sección (`Seccion…`) que recibe
     el estado por props. El estado sigue en la pantalla: así, en Perfil, lo cambiado se conserva
     al pasar de una pestaña a otra.

**Consecuencias.**
- **Los archivos grandes quedan así:**

  | Archivo | Antes | Ahora | Lo que salió |
  |---|---|---|---|
  | La gestión de la IA | 840 | 50 | un archivo por zona |
  | El modo foco | 602 | 107 | |
  | El editor | 362 | 204 | |
  | Progreso | 396 | 108 | |
  | Perfil | 359 | 160 | |
  | Peso | 334 | 95 | |
  | La guía de estilos | 659 | 51 | cinco grupos |

  El test que probaba tres pantallas de entrenar pasa a uno junto a cada pantalla.
- **Añadir una pantalla:** declararla en el `index.ts` de su módulo, en `config/urls.py` y en
  `rutas.ts`. Los dos tests avisan si falta alguno.
- Los ADR antiguos citan rutas como `pantallas/useEntrenar.ts`. Son historia y no se reescriben:
  el archivo vive ahora en `modulos/entrenar/foco/`.

---

## ADR-068 — La barra lateral es un carril entre 1024 y 1279 px
**Fecha:** 2026-10-31 · **Estado:** aceptada · **Matiza ADR-062**

**Contexto.** Desde `lg` la barra lateral medía 256 px fijos. Entre 1024 y 1279 px —un portátil
pequeño o una tableta en horizontal— dejaba el contenido en unos 690 px, menos que una tableta en
vertical, y las composiciones de dos columnas de los bloques B, C y E no cabían.

**Decisión.**
- De `lg` a `xl`, la lateral es un **carril de 80 px**: cada destino es su icono con la palabra
  debajo, como en la barra de pestañas. La palabra no se quita nunca. La marca deja solo la
  placa, y el título del grupo pasa a ser solo para el lector de pantalla.
- Desde `xl` vuelve la lateral completa, de 256 px.
- Es la variante `carril` de `app.css` (`@custom-variant`, `min-width: 64rem` y
  `max-width: 79.98rem`), aplicada con la utilidad `side-rail`. Los enlaces son los mismos y con
  los mismos nombres accesibles: `AppShell.test.tsx` no cambia.

**Consecuencias.**
- A 1100 px el contenido pasa de unos 690 a unos 870 px.
- En ese ancho van en dos columnas Entrenar (lo de hoy a la izquierda, fijo, y el diario a la
  derecha), el cierre (lo que pasó y lo que queda), el modo foco y la ficha.
- Inicio va en tres columnas desde `xl`.

---

## ADR-067 — Las pantallas largas se separan en pestañas, con la vista en la URL
**Fecha:** 2026-10-30 · **Estado:** aceptada · **Matiza ADR-043**

**Contexto.** El usuario vio las pantallas «muy simples» y largas, con tablas y secciones apiladas
en una misma pantalla que había que recorrer a base de desplazarse. Tenía razón en cinco sitios:

- **Progreso** apilaba el calendario, el peso, el mapa corporal, los días de la semana y las
  métricas.
- **Peso** ponía el historial debajo de todo, y el historial crecía sin fin.
- **Perfil** obligaba a recorrer veintiocho materiales para llegar a la altura.
- **El análisis de la IA** eran cinco tarjetas con dos tablas en medio.
- **La auditoría** abría el detalle debajo de toda la tabla.

Ninguno de esos bloques se mira a la vez que los otros.

**Decisión.**

1. **`ds/Pestanas.tsx`, con el ARIA de un tablist.**
   - `role="tab"` con `aria-selected`, y un `tabpanel` etiquetado por su pestaña.
   - Flechas, Inicio y Fin; solo la pestaña activa está en el orden de tabulación.
   - Tiene el aspecto del control segmentado de iOS. `SegmentedControl` sigue siendo para
     filtros y ajustes, que no enseñan un panel.

2. **La vista activa va en la URL** (`useVista`, `?vista=`; `?zona=` en la IA de gestión).
   - Con `replace`: cambiar de pestaña no es navegar, y «atrás» sale de la pantalla.
   - La primera vista no se escribe, para que la URL limpia siga siendo la de siempre.
   - Así un enlace lleva a una pestaña concreta: «Guardar mi panel» vuelve a
     `/progreso/?vista=metricas`, y el resumen de gestión abre los documentos del RAG. Recargar
     no devuelve a la primera.
   - No hacen falta rutas nuevas, ni tocar `SPA_URLS` ni `rutas.ts`.

3. **Solo se monta el panel activo.** Las gráficas y el calendario se miden al montarse, y en un
   panel oculto se dibujarían con ancho cero. De paso, las métricas de Progreso —lo caro, porque
   recorren el historial entero— solo se piden al abrir su pestaña.

4. **Dónde se ha aplicado:**

   | Pantalla | Pestañas |
   |---|---|
   | Progreso | Actividad · Cuerpo · Métricas (las cuatro cifras quedan fijas encima) |
   | Peso | Registrar · Historial (paginado) |
   | Perfil | Cuenta · Entrenamiento · Salud (un solo «Guardar cambios»; la pestaña con errores del servidor se marca) |
   | Análisis | Lectura · Estancamientos · Cambios (con cuántos hay en cada una) |
   | Notificaciones | Todas · Sin leer (con el `?unread=true` que ya existía) |
   | Catálogo y métricas (gestión) | De ejercicios · De métricas |
   | IA (gestión) | sus cuatro zonas, ahora en `?zona=` |

5. **Lo que acompaña:**
   - El detalle de la auditoría se abre en una hoja, y la lista se pagina.
   - Usuarios filtra por estado.
   - «Guardar mi panel» va pegado abajo.
   - `ds/Paginacion.tsx` es el componente común de paginación.
   - La utilidad `data-table` da a las tablas de escritorio cabecera con filete, fila resaltada
     bajo el ratón y dígitos tabulares.

**Consecuencias.**
- Lo que tiene ADR-043 de «panel de tarjetas» se conserva dentro de cada pestaña. Lo que cambia es
  que no se apilan todas.
- Los tests de pantalla abren la pestaña antes de buscar lo que hay dentro, o montan con
  `?vista=`. Los recorridos de Playwright también: «Historial» en Peso, «Cuerpo» en Progreso y
  «Salud» y «Entrenamiento» en Perfil.
- Una pestaña no puede llamarse igual que un texto que ya se busca en su pantalla. Por eso
  «De ejercicios» y no «Ejercicios», que es la etiqueta de una cifra.

---

## ADR-066 — Aviso push al acabar el descanso, con la aplicación cerrada
**Fecha:** 2026-10-30 · **Estado:** aceptada · **Matiza ADR-063** · **Modifica `.docs/06-security.md` (§12)**

**Contexto.** Con el descanso guardado en el servidor (ADR-065) volver a la aplicación lo encuentra
donde iba, pero nadie avisa de que se ha acabado si el teléfono está bloqueado en el bolsillo:
la vibración de ADR-057 solo suena con la pantalla delante. Se le preguntó al usuario y eligió
**«además, notificación push»**.

Un push es la única forma de que un navegador enseñe algo con la página cerrada. Tiene tres
partes —el navegador se suscribe, el servidor firma y manda, el service worker lo enseña— y cada
una puede filtrar algo o romperse sin que se vea.

**Decisión.**

1. **Web Push estándar con VAPID, sin terceros.**
   - `pywebpush` firma y cifra el mensaje.
   - Las claves `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY` y `VAPID_SUBJECT` van por entorno.
   - **Sin ellas el aviso está apagado**: `GET /api/avisos/clave/` dice `{activo: false}`, la
     aplicación no lo ofrece y no se encola nada. Así un despliegue sin claves no se rompe.
   - `prod.py` falla al arrancar si hay unas sí y otras no, o si el `subject` no es `mailto:` ni
     `https://`.
   - Nada de Firebase ni de OneSignal: serían un tercero más con la lista de quién entrena.

2. **Suscripciones** (`notifications.SuscripcionPush`).
   - Campos: usuario, `endpoint` único, `p256dh`, `auth` y fecha.
   - `POST /api/avisos/suscripcion/` crea o actualiza por `endpoint`. **Si el endpoint era de otra
     persona, pasa a quien lo manda ahora**: en un teléfono compartido los avisos tienen que
     llegarle a quien lo usa.
   - `DELETE` borra solo la propia y responde 204 siempre, para no confirmar si un endpoint existe.
   - Hay un tope de 10 por persona, un cupo de 30 por hora y CSRF como en todo lo que muta.
   - Se borran en cascada con la cuenta y salen en la exportación de datos (solo el servicio y la
     fecha, no el endpoint).

3. **El endpoint solo puede ser de un servicio de push conocido** (`AVISOS_PUSH_HOSTS`: Google,
   Mozilla, Apple y Windows), por `https`. Esto es la defensa contra SSRF: el `endpoint` lo manda
   cualquiera que hable con la API y el worker le hace un POST. Sin la lista, suscribir
   `https://169.254.169.254/…` haría que el servidor llamara a su propia red interna.

4. **La tarea se encola con `eta` y al ejecutarse no se fía de nada**
   (`workouts.tasks.avisar_fin_del_descanso`).
   - Se encola **después del commit** cada vez que un descanso arranca o se alarga, y solo si hay
     claves y alguna suscripción. Con `robust=True`: sin broker se pierde el aviso, no la serie.
   - Al ejecutarse hace un único `UPDATE` condicional: la sesión sigue abierta y su descanso
     termina **exactamente** cuando se programó. Si se saltó, se alargó, hubo otra serie o se
     terminó el entrenamiento, no toca ninguna fila y no avisa.
   - Ese mismo `UPDATE` vacía el descanso, así que una tarea reentregada avisa una sola vez. Por eso
     no hace falta revocar la tarea vieja al alargar.
   - Si llega antes de hora, se reprograma una vez: los relojes del proceso web y del worker no son
     el mismo. En desarrollo, con `CELERY_TASK_ALWAYS_EAGER`, llega en el acto y no hace nada.
   - Más de 2 minutos tarde ya no avisa: un «descanso terminado» a mitad de la serie siguiente es
     ruido.
   - Ningún descanso pasa de 30 minutos, muy por debajo del `visibility_timeout` de Redis (1 h).
     Si lo pasara, Redis reentregaría la tarea con la `eta` pendiente.

5. **El mensaje no lleva datos de nadie.** Lleva «Descanso terminado», «A por la siguiente serie.»,
   la URL de la sesión y una etiqueta. Ni kilos, ni nombres de ejercicio (uno propio puede llamarse
   «Rehab hombro operado»), ni el de la rutina: pasa por el servicio de push del navegador, que no
   es nuestro. TTL de 60 s, `Urgency: high` y `Topic` por sesión, para que uno nuevo sustituya al
   pendiente.

6. **El service worker enseña el aviso sin hablar con `/api/`**.
   - El mensaje trae todo lo que se enseña, y el manejador de `push` no tiene ni un `fetch`.
   - Si hay una ventana con el foco en esa misma sesión, no lo enseña: la pantalla ya vibra. En
     Safari lo enseña siempre, porque iOS revoca la suscripción de quien recibe un push y no enseña
     nada.
   - Tocarlo enfoca la ventana de esa sesión, o navega una, o abre otra. Solo URLs del mismo origen.
   - Funciona también con el interruptor de emergencia de la caché (`PWA_OFFLINE=False`). Esto es
     lo que matiza ADR-063: el service worker ya no es solo caché.

7. **El cliente pide permiso desde un gesto, y con contexto.**
   - Con el primer descanso, el modo foco ofrece «¿Te aviso cuando acabe el descanso?» con
     «Activar» y «Ahora no». El «no» se recuerda en el navegador.
   - Cuenta tiene el interruptor «Avisarme al acabar el descanso».
   - En un iPhone sin la aplicación instalada se explica que hace falta instalarla: Safari solo
     manda avisos a las de la pantalla de inicio (16.4+).
   - **Antes de suscribirse se pregunta al service worker si sabe recibirlos** (`CAPACIDADES` por
     `MessageChannel`). Tras un despliegue puede seguir activo uno viejo sin manejador, y con él
     Chrome enseñaría su aviso genérico.
   - **Al cerrar sesión el navegador se da de baja**: en el servidor (antes de salir, mientras hay
     sesión) y en el propio navegador. Al borrar la cuenta, solo en el navegador; el servidor ya lo
     hizo en cascada.

**Consecuencias.**
- Sin worker de Celery no hay avisos. En Railway el proceso `worker` del `Procfile` tiene que
  estar activo, y en local hace falta un worker de verdad (ver el runbook).
- En iPhone solo funciona con la aplicación instalada y en iOS 16.4 o posterior.
- Una dependencia nueva (`pywebpush`, que trae `aiohttp`, `http-ece` y `py-vapid`), auditada con
  `pip-audit` en CI.
- `test_push.py` cubre la clave, la suscripción, el SSRF, la propiedad del endpoint, el tope, el
  CSRF, la baja y el envío (firma por destinatario, borrado de 404/410, nada sensible en los
  logs). `test_tarea_descanso.py` cubre cuándo avisa y cuándo no, y `avisos.test.ts` el cliente
  con el navegador simulado.

---

## ADR-065 — El descanso lo guarda el servidor y se reanuda al volver
**Fecha:** 2026-10-30 · **Estado:** aceptada · **Matiza ADR-057**

**Contexto.** El descanso vivía solo en la memoria de la pantalla (`useCuentaAtras`). Salir con
la ✕, tocar «Cómo se hace» —que navegaba a la ficha—, recargar o que el sistema cerrara la
aplicación instalada se lo llevaban: al volver no había descanso. El usuario lo describió así:
«salgo o cierro, el tiempo de descanso se corta». Y «Continuar» llevaba siempre al primer
ejercicio, no a donde se había dejado.

ADR-057 ya decía que el descanso **es de la sesión, no de la pantalla**. Lo que faltaba es que la
sesión lo guardara.

**Decisión.**

1. **Dos campos en `WorkoutSession`**: `rest_ends_at` (cuándo acaba) y `rest_seconds` (cuánto
   dura en total, para el anillo).

2. **Las reglas pasan al servidor** (`workouts/focus.py`) y las escrituras van en
   `workouts/descanso.py`:
   - Registrar una serie arranca el descanso de su fila en la rutina, o el del ejercicio si la
     sesión es libre. Si el ejercicio aparece dos veces, las series se reparten entre sus filas en
     orden (`_repartir`), y manda la fila de la serie.
   - **Tras la última serie pendiente de toda la sesión no hay descanso.** Antes lo decidía el
     cliente con `siguiente === null`. Una serie extra sobre un ejercicio ya completo sí descansa.
   - Corregir o borrar una serie no lo toca (ADR-057), y terminar el entrenamiento lo borra.
   - `POST /api/entrenamientos/{id}/descanso/` con `alargar` (+30 s, hasta 30 min) o `saltar`.
     Bloquea la fila con `select_for_update` y responde 404 con una sesión ajena.
   - Registrar también bloquea la sesión, así que dos series a la vez no se pisan el descanso.

3. **El servidor manda segundos que quedan, no una hora** (`{restante, total}`), en el foco
   (`descanso_en_curso`) y en la respuesta de registrar (`descanso`). Así un teléfono con el reloj
   adelantado no cuenta mal. El cliente fija el fin contra el instante en que llegó la respuesta.

4. **En el cliente, el descanso vive en el módulo y no en un componente** (`lib/descanso.ts`).
   - Salir del modo foco no lo para. La barra superior de cualquier pantalla enseña una píldora
     «1:12» que vuelve a ese entrenamiento, como el reproductor en miniatura de una aplicación de
     música.
   - Lo que llega del servidor manda, con dos matices. Una respuesta **más vieja** que lo último
     aplicado no cuenta: el foco de otro ejercicio guardado en la caché lo resucitaría. Una
     diferencia de menos de 1,5 s no se corrige, para que el anillo no salte con cada petición.
   - «+30 s» y «Saltar» se ven en el acto y se le dicen al servidor. Su respuesta se copia a todos
     los focos guardados de la sesión.

5. **Retomar donde se dejó.** Sin `?ejercicio`, el foco abre el primer ejercicio con series
   pendientes, y la pantalla lo fija en la URL con `replace`. «Continuar» ya lleva ahí.

6. **Pantalla siempre encendida, opcional.** La cabecera del modo foco tiene un interruptor con la
   Screen Wake Lock API, que se vuelve a pedir al volver a la página. No se enciende solo, porque
   gasta batería; donde el navegador no sabe hacerlo, no se enseña.

**Consecuencias.**
- Recargar o volver encuentra el descanso con el tiempo real; lo vigilan
  `TestElDescanso` en `test_entrenar.py` y los tests de `Entrenar.test.tsx`.
- Fuera del modo foco, recargar la página vacía la píldora hasta que se vuelve a entrenar: el
  descanso sigue en el servidor, pero nadie lo ha pedido todavía.
- Con el descanso en el servidor, avisar de que se acabó con la aplicación cerrada es posible: es
  ADR-066.

---

## ADR-064 — Las pantallas se recomponen sobre un hook que hace y una vista que pinta
**Fecha:** 2026-10-29 · **Estado:** aceptada · **Matiza ADR-043 y ADR-033**

**Contexto.** Rehacer la interfaz con Aire (ADR-061) obligaba a reescribir el marcado de las
pantallas de usuario. Las más importantes —entrenar y el editor de rutinas— tenían su lógica
mezclada con el marcado:
- **Entrenar**: qué valores proponer, cuándo arranca el descanso y cuándo se pasa solo al
  siguiente ejercicio.
- **Editor de rutinas**: el borrador, la guarda de cambios y el orden de los ejercicios.

Dos de ellas tenían además el JSX comprimido en una sola línea. Cambiar el aspecto sin tocar el
comportamiento pedía separarlos primero.

**Decisión.**

1. **La lógica sale a un hook** (`pantallas/useEntrenar.ts`, `pantallas/useEditorDeRutina.ts`)
   sin tocar el marcado. Se pasan los tests de la pantalla, que buscan por rol y por texto, y
   **después** se reescribe la vista como presentación. Así cada paso tiene su red: si un test
   falla tras sacar el hook, el fallo es de la extracción y no del diseño.

2. **Entrenar es modo foco con la barra de registrar pegada abajo.** Matiza ADR-033: la fila de
   registrar ya no se apila en la tarjeta, sino que va pegada al borde.
   - Arriba: la ✕ y el nombre de la rutina.
   - Debajo: el avance, el ejercicio con su imagen y la lista de series.
   - Abajo, en una barra fija con el cristal de las barras de navegación: los dos steppers grandes
     (`Stepper tamano="lg"`, 56 px) y «Registrar serie».
   - El descanso, cuando corre, se pone encima de esa barra en una sola fila, así que la siguiente
     serie se puede ir ajustando sin cerrarlo.
   - «Terminar» navega con `replace`, para que «atrás» desde el cierre no vuelva a una sesión ya
     cerrada.

3. **La pestaña «Entrenar» es un centro y no solo el historial.**
   - Arriba va lo que toca hoy con su botón, la misma tarjeta de Inicio (`TarjetaDeHoy`): es la
     pestaña que se toca con el teléfono en la mano al llegar al gimnasio, y antes obligaba a
     volver a Inicio para empezar.
   - Debajo, el entrenamiento libre y el diario.
   - La tarjeta usa la consulta de Inicio y su caché.
   - El diario dice el nombre de la rutina: la API añade `routine_name`, que antes faltaba y
     dejaba «Rutina» en todas las filas.

4. **Listas agrupadas como las de iOS** en Plan, el día del plan, el editor y Cuenta. Las
   composiciones propias de ADR-043 se conservan donde la tarea lo pide: Progreso sigue siendo un
   panel de tarjetas y Ejercicios un catálogo.

5. **El acceso parece una aplicación.**
   - En el teléfono: el icono grande, el título y el formulario, sin caja alrededor.
   - En escritorio: la tarjeta de dos mitades.

**Arreglos que salieron al recomponer.**
- **Los tonos de `Badge` no se generaban.** «Finalizado», «Récord», «Hoy», «bajada» e
  «informativo» salían grises, en Forja y en Aire. `Badge` arma la clase `badge-${tono}` en
  tiempo de ejecución y solo existían los tonos escritos literalmente en algún otro sitio. Se
  declaran con `@source inline`, y `TestLasClasesConstruidasExisten` compara los tonos y variantes
  que declaran `Badge.tsx` y `Button.tsx` con lo que lista el CSS.
- **Borrar un peso pregunta antes** (`Confirmacion`). Era un botón que borraba al primer toque,
  justo donde cae el pulgar al desplazar la lista apilada.
- **El equipamiento del perfil son chips** que se marcan, no 28 casillas en una columna que en el
  teléfono medían tres pantallas. Siguen siendo `checkbox` para el lector de pantalla.
- **Las navegaciones tras guardar usan `replace`**: rutina nueva, día del plan, programa nuevo y
  eliminar rutina. Así «atrás» no vuelve a un formulario ya enviado.

**Consecuencias.**
- Los tests de pantalla no cambiaron de forma, porque buscan por rol y texto; los textos que
  fijan se conservaron. Hubo tres ajustes deliberados:
  - El diario lleva el nombre de la rutina.
  - Peso confirma antes de borrar (vitest y Playwright).
  - El centro «Entrenar» necesita un manejador de `/api/inicio/`.
- La revisión visual de Playwright corre solo en el proyecto de escritorio: ella fija los cuatro
  anchos, y en los dos proyectos gastaba el cupo diario de la API de la cuenta de pruebas (1000
  peticiones), con lo que el resto de recorridos acababa en 429.

---

## ADR-063 — La PWA abre sin conexión; los datos, nunca de caché
**Fecha:** 2026-10-29 · **Estado:** aceptada, **matizada por ADR-066** (el service worker también enseña avisos push) · **Sustituye a ADR-050** · **Modifica `.docs/06-security.md` (§11)**

**Contexto.** ADR-050 dejó la PWA instalable pero sin caché, a petición del usuario. El usuario ha
vuelto a pedirlo de otra manera: que la aplicación sea una PWA de verdad. Se le planteó qué
significaba eso y eligió **«abre sin conexión»**: que la aplicación instalada se abra sin red y
diga que no la hay, en vez de enseñar la página de error del navegador.

ADR-050 tenía dos objeciones, y siguen siendo ciertas:
- Una caché mal invalidada deja a parte de la gente en una versión vieja durante días.
- Sin red no se puede registrar una serie, porque el número y el peso propuesto los pone el
  servidor.

Lo que se decide aquí es cómo cachear **sin caer en ninguna de las dos**.

**Decisión.**

1. **Se cachea la aplicación, no los datos.** El service worker precachea la cáscara y los
   archivos del build.
   - La cáscara es `spa.html`, que no lleva ningún dato de quien la pide. Se pide a `/entrar/`
     sin credenciales.
   - Los archivos del build salen todos del manifiesto de Vite: entrada, trozos perezosos, hojas
     y fuentes, más `theme.js` y los iconos.
   - **`/api/`, `/admin/` y `/media/` no los toca ni los intercepta.** Lo que no es `GET` tampoco
     pasa por él.
   - **La caché de TanStack nunca se persiste**: vive en memoria y muere con la pestaña.

2. **Una versión por build y la nueva espera a que la pidan.**
   - La versión es la huella del manifiesto de Vite, del propio service worker y de los estáticos
     de la cáscara. Va en `<meta name="app-version">`, y la caché se llama `gym-<versión>`.
   - Al instalarse, la versión nueva **no** llama a `skipWaiting()`. La página enseña «Hay una
     versión nueva» con un botón «Actualizar», que pasa por la guarda de cambios sin guardar.
     El aviso no aparece en el modo foco, donde recargar se llevaría el temporizador de descanso.
   - Al activarse, se borran las cachés de otras versiones.
   - **Comprobación de integridad.** La cáscara se guarda solo si contiene su misma versión. Si
     durante un despliegue la sirviera todavía el proceso viejo, se rechaza en vez de quedar
     apuntando a archivos que no existen.

3. **Navegar va primero a la red.** Si no hay red, o el servidor da un 5xx, se sirve la cáscara
   guardada. Con cáscara guardada la red tiene 4 s; sin ella, todo el tiempo que necesite. **Lo
   que llega de una navegación nunca se guarda**: así la cáscara y sus archivos siempre son de la
   misma versión. Los estáticos se sirven primero de la caché, porque llevan el hash en el nombre.

4. **Sin red no se finge.**
   - La sesión no puede comprobarse y la aplicación enseña «Sin conexión» con un reintento, en
     vez de mandar al acceso a quien sí tiene sesión. `useSesion` falla en vez de quedarse en
     pausa (`networkMode: "always"`).
   - Las mutaciones también fallan en el acto, en vez de esperar a enviarse cuando vuelva la red.
     Así una serie no se registra horas después, ni dos veces.
   - «Registrar serie» se desactiva sin red y lo explica. Una franja bajo la barra superior avisa
     de que lo que se ve es lo último que cargó.

5. **Al cerrar sesión o borrar la cuenta se vacían las cachés.** No tienen datos de nadie, así que
   no es lo que protege la privacidad: eso lo hace el punto 1. Es la otra mitad de la misma idea:
   el dispositivo se queda como si la aplicación no se hubiera abierto.

6. **Interruptor de emergencia.** Con `PWA_OFFLINE=False`, o con el servidor de Vite, `/sw.js`
   sirve una versión que no cachea, borra lo que hubiera y se activa en el acto. Si un despliegue
   dejara a alguien atascado, se arregla con una variable de entorno y sin tocar código.

**Lo que se añade para instalar.**
- El manifiesto lleva `id`, `categories`, `launch_handler` y atajos con icono. Sus colores son los
  del tema claro.
- La cáscara lleva las metas de iOS y un icono de 180 px opaco.
- Chrome y Edge avisan con `beforeinstallprompt`, y la fila «Instalar la aplicación» de Cuenta
  llama a `prompt()`. Safari en iOS no tiene ese evento, así que ahí la fila explica los pasos.
- Los iconos se dibujan sin tipografía: la mancuerna, con la geometría del icono de la
  aplicación.

**Consecuencias.**
- `test_pwa.py` vigila el service worker: no se cachea, solo precarga `/static/`, excluye `/api/`
  y `/admin/`, la versión cambia con el build y coincide con la de la cáscara, `skipWaiting()`
  solo se llama al pedirlo, y el JavaScript generado pasa `node --check`.
- `test_templates.py` comprueba que la cáscara renderizada para un usuario no contiene ni su
  nombre ni su correo: es la página que se guarda.
- Un test de deriva obliga a que cada color escrito fuera del CSS (`theme.js`, `spa.html`, el
  manifiesto, el generador de iconos, los respaldos de las gráficas, el service worker) sea un
  token de `app.css`.
- Para que esto funcionara hizo falta ADR-060, que da una URL única por archivo del bundle.
- **Lo que no hace, a propósito:** registrar series sin red. Si algún día hace falta, es otra
  decisión: el número de serie y el peso propuesto tendrían que poder calcularse en el cliente, y
  el servidor tendría que aceptar series con fecha atrasada sin duplicarlas.

---

## ADR-062 — Barra superior con título y «atrás», barras translúcidas, modo foco sin marco
**Fecha:** 2026-10-29 · **Estado:** aceptada · **Sustituye a ADR-034 y ADR-035** · **Matiza ADR-048 y ADR-051**

**Contexto.** ADR-034 quitó la barra superior porque en un monitor «la aplicación parecía un móvil
estirado». En el teléfono eso dejó cuatro huecos que una aplicación instalada no puede tener:

- No había ningún sitio fijo para volver atrás. Cada pantalla de segundo nivel pintaba su
  propio «‹ Plan» (ADR-035), con un destino escrito a mano.
- El aviso de mensajes sin leer solo existía en la barra lateral de escritorio.
- La franja de arriba del teléfono era un texto «PROJECT_GYM» que se iba con el scroll.
- El modo foco conservaba un botón de Cuenta, contra su propia regla de que la única salida es
  la ✕.

Al pedir que la aplicación se sintiera nativa (ADR-061), esos huecos pasaron a ser lo más
visible.

**Decisión.** El marco pasa a tener tres piezas. Las dos de navegación siguen pintando una sola
lista de cinco destinos.

1. **Barra superior fija y translúcida.** Se queda pegada arriba, con la muesca descontada.
   Tiene tres columnas:
   - **Atrás**, en las pantallas que no son uno de los cinco destinos.
   - **El título de la pantalla en pequeño**, solo cuando el título grande ya salió por arriba.
     Es el patrón del título grande de iOS. `Cabecera` publica su título y su `<h1>` en
     `lib/marco.tsx`, y un `IntersectionObserver` decide cuándo repetirlo. El título repetido no
     es un encabezado y va `aria-hidden`: dos encabezados iguales se anunciarían dos veces.
   - **En el teléfono, la campana con la cifra de sin leer y la inicial que abre Cuenta.**

   En escritorio la barra solo aparece si hay a dónde volver: la lateral ya tiene lo demás.

2. **Un solo «atrás», en la barra.** Sustituye a ADR-035 y se borran los tres de las pantallas.
   - Con historial dentro de la aplicación, vuelve por el historial. Así Ejercicios conserva sus
     filtros y la guarda de cambios sin guardar pregunta antes de salir del editor.
   - Sin historial (enlace de un correo, aplicación instalada abierta justo ahí), va al padre de
     la pantalla con `replace`.

   El padre sale de `ds/navegacion.ts`, que sube por los segmentos del camino. Solo hay un mapa
   para los que no se deducen solos, así que **añadir una pantalla sigue tocando tres sitios, no
   cuatro**.

3. **Pestañas abajo, planas y translúcidas.** Se quita la baldosa elevada de «Entrenar», porque
   las barras de iOS no destacan una pestaña. La palabra va siempre bajo el icono. Su alto es
   `--tab-bar-h`: el contenido, la barra del editor y lo que vaya pegado encima lo leen de ahí.

4. **El modo foco no tiene marco.** Sin barras y sin Cuenta. `MarcoDeFoco` solo pone las zonas
   seguras y el ancho de lectura.

5. **Gestión es una pantalla de profundidad.** Sustituye a la parte de ADR-048 que le daba
   navegación propia con un «Volver a la aplicación».
   - En el teléfono no lleva barra de pestañas: de gestión no se salta a entrenar, se sale, y la
     salida es el «atrás» de la barra.
   - Sus cinco secciones son chips desplazables bajo el título.

**Además:**
- La tarjeta «Ajustes» que Perfil enseñaba solo en el teléfono se borra. Duplicaba Cuenta, y su
  «Cerrar sesión» se saltaba la guarda de cambios sin guardar: salir con el perfil a medio
  editar tiraba los cambios sin preguntar.
- Los `<a href>` a pantallas de la aplicación pasan a `Link`. Estaban en Generar rutina,
  Análisis, Avisos y el resumen de Gestión, y cada clic recargaba la página entera. El de
  Avisos además apuntaba a `/analisis/`, que no existe: era un 404.

**Consecuencias.** Lo que comprueba `AppShell.test.tsx`:
- Sigue comprobando que hay dos navegaciones «Principal», cada una con los cinco destinos, y dos
  botones «Cuenta».
- Comprueba también que «Avisos» está en las dos barras con su cifra, que no hay «atrás» en los
  destinos y sí en las rutas de segundo nivel, y que la barra no tiene encabezados.
- En gestión hay una sola navegación «Principal».

El marco no hace ninguna petición nueva: la cifra de la campana es la misma consulta que la de
la lateral.

---

## ADR-061 — «Aire»: claro primero, acción en azul, dato en verde azulado, Inter tabular y tema del sistema
**Fecha:** 2026-10-29 · **Estado:** aceptada · **Sustituye a ADR-044** · **Matiza ADR-051**

**Contexto.** El usuario pidió mejorar toda la interfaz para que la aplicación se sienta como una
aplicación instalada y no como una web, y cambiar el concepto visual. Se le presentaron tres
direcciones —oscuro deportivo, claro nativo y una evolución de Forja que conservara la paleta— y
eligió **la clara y nativa, al estilo de iOS**. También eligió que el tema **siga al del
sistema**, en vez de arrancar siempre en oscuro como Forja.

**Decisión.** Se reescribe `assets/app.css` con la misma estructura y los mismos nombres de
utilidad: los componentes siguen diciendo `btn-primary`, `card`, `chip-on` y `stat-tile`, y lo
que cambia es lo que hay dentro. Seis decisiones, cada una con su razón:

1. **Los tokens se renombran por lo que significan: `ember` → `primary` y `steel` → `data`.**
   Un `--ember` azul confundiría a cualquiera que lea el código. El cambio tocó unas cuarenta
   clases en dieciocho componentes, y un test (`TestNingunComponenteNombraUnTokenQueYaNoExiste`)
   impide que vuelva a aparecer una: una clase de Tailwind con un color que no existe no falla,
   simplemente no pinta.

2. **`primary` se parte en dos: el azul que se lee y el que se rellena.** En el oscuro no existe
   un azul que dé 4,5:1 como texto sobre la tarjeta `#1c1c1e` y a la vez 4,5:1 con texto blanco
   encima. `--primary` es para texto, enlaces, iconos y bordes; `--primary-fill` es para el fondo
   del botón primario, del día de hoy y de la placa de la marca. En el claro valen lo mismo.

3. **El claro es el predeterminado y el tema sigue al sistema.** `:root` lleva el claro, y es lo
   que se ve si `theme.js` no llega a ejecutarse. La preferencia guardada puede ser *sistema*,
   *claro* u *oscuro*. Con *sistema*, `theme.js` escucha `prefers-color-scheme` y cambia en
   caliente. La clave de `localStorage` pasa a `gym-tema`. Quien eligió algo en Forja conserva su
   elección; quien nunca eligió pasa a *sistema*. Sigue sin haber nada más en `localStorage` que
   preferencias de presentación.

4. **Las cifras siguen siendo tabulares, pero en Inter y no en mono.** La regla 5 de ADR-044
   —toda cifra que lea una persona va en `metric-*`, `tag` o `num`— se mantiene, porque lo que
   evita que una columna de kg baile es que los dígitos midan todos lo mismo, no que la fuente
   sea mono. Inter tiene `tnum`, comprobado sobre el subconjunto descargado. Se borran Archivo e
   IBM Plex Mono, y `--font-mono` queda en la del sistema, solo para `<code>`.

5. **El anillo de foco pasa a ser azul.** Es una desviación deliberada de ADR-044.4, que lo
   quería de un color distinto al de la acción para que un botón primario enfocado no se
   confundiera con uno pulsado. En Aire lo separa el desplazamiento de 2 px, igual que en iOS y
   macOS, y un anillo verde azulado alrededor de un botón azul se leía como un error de
   pintado.

6. **El dato se queda con todo lo que se mira y no se pulsa.** Gráficas, calendario de
   actividad, mapa corporal, anillo de descanso y barra de avance van en `data`. Es la misma
   razón de ADR-044.4 llevada más lejos: en Aire el azul significa «toca aquí», y un mapa de
   calor azul invitaba a tocarlo. El músculo elegido como filtro sí va en `primary`, porque
   elegir es una acción.

**Lo que se hereda de ADR-044 sin cambios:**
- Los tokens viven en `:root` y `@theme inline` los expone.
- Las fuentes se autoalojan, porque la CSP declara `font-src 'self'`.
- Los campos miden al menos 16 px (ahora 17), para que iOS no haga zoom.
- El contraste se calcula y no se afirma. Los pares son ahora veinticinco: se añadieron el texto
  del botón primario al pasar por encima, el azul sobre una superficie elevada, la etiqueta de
  una pestaña sobre la barra, el recuento dentro de un chip y la marca de serie hecha.

**Consecuencias.**
- `test_design_system.py` busca los bloques de tema por selector al principio de línea y no por
  primera aparición de la cadena, que ahora sale también en la variante `dark:`. Además comprueba
  que `:root` sea el claro y que no quede ningún `.woff2` sin usar.
- `DESIGN/forja-*.html` quedan como histórico. La referencia viva es `/estilos/` junto con este
  archivo.
- La marca sigue siendo PROJECT_GYM. Cambia la placa: el «PG» pasa a ser la mancuerna del icono
  de la aplicación, para que la pantalla de inicio del teléfono y la aplicación se reconozcan como
  la misma cosa.

---

## ADR-060 — La cáscara pide el bundle por el nombre que le puso Vite, no por el de `collectstatic`
**Fecha:** 2026-10-29 · **Estado:** aceptada · **Matiza ADR-047**

**Contexto.** `{% vite %}` construía las URL del bundle con `static()`. En producción eso pasa por
`CompressedManifestStaticFilesStorage`, que le pone un segundo hash al nombre:
`main-BNTxZHpa.js` → `main-BNTxZHpa.<12 hex>.js`. Pero los `import` que hay dentro del bundle no
se reescriben (`support_js_module_import_aggregation` está a `False`), y el trozo perezoso de la
gráfica empieza con `import … from "./main-BNTxZHpa.js"`. Un módulo ES se identifica por su URL:
con dos nombres para el mismo archivo, **el módulo principal se evaluaba dos veces** —dos copias de
React, un segundo `createRoot` sobre `#root`— y la gráfica llamaba a los hooks de la copia
equivocada. En desarrollo no hay segundo hash y por eso ni los tests ni los recorridos de
Playwright lo podían ver. `TestLosTrozosPerezososResuelven` comprobaba que el trozo *existe*, que
era la mitad del problema. Lo destapó la revisión previa a hacer que la PWA abra sin conexión: el service worker
necesita una URL por archivo para precachearlo.

**Decisión.** `vite._estatico()` devuelve `STATIC_URL + "spa/" + archivo`, sin `static()`. El hash
de Vite ya va en el nombre, así que la caché larga sigue siendo segura: un despliegue cambia la
URL. Lo que el segundo hash daba —que Whitenoise sirviera el archivo con caché de un año— lo da
ahora `WHITENOISE_IMMUTABLE_FILE_TEST`, una expresión que reconoce los dos hashes: el de Vite bajo
`/static/spa/assets/` y el de `collectstatic` para el resto. `theme.js` y los iconos siguen
pasando por `static()`; esos no los importa nadie desde dentro del bundle.

**Consecuencias.** `test_vite.py` prueba las URL con `ManifestStaticFilesStorage` y un manifiesto
vacío —si alguien vuelve a meter `static()`, el almacén estricto lanza antes de la aserción— y
vigila la expresión en los dos sentidos: lo que lleva hash es inmutable y `theme.js` no.
`WHITENOISE_KEEP_ONLY_HASHED_FILES` no puede activarse nunca: borraría los originales y cada trozo
daría 404. Si las gráficas fallaban en Railway, este era el motivo.

---

## ADR-059 — `dev` se promueve sola a `main` por PR cuando pasa el CI
**Fecha:** 2026-09-29 · **Estado:** aceptada

**Contexto.** Se trabaja en `dev` y Railway despliega `main`. Llevar lo uno a lo otro era un PR a
mano, y en medio las dos ramas se separaron: `main` recibió dos commits directos (la configuración
de Railway y las confirmaciones propias, ADR-052 y ADR-053) que `dev` no tenía, y `dev` un commit
grande que `main` no tenía. Se pidió que `dev` llegue a `main` sola, pasando por el CI.

**Decisión.**

- **`promover.yml`**: en cada push a `dev` corre el CI entero (`ci.yml`, ahora también
  `workflow_call`) y, si sale en verde, abre —o reutiliza— un PR `dev → main` y lo fusiona.
- **Se eligió PR frente a avanzar `main` directamente**, a petición: deja rastro de cada
  promoción en la lista de PR.
- **La fusión la hace el propio workflow cuando termina el CI, no el auto-merge de GitHub.** El
  auto-merge nativo necesita activar «Allow auto-merge» y proteger `main` con checks obligatorios;
  sin esa protección, `gh pr merge --auto` falla o fusiona sin esperar. Fusionando en un job que
  depende del CI, el orden lo garantiza el workflow y basta con **un** ajuste del repositorio:
  «Allow GitHub Actions to create and approve pull requests».
- **`--match-head-commit`**: se fusiona solo si `dev` sigue en el commit que pasó el CI. Si alguien
  empujó mientras tanto, la fusión se niega y la promueve la ejecución de ese push.
- **`--merge`, no `--squash`**: con squash, `main` tendría commits que no están en `dev` después
  de cada promoción y la siguiente chocaría.
- Un push nuevo a `dev` **cancela** la promoción anterior en curso (`concurrency`).

**Consecuencias.** **No se empuja a `main` a mano**: lo que entra ahí sin pasar por `dev` separa
las ramas otra vez y la promoción siguiente puede chocar. Si hace falta un arreglo urgente, se hace
en `dev`. La fusión la hace `GITHUB_TOKEN`, así que el push a `main` **no** vuelve a lanzar
`ci.yml` —el commit ya se probó— pero sí le llega a Railway, que escucha a GitHub y no a Actions.
Si algún día se protege `main` exigiendo checks, sus nombres son los del workflow llamado:
`ci / test`, `ci / frontend` y `ci / seguridad`. Si se exige además una aprobación, el workflow no
podrá fusionar.

---

## ADR-058 — Las series se numeran 1..n y borrar una renumera las demás
**Fecha:** 2026-09-29 · **Estado:** aceptada

**Contexto.** El número de serie lo pone el servidor desde la Fase 6, pero lo **contaba**:
`count() + 1`. Con las series 1, 2 y 3, borrar la 1 y registrar otra daba 2, 3 y **3**. La pantalla
de entrenar no lo enseñaba porque coloca las filas por posición, pero `last_performance()` ordena
por número, así que «la última vez» podía salir desordenada, y la exportación del RGPD sacaba dos
series «3».

**Decisión.**

- **Borrar una serie renumera las que quedan de ese ejercicio en esa sesión** a 1..n, conservando
  el orden (`SetLog.renumerar`). Se eligió frente a «el mayor más uno» a secas porque este dejaría
  huecos —«2, 3, 4» tras borrar la primera—, y una serie «4» en un ejercicio de tres se lee como
  una de más.
- **Registrar usa el mayor más uno** (`SetLog.siguiente_numero`), no el recuento: con la
  renumeración coinciden, pero si algo deja un hueco —el `/admin/`, una serie que se mueva de
  ejercicio— el recuento vuelve a repetir y el máximo no.
- **Numerar bloquea la fila de la sesión** (`select_for_update`) dentro de una transacción: dos
  registros simultáneos leerían el mismo máximo. Solo se esperan entre sí los de la misma sesión.
- **La migración `workouts.0007` arregla los repetidos que ya existían**, con la lógica copiada y
  no importada: tiene que hacer lo mismo aunque el modelo cambie.

**Consecuencias.** El número de una serie **no es estable**: borrar la 1 convierte la 2 en la 1.
Nada lo usa como identificador —para eso está la `pk`—, y es lo que cualquiera espera al tachar
una serie en un papel. No se añade una restricción `UNIQUE` en la base: el cliente puede mandar su
propio `set_number` al crear, y una restricción lo convertiría en un 500 en vez de en un número
repetido. Si algún día se quita esa opción, es el siguiente paso.

---

## ADR-057 — El descanso se acaba en cero y es de la sesión, no del ejercicio
**Fecha:** 2026-09-29 · **Estado:** aceptada, **matizada por ADR-065** (el descanso lo guarda el servidor y la regla «sin descanso tras la última serie» pasa allí)

**Contexto.** Tres quejas de quien entrena con la aplicación, las tres de la misma pantalla:

1. **El descanso no se acababa.** Llegado a cero seguía contando hacia arriba en `warning`
   («+0:05», «+0:30», «Descanso excedido»). Era una decisión escrita solo en el código
   (`lib/cuentaAtras.ts`, `ds/RestTimer.tsx`) con su razón: «un temporizador que se apaga deja sin
   saber si se lleva medio minuto de más o cinco». Quien lo usa lo vive al revés: configuró un
   minuto o minuto y medio y quiere que eso sea todo.
2. **Corregir una serie reiniciaba el descanso.** No había «editar»: solo un botón de borrar que
   aparecía al pasar el ratón, invisible en un teléfono. Corregir una errata era borrar y volver a
   registrar, y registrar arranca la cuenta atrás desde el principio. Además, cambiar de ejercicio
   **paraba** el descanso, así que volver al anterior a arreglar algo también lo perdía.
3. **Terminadas las series de un ejercicio, la pantalla no avanzaba.** El descanso arrancaba y
   había que pulsar «Siguiente» a mano con el teléfono en una mano.

**Decisión.**

- **Al llegar a cero, el descanso se quita** y el teléfono vibra (`navigator.vibrate`). Solo vibra
  si el fin acaba de pasar (menos de 2 s): con la pantalla bloqueada el tick no corre, y vibrar al
  desbloquearla minutos después no avisaría de nada. Desaparecen `rest-over` y «Descanso excedido».
- **El descanso es de la sesión, no de la pantalla.** Cambiar de ejercicio —a mano, con el «atrás»
  del navegador o por el avance automático— ya no lo corta. Solo lo cambian «Saltar», llegar a
  cero y registrar otra serie. Esto sustituye la regla de la Fase 6 «cambiar de ejercicio corta el
  descanso», que no tenía ADR y se apoyaba en que el descanso era «del ejercicio que se acaba de
  hacer»: con el avance automático, arrastrarlo al siguiente es justo lo que se quiere.
- **Corregir es un `PATCH`**, desde un panel que se abre tocando la fila hecha. No toca el descanso
  ni cambia de ejercicio. Borrar se queda dentro del mismo panel.
- **Registrar la última serie de un ejercicio lleva solo al siguiente**, con el descanso corriendo.
  «Completo» (`actual.completo`) y «cuál va después» (`siguiente`) los decide `focus.py`: el
  siguiente es el próximo ejercicio con series pendientes, hacia delante y **dando la vuelta**,
  porque quien se saltó uno por tener la máquina ocupada vuelve a él al acabar. El cliente solo
  compara `completo` antes y después de registrar: una serie extra en un ejercicio ya completo no
  mueve a nadie. Si no queda nada pendiente, no hay descanso y se ofrece «Terminar».

**Consecuencias.** Se pierde saber cuánto se ha pasado del descanso; quien lo quiera tiene
«+30 s» antes de que acabe. **En iPhone no vibra**: Safari no implementa `navigator.vibrate`, así
que ahí el aviso es solo que el anillo desaparece. Y el avance automático cuesta una petición más
(se vuelve a pedir el foco antes de decidir), unos 100 ms que pasan mientras corre el descanso.

---

## ADR-056 — La programación es de Python; el RAG elige ejercicios, no series
**Fecha:** 2026-09-22 · **Estado:** aceptada · **Completa ADR-054** · **Matiza ADR-005**

**Contexto.** Una rutina generada para «pectorales, tríceps y deltoides» salió con ocho ejercicios,
**doce series en total** —una o dos por ejercicio—, 60 s de descanso en todo y tres variantes del
press de banca. La persona había subido dos libros de hipertrofia al RAG y preguntaba, con razón,
si eso servía de algo. La auditoría (`AIGeneration` nº 44) dice que el fallo no era del modelo:

1. **Lo único que sabía de la intención era el perfil de nutrición**: `Objetivo: Mantenimiento ·
   Nivel: Principiante`. La regla 7 del prompt le ordenaba «un principiante no necesita el volumen
   de un avanzado». **El concepto “objetivo de entrenamiento” no existía**: `accounts.Goal` es
   Volumen / Definición / Mantenimiento, que es peso corporal, no entreno.
2. **Nada comprobaba los números.** El esquema de salida no admite `minimum`/`maximum` —rompen en
   los tres proveedores (ADR-030)— y `apply_plan` solo acota lo disparatado. La validación de
   ADR-054 mira días, cobertura y énfasis; el volumen no.
3. **Las métricas le decían que esa persona entrenaba 2 series por grupo y semana**, así que doce
   en un día le pareció un aumento.

**Sobre el RAG, que es lo que se preguntaba.** Está bien conectado: `active_vector_store_ids()`
devuelve el almacén, `OpenAIProvider` adjunta `file_search` y los documentos están indexados. Pero
`file_search` es una herramienta que **el modelo decide** usar, y aunque la use, **un libro no
rellena el campo `sets`**. El RAG sirve para elegir mejor los ejercicios y justificar el plan; los
números tienen que salir de Python, como la aritmética de progreso (`.docs/07-reglas.md`) y el reparto
(ADR-054).

**Decisión.**

- **`TrainingGoal`** —hipertrofia, fuerza, resistencia— se elige **en el formulario de generar**,
  no en el perfil: se puede entrenar para hipertrofia estando en déficit, y quien alterna bloques
  no tiene que ir a otra pantalla. El objetivo de peso del perfil se queda como está.
- **`ProgrammingRules`**, una fila por objetivo: series por ejercicio, banda de repeticiones,
  descanso mínimo —distinto en compuestos y en aislamiento— y series mínimas por músculo y día.
  Las crea una **migración de datos** desde `PROGRAMACION_POR_DEFECTO`, que se queda en el código
  como respaldo, y **se ajustan desde `/gestion/` → IA → Programación** sin desplegar.
- **Las repeticiones son una banda por objetivo, no un número por tipo de ejercicio.** La primera
  versión separaba compuestos (6-12) y aislamiento (10-20) y rechazaba un 8-12 en un curl, que es
  correcto. Con la banda 6-20 caben las dos cosas. Lo que sí distingue compuesto de aislamiento es
  **el descanso**, y ahí la diferencia es real.
- **Compuesto o aislamiento se deduce de los músculos secundarios** (`n_secundarios ≥ 2`), la
  misma anotación que ya ordena los candidatos. El dataset no trae ninguna columna que lo diga.
- **El mínimo por músculo se acota a lo posible**: `(ejercicios // músculos) × series_min`. Con
  tres ejercicios y tres músculos no caben seis series en cada uno, y exigirlo agotaría los tres
  intentos siempre. Se calcula sobre las series **mínimas** y no las máximas: pedir el máximo en
  todos los ejercicios para aprobar no es programar, es apurar.
- **El prompt enseña esos mismos números** (`{{ programacion }}`, renderizado desde las reglas) y
  pide explícitamente **consultar los documentos** antes de elegir, diciendo en `rationale` qué se
  sacó de ellos.

**Consecuencias.** Un plan que no cumple se rechaza y se reintenta con el número concreto —«lleva
1 series y van de 3 a 4»—, que es el mecanismo que ya funcionó en ADR-054.

**Y los reintentos cuestan cupo, así que los libros solo van en el primero.** Adjuntar
`file_search` multiplica por cinco lo que OpenAI **reserva** del límite por minuto: medido contra
la API con el mismo prompt de 4.000 tokens, 3.632 sin la herramienta y 18.501 con ella. Con tres
intentos cargando los libros, una sola generación puede no caber en un cupo de 200.000 TPM. Un
reintento no necesita buscar: ya tiene la rutina escrita y lo que se le pide es corregir un
número. Subir mucho los mínimos
desde el panel puede agotar los intentos: la pestaña lo advierte. Y esto no arregla la *elección*
de ejercicios —tres presses de banca seguidos—; eso depende del modelo, y el activo es
`gpt-4o-mini` con `effort=low`.

**Verificación.** 21 tests del servicio (cada regla con su caso, las tres fuentes de las reglas, y
el acote del mínimo), tres del generador —que el prompt lleve los números del objetivo elegido y
que una rutina floja se reintente con «lleva 1 series» y «descansa 60 s»—, y ocho de API entre el
parámetro, su rechazo y la edición desde el panel.

---

## ADR-055 — Los documentos del RAG se suben desde el panel
**Fecha:** 2026-09-22 · **Estado:** aceptada · **Sustituye el punto 6 de ADR-048** (los otros
cinco siguen en pie)

**Contexto.** ADR-048 §6 dejó la subida de documentos en el `/admin/` con dos razones: que subir un
archivo se hace «una vez al mes y con el archivo delante», y que duplicar aquí la validación por
magic bytes habría dejado dos sitios que mantener sincronizados. La primera es una estimación de
frecuencia; la segunda es la que sostenía la decisión, y **no era cierta ni entonces**:

- La validación es **una sola función**, `validate_knowledge_document()`
  (`apps/aiassist/validators.py`). El formulario del admin es un envoltorio de seis líneas.
- `DocumentoSerializer.validate_file()` **ya la llamaba**, y su propio docstring decía que se
  reutilizaba tal cual «porque tenerla escrita dos veces es cómo se acaba con una de las dos
  desactualizada».
- `DocumentoViewSet` ya traía `CreateModelMixin` y `DestroyModelMixin`, y `AlmacenViewSet` la
  acción `crear_en_openai`. **El backend permitía subir desde el primer día**: lo que no existía
  era el formulario, y la pantalla mandaba al admin dando una razón que su propio código
  desmentía.

Y el efecto práctico era peor que la incomodidad: con cero almacenes, la pestaña era un callejón
sin salida —un aviso diciendo que no había ninguno y un enlace a otra aplicación—.

**Decisión.** El panel crea el almacén, lo crea en OpenAI, sube documentos, los reintenta y los
borra. El `/admin/` **se conserva** con el mismo papel que le da ADR-048: red de seguridad.

Cuatro detalles que son la decisión de verdad:

1. **Las extensiones y el tope los dice el servidor** (`GET /api/gestion/documentos/limites/`),
   leídos de los mismos settings que usa el validador. Escribirlos en React sí habría sido la
   duplicación que ADR-048 temía: el día que se admitiera otro formato, el formulario seguiría
   rechazándolo antes de preguntar.
2. **Subir no espera al troceado, y el panel no depende de Celery.** Esto se decidió **después de
   medirlo**: la primera versión encolaba `index_knowledge_document`, que usa `upload_and_poll` —
   sube y luego pregunta a OpenAI cada segundo hasta que el documento está troceado y
   vectorizado—. En desarrollo las tareas corren dentro de la petición
   (`CELERY_TASK_ALWAYS_EAGER`), así que subir un PDF de verdad dejaba el navegador esperando
   minutos hasta rendirse con un *broken pipe*; el documento acababa indexado, pero quien lo
   subió solo veía una conexión rota. Y en producción, un panel que solo funciona si hay un
   worker levantado es un panel que a veces no funciona.

   Así que la subida hace las dos llamadas rápidas —crear el archivo y asociarlo al almacén— y
   deja el documento en `indexing` (`rag.start_indexing`). El estado final lo trae
   `rag.refresh_status()`, que el listado consulta **solo de los que están a medias**, y el panel
   vuelve a preguntar cada cuatro segundos mientras quede alguno. Medido: la subida responde en
   3,4 s y el estado llega solo, sin recargar.

   Un fallo no tumba la subida: el archivo está validado y guardado, y el documento queda en
   `failed` con el motivo a la vista, que es de donde se sale con «Reintentar».
   `index_document()` (con espera) se conserva para la tarea de Celery, que es la que usa el
   admin.
3. **Borrar borra en los dos sitios.** Quitar solo la fila local dejaba el libro dentro del
   almacén: seguía contestando a las búsquedas y ya no quedaba nada por aquí que dijera que
   estaba ahí. Si el borrado remoto falla se responde 502 y **la fila se queda**: perderla
   convertiría un fallo temporal en un archivo huérfano que nadie va a volver a encontrar.
4. **Subir exige que el almacén exista en OpenAI.** Mientras no existe no hay dónde indexar, así
   que la tarjeta ofrece «Crear en OpenAI» y no el formulario. La creación local y la remota
   siguen separadas, como ya decía el modelo: permite arreglar una clave mal puesta sin perder los
   documentos ya subidos.

**Consecuencias.** `api()` (`frontend/src/api/cliente.ts`) aprende a mandar `FormData`: si el
cuerpo lo es, **no** se pone `Content-Type` —lo escribe el navegador con su `boundary`— y va tal
cual. Es el único cambio en el cliente compartido y sigue poniendo CSRF y credenciales, que es
para lo que existe. Un usuario normal no puede tocar nada de esto: todo el panel es `IsAdminUser`
y hay un test que lo comprueba recorriendo el router.

**Verificación.** Siete tests de API (subida válida, que no espera al troceado, ejecutable
renombrado a `.pdf`, fallo de OpenAI, borrado remoto, borrado remoto fallido, límites), ocho de
`rag` (`start_indexing`, `refresh_status` y `delete_document`) y seis de la pantalla. Y a mano en
Chrome, contra OpenAI de verdad: la subida responde en **3,4 s** —antes colgaba hasta el *broken
pipe*—, el estado pasa de «Indexando» a «Indexado» sin recargar, el borrado quita el archivo de la
cuenta de OpenAI, y un `.exe` renombrado a `.pdf` se rechaza **con el mensaje del validador en el
campo del archivo**: «se esperaba application/pdf y se encontró application/x-msdownload».

---

## ADR-054 — El reparto semanal es un dato que se valida, no una frase en las notas
**Fecha:** 2026-09-21 · **Estado:** aceptada · **Matiza ADR-008 y ADR-030**

**Contexto.** Una generación real (auditoría nº 10) pidió por escrito «lunes pecho, tríceps y
hombros; martes espalda, bíceps y antebrazo; miércoles pierna con énfasis en cuádriceps; los otros
días tren superior; el último femorales; 8 ejercicios». Salió un plan de seis días con rutinas de
4, 3, 2, 2 y 2 ejercicios, el día de tríceps **sin un solo ejercicio de tríceps** y un curl de
muñeca dentro. Al mirarlo de cerca no era el modelo eligiendo mal:

- **La lista de candidatos no tenía de dónde elegir.** `select_candidates()` repartía 22 ejercicios
  **por zona del cuerpo** y ordenaba por equipamiento y luego alfabéticamente. «upper legs» son
  cuádriceps, isquiotibiales y glúteos a la vez: sus 22 huecos se los comían quince variantes de
  sentadilla y glute bridge con barra, y el corte caía en «barbell lying…». De 178 candidatos con
  gimnasio completo, **3 eran de cuádriceps y 1 de isquiotibiales**, cuando el catálogo tiene 44 y
  28. Los 22 de antebrazos y los 22 de gemelos sí estaban enteros. Y como la prioridad de
  equipamiento se aplicaba **vaciando** el cubo de barra antes de pasar al siguiente, no llegaba
  ni una polea ni una máquina: ni jalón, ni prensa, ni curl femoral.
- **Nadie comprobaba que el plan fuera el pedido.** `validate_plan()` miraba identificadores, siete
  días, nombres únicos y rutinas no vacías. Un día que no cubre lo que su propio nombre anuncia
  pasaba entero.
- **El formulario y el texto se contradecían y ganaba quien quisiera.** El campo «días por semana»
  decía 3; el texto pedía seis. Nada resolvía el conflicto porque el reparto solo existía en prosa.
- **No había ninguna noción de recuperación**, ni en el prompt ni en la validación.

**Decisión.**

- **El reparto se elige día a día en la pantalla** y viaja como dato (`apps/aiassist/services/
  split.py`): músculos por día, énfasis opcional y número exacto de ejercicios. Sustituye al campo
  «días por semana», que era la mitad del conflicto. El texto libre se queda para lo que sí es
  texto —«los viernes tengo poco tiempo»— y sigue entrando delimitado como dato (ADR-010).
- **La cuota de candidatos pasa a ser por músculo objetivo**, no por zona: 18 por músculo pedido y
  28 para el de énfasis, cogiendo **una ronda por cada tipo de material** en vez de vaciar la barra
  primero, los compuestos delante, y colapsando las variantes cosméticas del dataset —`(male)`,
  `(back pov)`, `(side pov)`—, que son la misma sentadilla ocupando tres huecos. Con reparto solo
  entran los músculos que se van a entrenar: la lista sube a 260 líneas y a la vez se abarata,
  porque ninguna se gasta en un músculo que no toca.
- **El plan se valida contra el reparto**: días exactos, recuento exacto por día, un ejercicio
  **primario** por cada músculo nombrado, el énfasis con dos o más y ninguno por encima, y sin
  ejercicios repetidos en una rutina. Cada fallo lleva su corrección apuntada en `FIXES`, que es lo
  que hace útil el reintento que ya existía.
- **48 horas para el mismo músculo**, no 24. Veinticuatro bastan **entre grupos distintos**; el
  mismo grupo dos días seguidos entrena sobre fibra que aún se repara. Se exceptúan abdominales,
  oblicuos, gemelos y antebrazos: fibra lenta, recorrido corto y poco daño por sesión, y
  bloquearlos sería aplicar una regla verdadera donde no aplica. La semana se trata como un ciclo,
  así que domingo y lunes también son consecutivos.
- **El reparto se comprueba antes de llamar al proveedor.** Un reparto que incumple las 48 h no lo
  puede arreglar el modelo sin desobedecer: pedírselo sería gastar una generación para rechazar
  tres respuestas. Responde 400 con código `reparto` o `descanso`, y no gasta cupo.
- **`AIGeneration.request_params` guarda lo pedido.** Diagnosticar todo esto fue posible porque el
  prompt quedaba guardado; el reparto en prosa había que leerlo a ojo entre las notas.

**Consecuencias.** No se puede generar sin marcar al menos un día: el reparto ya no se adivina.
Los músculos que se ofrecen salen de `musculos_entrenables()`, que cuenta **solo el músculo
objetivo y solo con el material declarado** —contar los secundarios ofrecería un día de bíceps que
luego no se puede cubrir—. El endpoint sigue aceptando peticiones sin reparto, con el
comportamiento anterior, pero también ese camino se beneficia de la cuota por músculo. Nada de
esto arregla el modelo: la configuración activa era `gpt-4o-mini` con `effort=low`, y esa parte es
del admin, no del código.

**Verificación.** 47 tests de generación (cuota por músculo, variedad de material, colapso de
variantes, y un caso por cada validación nueva), 23 del reparto y 35 de la API. La comprobación
que cierra el diagnóstico se hace contra el catálogo real: pedir cuádriceps con énfasis devolvía 3
candidatos de un solo material y ahora devuelve 28 de cinco.

---

## ADR-053 — Descartar cambios se pregunta en un panel de la aplicación, no con `window.confirm`
**Fecha:** 2026-09-21 · **Estado:** aceptada · **Matiza ADR-051**

**Contexto.** La guardia de cambios sin guardar —salir del editor y cerrar sesión con un borrador a
medias— preguntaba con `window.confirm`. Era el único trozo de interfaz que no pintaba la
aplicación, y se notaba: ignora el tema y la tipografía, sus botones salen en el idioma del sistema
(«OK»/«Cancel») en vez de decir qué hace cada uno, en móvil aparece pegado al borde superior con el
nombre del dominio encima, y bloquea el hilo, así que ningún estado de carga ni ninguna animación
sigue viva detrás. Chrome además deja de mostrarlo si se repite mucho en la misma página: la
protección desaparecía sin avisar justo cuando más se usaba.

**Decisión.** `ds/Confirmacion.tsx`, montado sobre `Panel`, con texto propio para cada acción
(«Salir sin guardar» / «Seguir editando»). Escape y la ✕ **cancelan**, y el foco inicial va al
botón de cancelar: un diálogo destructivo se descarta, no se acepta por inercia.

Lo pinta el proveedor `CambiosPendientes`, no cada pantalla, porque la misma pregunta sale al
navegar desde el editor y al cerrar sesión desde Cuenta. Y `confirmar()` pasa a devolver una
**promesa**: un diálogo de la aplicación no puede parar el hilo, así que quien pregunta espera la
respuesta. Eso obliga a partir en dos lo que antes decidía `useBlocker` de una vez: el enrutador
solo decide **bloquear** (hay cambios y la URL cambia) y la pregunta se hace en un efecto, que
llama a `proceed()` o a `reset()` cuando llega la respuesta. La pregunta en curso vive en un ref
para que dos llamadas seguidas compartan diálogo; si cada una abriera el suyo, la primera promesa
se quedaría sin resolver y la navegación no volvería a moverse.

Recargar o cerrar la pestaña **sigue siendo el cuadro del navegador**: `beforeunload` no admite
otra cosa, y ahí el mensaje lo elige el navegador.

**Consecuencias.** Al cerrar sesión con cambios pendientes quedan dos diálogos apilados —Cuenta
debajo, el aviso encima—; la capa superior del `<dialog>` nativo ya lo resuelve, y Escape solo
cierra el de arriba. Los tests dejan de espiar `window.confirm` y pulsan botones de verdad, que es
lo que hace un test capaz de notar que el diálogo no se ve. Cualquier confirmación nueva sale de
este componente en vez de escribir otro panel a mano.

**Verificación.** 237 tests de componentes (dos casos nuevos: quedarse y descartar en el editor, y
el aviso antes de cerrar sesión, que comprueba que no se manda el DELETE al quedarse) y 887 de
pytest. El recorrido de Playwright en Chrome cubre lo que jsdom no puede decir: los dos diálogos
apilados, Escape sobre el de arriba, el foco devuelto al botón que lo abrió y el `beforeunload`
todavía nativo.

---

## ADR-052 — Construir React también con Railpack y verificar la imagen antes de servir
**Fecha:** 2026-09-21 · **Estado:** aceptada · **Completa ADR-047**

**Contexto.** Un despliegue en Railway arrancó Gunicorn y completó `collectstatic`, pero respondió
500 porque faltaba `frontend/dist/.vite/manifest.json`. El log prueba la ausencia del artefacto,
no qué constructor se usó. El repositorio solo configuraba Nixpacks; Railway usa Railpack por
defecto, que lee `railpack.json` y no `nixpacks.toml`.

**Decisión.** `railway.toml` fija Railpack y el comando de construcción; `railpack.json` conserva
el proveedor Python y añade Node 22. `scripts/build-frontend.sh` instala con `npm ci --include=dev`,
compila React y comprueba el manifiesto, sus referencias y archivos. Lo comparten Railpack,
Nixpacks y el job Django de CI. La comprobación se repite al arrancar el proceso web, antes de
migrar, recolectar estáticos o aceptar tráfico. No necesita Django, BD ni credenciales.

**Consecuencias.** El bundle sigue fuera de Git y se genera dentro de la imagen. Una imagen sin
frontend falla con un mensaje accionable al construir/arrancar. `collectstatic` permanece en el
arranque; los comandos separados de web, worker y beat no se sobrescriben globalmente. El servicio
debe construir desde la raíz del repo. Confirmar la solución remota requiere desplegar el commit
nuevo; reiniciar la imagen antigua no añade el frontend.

Referencias: [Railpack](https://railpack.com/config/file/),
[configuración Railway](https://docs.railway.com/config-as-code/reference).

---

## ADR-051 — Experiencia OpenGym, Cuenta común y rutinas con borrador
**Fecha:** 2026-09-21 · **Estado:** aceptada · **Matiza ADR-031, ADR-043 y ADR-044** · **Matizada por ADR-061 y ADR-062**

**Contexto.** El cierre de sesión no era descubrible en móvil: estaba dentro de Perfil. La
creación manual pedía metadatos antes de mostrar el editor y persistía cada acción por separado.
El usuario pidió las composiciones e interacciones de su referencia local OpenGym, conservando
PROJECT_GYM y naranja, y eligió explícitamente guardar al final tanto al crear como al editar.

**Decisión.**

- Cuenta tiene una entrada etiquetada en el marco móvil, la barra lateral y el modo de entrenar.
  Un panel común ofrece Perfil, notificaciones, tema, Gestión para staff y Cerrar sesión.
  Conserva DELETE con CSRF, limpieza del caché y errores con reintento.
- Los tokens neutros pasan a negros y grises; se conservan fuentes locales, naranja, tema claro,
  contraste, cinco destinos y navegación lateral en escritorio. Listas compactas para Plan,
  ejercicios del editor e historiales; cabeceras comunes y estados vacíos más cortos.
- `Panel` usa `<dialog>.showModal()`: capa superior, fondo inerte, Escape y devolución del foco.
  Hoja inferior en móvil y diálogo centrado en escritorio. El buscador recibe foco explícito
  después de abrir, porque el autofocus de React se ejecuta antes de `showModal()`.
- El editor nuevo y el existente mantienen nombre, descripción y lista ordenada en memoria.
  Añadir/configurar/quitar/mover modifica el borrador. Solo Guardar persiste; un error conserva
  lo escrito. La interfaz exige nombre y al menos un ejercicio. No se usa localStorage.
- `POST /api/rutinas/` y `PATCH /api/rutinas/{id}/` admiten `exercises` opcional como lista completa:
  cada fila lleva `exercise`, `target_sets`, `target_reps_min`, `target_reps_max`, `rest_seconds`
  e `id` solo para elementos existentes. El índice establece el orden. Si se omite la lista,
  se conserva el contrato anterior; los endpoints individuales siguen disponibles.
- Validación antes de persistir, transacción atómica y bloqueo de la rutina durante edición.
  Se conservan IDs existentes, se crean los nuevos y se eliminan los retirados, sin modificar
  los registros de entrenamiento. IDs de elementos ajenos responden 404; IDs repetidos, 400.
- React Router utiliza un data router para `useBlocker`, manteniendo las URLs. Se confirma
  descartar antes de navegar o cerrar sesión; recargar/cerrar pestaña usa `beforeunload`.
  No hay recuperación del borrador tras aceptar una recarga: no es almacenamiento offline.
- Plan asigna los días en un panel y conserva la ruta directa anterior. Crear programa sigue
  siendo una decisión explícita. La IA conserva sus contratos y reglas.

**Consecuencias.** Ninguna migración de datos. La referencia guía diseño e interacción, sin añadir
superseries ni reglas nuevas de progresión. El guardado completo se distingue del parche individual:
una fila parcial se rechaza para no mezclar rangos nuevos con valores antiguos. Una operación
fallida revierte también el nombre, no solo los ejercicios.

**Verificación.** Pruebas de rollback, IDs ajenos, compatibilidad e historial; componentes con
borrador sin escrituras intermedias y recuperación de errores; recorridos reales de crear,
asignar, entrenar, salir, proteger cambios y foco. Matriz visual a 375/390/768/1440 px y dos temas.

---

## ADR-050 — La PWA es instalable y **no** funciona sin conexión
**Fecha:** 2026-09-20 · **Estado:** SUSTITUIDA por ADR-063 · **Completa ADR-047**

**Contexto.** Con la aplicación ya en React, convertirla en PWA es barato. El usuario lo pidió
explícitamente acotado: «solo instalable, sin offline». Había que decidir si respetarlo o «regalar»
una caché, que es la tentación evidente cuando ya hay un service worker registrado.

**Decisión.** Manifiesto, iconos y un service worker **que no cachea nada**.

- **El service worker existe solo porque Chrome lo exige.** Para ofrecer instalar hacen falta un
  manifiesto válido y un service worker registrado con un manejador de `fetch`. El nuestro tiene
  el manejador **vacío**: sin `respondWith`, el navegador sigue su camino normal a la red.
- **No cachear es la decisión, no una simplificación.** Una caché mal invalidada es el fallo más
  desconcertante que hay en una aplicación web: alguien despliega y una parte de los usuarios
  sigue viendo la versión anterior durante días, sin error en ninguna parte. Y aquí no compraría
  nada: **sin conexión no se puede registrar una serie**, porque el número de serie lo pone el
  servidor y el peso propuesto sale del historial. Una aplicación que deja «entrenar» sin red y
  después no puede guardarlo es peor que una que dice que no hay red.
- **Los dos archivos se sirven desde la raíz, con vistas de Django.** El alcance de un service
  worker es su propia ruta: desde `/static/js/sw.js` controlaría `/static/js/…` y nada más. Y el
  manifiesto tiene que resolver las URL de los iconos con `static()` —en producción llevan hash de
  `collectstatic`— y salir con `Content-Type: application/manifest+json`, que servido como archivo
  estático no está garantizado. Chrome ignora un manifiesto con el tipo equivocado **sin decir por
  qué**: la aplicación sencillamente no ofrece instalarse.
- **Hay un icono `maskable` además de los normales.** Android recorta el icono a la forma del
  lanzador —círculo, cuadrado redondeado, gota— y sin una versión con la marca dentro de la zona
  segura del 80 % recorta el normal, llevándose las esquinas de la placa.
- **Los iconos se generan desde los tokens** (`scripts/generar_iconos.py`) y se comitean. Generarlos
  en el despliegue obligaría a meter Pillow en la imagen de producción para producir cuatro
  archivos que no cambian nunca; dibujarlos a mano los dejaría con el naranja viejo el día que
  alguien retoque `--ember`, y nadie mira los iconos hasta que instala la aplicación.

**Consecuencias.** No hace falta tocar la CSP: `worker-src` y `manifest-src` caen por defecto en
`default-src: 'self'`, y los dos archivos son del propio origen. El registro va en un `catch`
silencioso: en desarrollo sin HTTPS falla y **no pasa nada** —la aplicación funciona igual, solo
que no se puede instalar—, y dejar que la promesa rechace llenaría la consola de un error que no
lo es, lo que haría fallar los recorridos de Playwright. Si algún día hace falta offline de
verdad, esto se sustituye entero y se escribe su ADR: no se le añade una caché a este.

---

## ADR-048 — El panel de gestión vive en la aplicación, y el `/admin/` de Django se conserva
**Fecha:** 2026-09-20 · **Estado:** aceptada · **Modifica `.docs/06-security.md` §2 y §6** · **Matizada por ADR-062**

**Contexto.** `.docs/06-security.md` afirmaba que `AIProviderConfig`, `PromptTemplate`,
`VectorStore` y `AIGeneration` «no tienen serializadores ni endpoints: solo admin, solo staff».
Era cierto y era cómodo, pero el `/admin/` de Django hace mal justo las tres cosas que se hacen a
diario en esta aplicación: probar una clave es una *acción de lista* que hay que buscar en un
desplegable, mirar por qué falló una generación es abrir una fila de solo lectura y leer un
`<textarea>` de mil líneas, y desbloquear una cuenta de django-axes está en otra sección entera.
El usuario pidió un panel propio con Forja, cubriendo cuatro áreas: IA, auditoría, usuarios y
catálogo.

**Decisión.** Se construye el panel en `/gestion/`, servido por la SPA, contra endpoints nuevos
bajo `/api/gestion/`. **Y el `/admin/` se conserva**: esto no lo sustituye. El panel es la
pantalla cómoda de lo que se hace cada semana; el admin es la red de seguridad para lo demás —y
para el día en que lo que esté roto sea el panel—. La barra lateral enseña los dos.

Seis condiciones, cada una por una razón concreta:

1. **`IsAdminUser` en todo, impuesto por una clase base** (`VistaDeGestion`) y comprobado
   recorriendo el router entero. Una lista de endpoints escrita a mano envejece, y el día que
   envejece deja de comprobar justo el que se acaba de añadir.
2. **La API key es `write_only`.** Lo que sale es `masked_api_key`. No es desconfianza del staff:
   una clave en una respuesta acaba en el historial del navegador, en una captura de pantalla y
   en el registro de cualquier proxy por el que pase. Editar el modelo o el tope de tokens no
   exige volver a pegarla.
3. **El área de usuarios no expone datos de salud.** Peso, altura, sexo, fecha de nacimiento y
   lesiones no están en el serializador. Administrar —ver quién se registró, desactivar una
   cuenta, desbloquearla— no requiere leer el historial médico-deportivo de nadie. Tampoco se
   cambian contraseñas ni correos: con el correo cambiado se pide un restablecimiento y se entra
   en la cuenta, y eso no es administrar.
4. **La auditoría sí expone el prompt y la respuesta cruda, pero solo en el detalle.** Es su razón
   de ser —sin ellos no se sabe por qué el modelo devolvió lo que devolvió— y a la vez el sitio
   donde más datos ajenos hay. En el listado no van: esa es la pantalla que se queda abierta en un
   portátil. Y no se pueden borrar: una auditoría que se edita no es una auditoría.
5. **Lo que se genera desde fuera no se edita aquí.** El catálogo de ejercicios viene de
   `import_catalog` y las métricas de `sync_metrics`: un cambio a mano se perdería en la siguiente
   ejecución y hasta entonces habría un panel mintiendo. De las métricas solo se tocan los tres
   interruptores que el modelo ya documenta como del admin.
6. ~~**Los documentos del RAG se suben desde el admin.**~~ **SUSTITUIDO por ADR-055**: la
   validación nunca estuvo duplicada —es una función que el serializador ya reutilizaba— y la
   pestaña sin almacenes era un callejón sin salida. Se conserva el texto original porque el valor
   de este registro está en poder reconstruir por qué el proyecto fue como fue.
   Subir un archivo se hace una vez al mes y
   con el archivo delante; duplicar aquí la validación por magic bytes habría dejado dos sitios
   que mantener sincronizados. Lo que sí está en el panel es **el estado**, que es lo que se
   consulta: cuántos indexados, cuántos fallidos y reintentar los que fallaron.

**Consecuencias.** `.docs/06-security.md` deja de poder decir que `AIGeneration` no tiene
endpoints, y se actualiza con las dos condiciones que lo hacen aceptable. El panel no protege
nada por sí mismo —esconder un enlace no es proteger—: la comprobación de `is_staff` en el cliente
existe para enseñar una pantalla que lo explica en vez de cinco secciones cargando y fallando a la
vez. Probar una clave **cuesta dinero** y queda registrado como `kind=test`, para que el gasto
cuadre.

---

## ADR-049 — El entrenamiento termina en una pantalla, no en una redirección
**Fecha:** 2026-09-20 · **Estado:** aceptada

**Contexto.** `session_finish` era un POST que marcaba la hora y redirigía al historial. Media hora
de trabajo terminaba en una lista donde la sesión recién cerrada era una fila más, con la misma
tipografía que las de hace tres meses. Todo lo que hacía interesante ese momento —cuánto se
levantó, si se batió algún récord, qué se trabajó— estaba en la base de datos y no se enseñaba en
ningún sitio.

**Decisión.** Cerrar un entrenamiento lleva a `/entrenamientos/{id}/cierre/`: duración, series,
tonelaje, **récords batidos**, músculos trabajados y las notas. El resumen se puede pedir sin
cerrar (`resumen/`) para que recargar la pantalla no dependa de volver a escribir la hora.

Dos reglas sobre qué se cuenta, que es donde está el contenido de la decisión:

- **Un récord es superar lo anterior, y un ejercicio nuevo no lo es.** Se compara contra las
  series de **otras** sesiones: si se comparara dentro de la misma, la segunda serie de hoy sería
  récord por superar a la primera y cualquier sesión progresiva sería una ristra de insignias. Y
  un ejercicio que nunca se había hecho se excluye: el primer día todo sería récord y la insignia
  dejaría de significar nada.
- **El tonelaje no se recalcula.** Sale de `total_work()`, que ya cuenta los dos lados de un
  unilateral y el peso corporal de una dominada. Las series de peso corporal sin ningún pesaje
  registrado **no suman cero**: se dice cuántas quedan fuera, porque un cero se leería como «no
  levantó nada».

**Consecuencias.** `finalizar/` devuelve el resumen en vez de un 302, y llamarlo dos veces no
alarga el entrenamiento —la hora se fija la primera vez—. La aritmética vive en
`apps/workouts/focus.py::resumen_de_cierre` con sus tests; la pantalla solo pinta.

---

## ADR-046 — La sesión de la web va en cookie, no en un JWT guardado en el navegador
**Fecha:** 2026-09-19 · **Estado:** aceptada · **Matiza ADR-012**

**Contexto.** Con el frontend en React (ADR-047) había que decidir cómo se autentica. El camino
que parece natural en una SPA es pedir un JWT y guardarlo —`localStorage`, `sessionStorage`— y
mandarlo en una cabecera. El proyecto ya tiene SimpleJWT montado desde ADR-012.

**Decisión.** La web usa **la sesión de Django**, que ya viajaba en una cookie `HttpOnly`
(`SESSION_COOKIE_HTTPONLY`, `SameSite=Lax`). DRF ya tenía `SessionAuthentication` en la lista, así
que no hubo que tocar un solo setting: solo hacían falta los endpoints
(`apps/api/auth.py`).

La razón es el modelo de amenaza, no la comodidad. Un token en `localStorage` **lo lee cualquier
script que consiga ejecutarse** en la página; una cookie `HttpOnly` no. Lo que hay detrás de esta
autenticación son datos de salud (`.docs/06-security.md` §8). A cambio hay que ocuparse del CSRF,
que la cookie sí trae de vuelta — y eso es un problema resuelto desde hace veinte años.

**SimpleJWT se queda intacto** para clientes que no son la web: ADR-012 sigue vigente y
`/api/auth/token/` no cambia. Lo que cambia es que deja de ser el camino del navegador.

**Cuatro detalles que costaron, y ninguno se ve.**

1. **`csrf_protect` en entrar y en registrarse.** `APIView.as_view()` envuelve la vista en
   `csrf_exempt`, y la protección la reintroduce `SessionAuthentication` **solo cuando consigue
   autenticar**. En el inicio de sesión todavía no hay sesión, así que el POST se queda sin
   ninguna defensa: es el CSRF de login, con el que un tercero te mete en *su* cuenta y todo lo
   que registres a partir de ahí cae ahí. Entrar funciona igual de bien con el agujero abierto, y
   por eso hay un test —el único con `enforce_csrf_checks=True`— a cada lado de la comprobación.

2. **El bloqueo de django-axes hay que preguntarlo aparte.** `AxesStandaloneBackend` levanta
   `AxesBackendPermissionDenied` cuando la cuenta está bloqueada, pero
   `django.contrib.auth.authenticate()` **atrapa** `PermissionDenied`, corta el bucle de backends
   y devuelve `None` — exactamente lo mismo que una contraseña incorrecta. Atrapar la excepción en
   la vista no sirve porque nunca llega. Se consulta `AxesProxyHandler.is_allowed()` antes. Sin
   eso el bloqueo existe pero se anuncia como «usuario o contraseña incorrectos», y quien lleva
   una hora esperando sin saberlo sigue probando.

3. **El `?next=` se valida en el servidor.** Sin `url_has_allowed_host_and_scheme` es una
   redirección abierta: el enlace parece del dominio bueno, la contraseña se teclea en el
   formulario de verdad, y a quien acaba de entrar se le deposita —ya convencido— en una página
   ajena. Y **después de entrar se navega de verdad, no se enruta**: mientras dure la transición
   el destino puede ser una pantalla de Django.

4. **La respuesta de sesión no lleva datos de salud.** Es la que se pide en cada arranque y en
   cada recuperación, así que lo que entre ahí acaba en más sitios de los que nadie va a repasar.
   Peso, altura, sexo, fecha de nacimiento y lesiones salen por `/api/perfil/`, que se pide al
   abrir el perfil y solo entonces.

**Consecuencias.** `/entrar/` y `/registro/` los sirve la SPA; se borran `registration/login.html`,
`accounts/register.html`, la vista `register` y `RegisterForm`. **`/salir/` sigue siendo la vista
de Django** mientras queden plantillas: su barra lateral tiene un `<form method="post">` apuntando
ahí, y moverla dejaría ese formulario renderizando la aplicación en respuesta a un POST **sin
cerrar la sesión**, sin fallar. La SPA cierra sesión con `DELETE /api/auth/session/` y va a
`/sesion-cerrada/`, que es una pantalla nueva: antes, salir devolvía al formulario de acceso sin
decir nada, y ese formulario es el mismo que aparece cuando caduca la sesión.

Al salir se vacía el caché entero de TanStack Query, no solo la sesión: lo que hay dentro son el
plan, los entrenamientos y el peso de quien acaba de salir, y en un móvil compartido en un
gimnasio eso no es hipotético.

---

## ADR-047 — El frontend pasa a React: Vite construye, Django sirve, `assets/app.css` sigue mandando
**Fecha:** 2026-09-19 · **Estado:** aceptada · **Sustituye a ADR-019** · **Matiza ADR-011 y ADR-029** · **Matizada por ADR-060**

**Contexto.** El usuario pidió «componentes tipo React». Se le planteó la alternativa barata —una
capa de componentes en las propias plantillas, con `django-cotton` o con `include`— y eligió React
de verdad, SPA sobre la API, con el aviso por delante de lo que costaba.

El diagnóstico que llevó ahí es real aunque la causa no fuera la que parecía. Forja ya estaba
aplicado (ADR-044): tokens conmutables, tipografía autoalojada, veinte pares de contraste medidos.
Lo que no había era **capa de componentes**. `templates/styleguide.html` documenta trece componentes
con nombres de React —`Button`, `StatTile`, `SetRow`, `RestTimer`, `EmptyState`…— pero existían solo
como clases CSS, y cada una de las 33 plantillas reescribía el marcado a mano. Cambiar un componente
era buscarlo por 33 archivos.

**Decisión.** Vite construye el bundle, Django lo sirve y le pone la sesión, el nonce y el
manifiesto de `collectstatic` por encima. Cinco decisiones dentro de esa:

1. **`assets/app.css` no se toca y sigue siendo la fuente.** Tailwind pasa del binario standalone
   al plugin `@tailwindcss/vite`, pero lee **el mismo archivo**. Durante la transición se compila
   dos veces —el binario para las plantillas que quedan, Vite para el bundle— y escanea las dos
   mitades (`@source "../frontend/src"` junto a `../templates` y `../apps`). Escanear solo una
   dejaría media aplicación sin estilo sin que fallara un test: el marcado sería correcto, lo que
   faltaría es la regla.

   Lo que esto compra es que **`apps/common/tests/test_design_system.py` no cambia ni una línea**:
   la paridad de tokens entre temas, la prohibición de colores en crudo dentro de `@utility` y los
   veinte pares de contraste siguen midiéndose sobre el archivo de verdad.

2. **La CSP no se relaja en producción.** Los bundles son archivos del propio origen con nombre
   hasheado, React no necesita ningún script inline y el estado inicial **no viaja en
   `json_script`** sino en una llamada a la API al montar. `script-src` se queda en `'self'`.
   La apertura a `:5173` —módulos, websocket de HMR, fuentes— vive **solo en `dev.py`**, y solo
   si hay `VITE_DEV_SERVER_URL`.

   El nonce se pide **únicamente** en ese modo, y por un motivo que no se ve: en django-csp,
   *leer* `request.csp_nonce` es lo que hace que el centinela `NONCE` acabe en la cabecera. Si no
   se lee, se cae de la directiva. Pedirlo siempre metería un `'nonce-…'` en producción, donde no
   hay un solo inline que lo use — y una directiva con nonce es **más permisiva** que una sin él.
   No se notaría en nada: la aplicación funciona igual de bien con la CSP aflojada. Lo vigila
   `TestElNonceSoloExisteEnDesarrollo`, sobre la cabecera y a través del cliente, que es lo único
   que ejecuta el middleware; con `RequestFactory` el atributo ni existe y el test pasaría sin
   mirar nada. Comprobado por mutación.

3. **El modo lo decide `VITE_DEV_SERVER_URL`, no `DEBUG`.** Los fallos que rompen en producción
   —orden de carga de la hoja, rutas con hash, prefijo `base`— son justo los que el servidor de
   desarrollo esconde, y hay que poder mirarlos con `DEBUG=True`.

4. **El bundle no se comitea**, al revés que el CSS de ADR-019. Esa decisión existía para que
   producción no necesitara el binario de Tailwind; ahora hay un paso de Node en CI y en el
   despliegue (`nixpacks.toml`), así que comitear el artefacto solo serviría para que se quedara
   viejo. El CSS compilado **sí sigue comiteándose** mientras queden plantillas.

5. **Sin `django-vite`.** Lo que hacía falta son treinta líneas de leer un JSON
   (`apps/common/vite.py`), y a cambio de la dependencia habría que aceptar sus decisiones sobre
   prefijos y nonce.

**Dos trampas encontradas al montarlo, las dos mudas.**

1. Las rutas de `@font-face` de `assets/app.css` son relativas a la **salida** del binario
   (`static/css/app.css`), no al archivo fuente. Desde `assets/` apuntan a `<raíz>/fonts/`, que no
   existe. Vite las resuelve desde el fuente y el build fallaba. Se corrige con un plugin de seis
   líneas y **no** cambiando el archivo, que es lo que habría dejado sin tipografía a las
   plantillas que aún sirve Django.

2. **`base` también manda en el servidor de desarrollo.** Con `/static/spa/` fijo, Vite solo
   respondía bajo ese camino y `apps/common/vite.py` pedía `:5173/src/main.tsx` recibiendo un 404.
   `base` pasa a depender de `command`: el prefijo solo al construir, que es cuando sirve Django.

**Lo que NO cambia.** ADR-011 sigue en pie: ningún script de terceros, nada por CDN, todo del
propio origen. Siguen las tres desviaciones de contraste de ADR-044, el arranque de tema antes de
pintar con `theme.js` —ese trabajo no se puede mover a React, que monta después de que el navegador
haya pintado— y `@source inline` para las clases de tiempo de ejecución (ADR-024).

**Lo que se pierde, dicho en voz alta: las pantallas migradas ya no funcionan sin JavaScript.**
Hasta ahora todo lo animado era un añadido y lo de debajo servía por sí solo —asignar un día era
un `<form>` con radios, filtrar el catálogo eran enlaces, y `apps/common/tests/test_motion.py` lo
vigilaba—. Una SPA no arranca sin JavaScript, y eso incluye a quien lo tenga desactivado, a quien
use un navegador viejo y a cualquier rastreador. Es inherente a la decisión, no un descuido: se
anota aquí para que nadie lo descubra como si fuera un fallo. Las pantallas que **todavía** son de
Django mantienen su comportamiento, y su test sigue en pie.

**Consecuencias.** Ejecutar la aplicación **exige** construir el frontend: `frontend/dist/` está en
`.gitignore` y sin él `{% vite %}` levanta `ImproperlyConfigured` — con el comando que hay que
ejecutar en el mensaje— y **`pytest` falla** en los tests que recorren pantallas migradas. Por eso
CI construye el bundle antes de los tests y no en un job de al lado.

El despliegue necesita `nixpacks.toml`: Nixpacks detecta el lenguaje por los archivos de la raíz,
encuentra `requirements.txt` y `frontend/package.json` le pasa desapercibido. Sin el archivo, la
imagen sale sin Node, el despliegue funciona, `collectstatic` no se queja —`STATICFILES_DIRS` solo
incluye `frontend/dist` si existe— y lo que falla es la primera pantalla migrada que alguien abra.

Queda una cosa sabida y no resuelta, para cuando aparezca la primera ruta con carga perezosa:
Django no reescribe los `import` de un módulo JS (`support_js_module_import_aggregation` es `False`
y Whitenoise no lo cambia). Los trozos con nombre sin hashear también se recolectan, así que las
importaciones resuelven; lo que se pierde es la caché larga en esos archivos, no el funcionamiento.

---

## ADR-045 — El mapa corporal: anatomía vendorizada, mapeo en Python y coloreado propio
**Fecha:** 2026-09-16 · **Estado:** aceptada

**Contexto.** Faltaba la pregunta que se hace primero al abrir una aplicación de gimnasio: **qué
músculo es cada cosa**. El catálogo se filtraba con dos `<select>` de texto, la ficha de un
ejercicio decía «Dorsales, Bíceps» en una línea que hay que leer y traducir mentalmente a una parte
del cuerpo, y Progreso no tenía forma de enseñar el reparto de la semana.

El modelo ya lo soportaba entero: `MuscleGroup` con 30 músculos canónicos, `Exercise.target_muscle`
y `secondary_muscles`, y `muscle_contributions()` repartiendo 1.0 al objetivo y 0.5 a los que
ayudan. Lo que faltaba era el dibujo.

**Decisión.**

1. **La anatomía se vendoriza, no se dibuja.** 89 trazados de
   [`vulovix/body-muscles`](https://github.com/vulovix/body-muscles) (Apache-2.0, © 2024 Ivan
   Vulović) en `apps/workouts/bodymap/`, con `LICENSE`, `NOTICE` y `LEEME.md` documentando qué se
   cambió, que es lo que pide esa licencia al redistribuir.

   Se descartó la alternativa MIT más conocida (`HichamELBSI/react-native-body-highlighter`) porque
   **no separa los dorsales**: los mete dentro de `upper-back`. En una aplicación de gimnasio el
   dorsal es el objetivo de todo tirón del catálogo, y no distinguirlo del trapecio habría vaciado
   de sentido la mitad del mapa. Tampoco trae serrato ni glúteo medio.

   **De openGym no se toma nada**, aquí ni en ningún sitio: es AGPL v3 y contaminaría la licencia
   del resto (ADR-022).

2. **La geometría es un dato y el mapeo también.** `paths.py` es generado y no se edita; qué región
   es qué músculo vive en `REGION_MUSCLE`, en `taxonomy.py`, donde ya estaba el resto de la
   taxonomía. La plantilla solo recorre. El renderizador TypeScript del original **no se usa**: el
   SVG lo arma Django y el coloreado, la interacción y la accesibilidad son propios.

3. **Todo el mapa habla en slugs**, con guion (`upper-back`), que es lo que guarda
   `MuscleGroup.slug` y lo que devuelve `muscle_contributions()`. No en nombres canónicos con
   espacios. Esto no es cosmética: ver «el fallo» más abajo.

4. **El filtro por músculo trae objetivo y secundarios**, con `.distinct()`. Quien toca el bíceps
   en el mapa espera ver también los remos que lo trabajan. El `.distinct()` no es precaución: el
   `LEFT JOIN` de la tabla intermedia devuelve una fila por músculo secundario y, con el `OR`,
   todas satisfacen la condición por el lado del objetivo — un ejercicio con dos secundarios sale
   dos veces, y con tres, tres.

5. **Además de la figura hay una fila de chips.** No es redundancia: el bíceps ocupa unos 14×30 px
   en un teléfono, por debajo del objetivo táctil de 44. El chip es el camino que se acierta con el
   pulgar, el que usa quien navega con teclado, y el único sitio donde caben los seis músculos sin
   región (cardio, tobillos, manguito rotador…). Van ordenados **por número de ejercicios**: con el
   orden anatómico, el primer chip visible era «Esternocleidomastoideo».

6. **Los cortes de intensidad son fijos** —5, 10 y 15 series efectivas por semana— y no cuartiles
   del propio historial, por el mismo motivo ya escrito para el calendario de actividad: con
   cuartiles, una semana floja se reescala para parecer normal y dos personas no pueden comparar. El
   0 es su propio nivel y no se mezcla con «poco».

**El fallo que justificó los tests.** `REGION_MUSCLE` apuntaba a `"upper back"` cuando
`MuscleGroup.slug` guarda `"upper-back"`. Resultado: la espalda alta **nunca se encendía**, por
muchas dominadas que se registraran, y `?muscle=upper back` devolvía cero ejercicios. No fallaba
nada: el marcado era correcto, la página devolvía 200 y el músculo simplemente salía apagado. Lo
mismo con los otros siete músculos de dos palabras.

Por eso `apps/workouts/tests/test_bodymap.py` cierra el círculo por los dos lados —toda región
tiene destino, todo músculo tiene región o está declarado fuera— y exige que ningún destino lleve
espacios. Las tres comprobaciones se verificaron por mutación.

**Hallazgo colateral (2).** Con `media/` en R2 (ADR-041), las imágenes del catálogo dejan de ser
del propio origen, y `base.py` declara `img-src: 'self' data:`: en producción **la CSP bloqueaba
las 1324 imágenes**. `prod.py` añade ahora `https://{AWS_S3_CUSTOM_DOMAIN}` a `img-src`, copiando
los tres niveles del diccionario en vez de mutarlos — `from .base import *` los comparte, y un
`.append()` habría metido el dominio de R2 también en la CSP de desarrollo y de los tests, que es
la misma trampa ya documentada para `STORAGES`.

**Hallazgo colateral.** Al revisar Progreso apareció otro fallo mudo, anterior a este cambio: las
vistas hacían `json.dumps()` **y** la plantilla aplicaba `|json_script`, que serializa otra vez. El
`<script>` llevaba una cadena de JSON, `JSON.parse` devolvía un `str` y `datos.labels` era
`undefined`: **Chart.js dibujaba los ejes y ninguna línea**, sin error en consola. Afectaba a la
gráfica de peso de Inicio y Progreso y a todas las métricas. Corregido y fijado con tests en
`apps/common/tests/test_chart_payloads.py`.

**Consecuencias.** El mapa es un solo componente en cuatro pantallas: filtra en Ejercicios y en el
selector de una rutina, y es de solo lectura en Progreso, Inicio y la ficha. Los `<select>` del
selector se fueron y con ellos la última pantalla que filtraba distinto al resto. La figura es una
sola para todo el mundo: **no se usa `user.sex`**, que es dato de salud (ADR-027), y los músculos
son los mismos.

---

## ADR-044 — «Forja»: tokens conmutables, tipografía autoalojada y las cifras en mono
**Fecha:** 2026-09-16 · **Estado:** SUSTITUIDA por ADR-061 · **Sustituye a ADR-042** · **Matiza ADR-043**

**Contexto.** El usuario trajo un sistema de diseño terminado —`DESIGN/forja-design-system.html` y
`DESIGN/forja-pantallas.html`, 560 renglones de CSS compartidos, 12 componentes y 4 pantallas de
referencia— y pidió aplicarlo. El proyecto ya tenía el suyo (ADR-042): acento volt, neutros oliva,
titulares condensados en mayúsculas y fondos con degradado radial y rayado diagonal. Son dos
lenguajes incompatibles; convivir no era una opción.

**Decisión.** Se adopta Forja entero **retokenizando**, no importando. Las clases `fj-*` no entran
al proyecto: se reescriben el `@theme` y las `@utility` de `assets/app.css` conservando los nombres
que las 33 plantillas ya usan (`btn`, `card`, `chip`, `badge`, `segmented`, `empty-state`…). Meter un
segundo juego de clases junto a Tailwind habría dejado las plantillas hablando dos vocabularios.

Cinco decisiones dentro de esa, cada una con su razón:

1. **Los tokens viven en `:root` y `@theme inline` los expone.** Sin `inline`, Tailwind *copia* el
   valor dentro de cada utilidad y `bg-surface-100` se congela en el color del tema oscuro. Con
   `inline` emite `var(--surface-100)` y la utilidad sigue al atributo de `<html>`. Es lo que hace
   que **casi todas las variantes `dark:` sobren**: había 43 renglones con `dark:` en 18 plantillas
   y quedan cero. La variante sigue declarada para el único caso que va a contracorriente del tema,
   `ex-media`, que necesita fondo blanco siempre.

2. **El tema lo decide un atributo, no el sistema operativo.** `data-theme` en `<html>`, con
   conmutador y `localStorage`. Forja arranca en oscuro y trata el claro como alternativa, así que
   no se consulta `prefers-color-scheme`. `static/js/theme.js` se carga **sin `defer` y antes de la
   hoja de estilos**: si se aplicara después de pintar, la página cambiaría de color delante del
   usuario en cada carga. Es un archivo y no un `<script>` inline porque `script-src` es `'self'` y
   un nonce cambia en cada respuesta, así que el navegador no podría cachearlo.

3. **Las fuentes se autoalojan.** `font-src: 'self'` (ADR-011) bloquea Google Fonts, y el fallo es
   silencioso: la aplicación se ve «casi bien» con la tipografía de respaldo. Archivo variable e IBM
   Plex Mono 500/600, subconjuntos `latin` y `latin-ext`, 126 KB en total, en `static/fonts/` con su
   procedencia y licencia en `LEEME.md`. Las rutas de `@font-face` son relativas a la salida y el
   manifiesto de Whitenoise las reescribe en `collectstatic`.

4. **Las gráficas pasan de acento a `steel`.** Forja tiene dos acentos y esa es la decisión que lo
   sostiene: ember es la acción, steel es el dato. Una serie de gráfica pintada del color del botón
   principal invita a pulsarla. El anillo de foco también va en steel: si fuera del color de la
   acción, un botón primario enfocado se confundiría con uno pulsado.

5. **Toda cifra que lea una persona va en mono tabular** (`metric-xl/md/sm`, `tag`, `num`). No es
   estética: es lo que impide que la columna de kg baile cuando HTMX reemplaza la tabla de series.

**Tres desviaciones respecto a lo que publica Forja, las tres por accesibilidad y las tres medidas.**

1. **El texto de campo se queda en 16 px**, no en los 15 px del sistema: por debajo de 16 px Safari
   en iOS hace zoom al enfocar y descoloca la página entera.

2. **`--line-strong` del tema oscuro pasa de `#6b6155` a `#6e6458`.** Forja afirma que ese color
   «cumple 3:1 sobre `surface-000` y `surface-100` en los dos temas». Sobre la tarjeta del tema
   oscuro da **2,89:1**, calculado, no estimado — y es el borde de todos los campos, chips y
   botones secundarios, a los que WCAG 1.4.11 les pide 3:1. Tres unidades de aclarado lo dejan en
   3,02:1 sin mover el matiz.

3. **`--ember` del tema claro pasa de `#c4491a` a `#b8461a`.** Sobre su propio `--ember-soft` daba
   **4,13:1**, y el texto del badge de récord mide 11 px: es texto normal y le tocan 4,5:1. El
   ajuste lo sube a 4,53:1 y de paso mejora el enlace (4,55 → 5,00) y el texto del botón primario
   (4,56 → 5,01).

Las tres quedan escritas en el propio `assets/app.css`, y las dos de color las vigila
`TestElContrasteSeCalcula`: veinte pares reales —texto, bordes de control, anillo de foco, series
de gráfica— contra los umbrales de WCAG 2.2, leyendo los valores del archivo. Una afirmación en la
documentación de un sistema de diseño no es una medición.

Lo que ese test **no** comprueba, a propósito: la separación entre verde de éxito y rojo de
peligro, indistinguibles en deuteranopia. Es inherente a la semántica y no se arregla cambiando los
tonos — se arregla con la palabra que va dentro de la insignia, que es lo que impone este sistema.

**Lo que NO cambia.** La marca sigue siendo PROJECT_GYM con la placa «PG» — de Forja se toma el
lenguaje visual, no el nombre. Siguen en pie los dos modos de navegación (ADR-034), las
composiciones por pantalla (ADR-043), los objetivos táctiles, la puerta de movimiento reducido, el
`min-w-0` de la tarjeta (ADR-038), `@source inline` para las clases de tiempo de ejecución
(ADR-024) y Tailwind standalone con el CSS comiteado (ADR-019).

**Consecuencias.** `apps/common/tests/test_design_system.py` vigila lo que rompe en silencio: que
los dos temas declaren el mismo juego de tokens, que ninguna `@utility` escriba un color en crudo,
que el contraste de los veinte pares reales cumpla WCAG, y que los `.woff2` que nombra el CSS
existan. Un token presente en un tema y ausente en el otro no se nota hasta que alguien conmuta, y
entonces algo queda invisible; un `@font-face` roto hace que el navegador caiga a la fuente de
respaldo sin decir una palabra.

El formato del avance cambió de `2/9 series` a `2 / 9 series` —es como escribe el valor el
componente ProgressBar de Forja— y con él la afirmación de `test_focus.py`.

---

## ADR-043 — Cada pantalla principal necesita una composición propia
**Fecha:** 2026-09-16 · **Estado:** aceptada · **Amplía ADR-042** · **Matizada por ADR-064**

**Contexto.** El primer pase del rediseño cambió identidad, color, tipografía y superficies, pero
mantuvo casi intacta la estructura de varias páginas. El resultado era técnicamente distinto y aun
así se percibía igual: Plan seguía siendo siete tarjetas, Ejercicios seguía siendo una lista y los
historiales seguían siendo tablas dentro de otra tarjeta.

**Decisión.** Los componentes compartidos siguen resolviendo consistencia, pero las pantallas de
alto uso reciben composiciones específicas según su tarea: Plan es un tablero semanal numerado;
Ejercicios es un catálogo visual de tres columnas; Progreso separa consistencia, tendencia y
métricas en un bento; Entrenamientos es un diario cronológico; Peso, Perfil y Notificaciones tienen
cabeceras y jerarquías propias. En móvil esas composiciones vuelven a una columna sin perder la
barra inferior ni los objetivos táctiles.

El enlace del CSS lleva además una versión explícita durante este rediseño. En producción el
manifest ya cambia el nombre del archivo, pero en desarrollo `?v=20260916-2` evita que una caché
del navegador haga parecer que nada cambió.

**Consecuencias.** La interfaz ya no depende de que un cambio de paleta cargue con toda la
personalidad del producto. Hay algo más de marcado específico por pantalla, pero la interacción,
los datos, las URLs y los controles siguen siendo los mismos. La rama sin programa conserva la
biblioteca de rutinas; un test de autorización detectó esa regresión durante el cambio.

---

## ADR-042 — Identidad «performance editorial» sobre el sistema compartido
**Fecha:** 2026-09-16 · **Estado:** ~~aceptada~~ **SUSTITUIDA por ADR-044**

**Contexto.** Las pantallas ya eran funcionales, accesibles y responsive, pero el conjunto seguía
pareciendo una colección de componentes neutros: azul estándar, tarjetas planas, tipografía de
sistema sin carácter y la misma intensidad visual para casi todo. Mejorar una plantilla aislada
solo habría hecho más evidente la diferencia con las demás.

**Decisión.** La identidad vive en `assets/app.css`, no repartida pantalla por pantalla: tinta
mineral, marfil cálido y verde volt; `Bahnschrift Condensed`/`Aptos Display` para titulares con
fallbacks locales; patrón diagonal sutil; superficies con profundidad; botones con rotulación
técnica; y una placa `PG` como gesto de marca. Navegación, formularios, tarjetas, estados vacíos,
métricas y gráficos heredan el mismo lenguaje. Solo Inicio y acceso reciben composiciones propias,
porque son la bienvenida diaria y la primera impresión respectivamente.

No se añaden fuentes, imágenes ni scripts remotos. Se mantienen la CSP, Tailwind standalone
(ADR-019), los dos modos de navegación (ADR-034), los objetivos táctiles y la puerta de movimiento
reducido. El acento conserva contraste AA: `#4d7c0f` sobre `#fffef8` da 4,94:1 y `#bef264` sobre
`#1a1d18` da 13,04:1. El verde de éxito pasa a turquesa para no confundirse con la marca.

**Consecuencias.** Cambiar el carácter global sigue siendo una edición del sistema, no una búsqueda
por 25 plantillas. Login y registro comparten la misma composición editorial; la barra lateral y el
dashboard usan la marca nueva; el resto mejora por herencia sin duplicar estructura. El CSS
compilado continúa versionado y producción no necesita herramientas de frontend.

---

## ADR-041 — `media/` en Cloudflare R2: el disco de una PaaS es efímero y un Volume no se comparte
**Fecha:** 2026-09-16 · **Estado:** aceptada · **Sustituye la parte de `media/` de ADR-040**

**Contexto.** ADR-040 arregló los 404 de las imágenes del catálogo sirviendo `media/` con
Whitenoise desde un Volume de Railway. Se desplegó y **funcionó**: las 1324 imágenes se veían, con
caché larga y compresión. Lo que apareció después no fue un fallo, fueron dos límites del diseño:

1. **El disco de una PaaS es efímero.** Sin Volume, cada redeploy borraba los 138 MB del catálogo
   y había que volver a correr `import_catalog`. El Volume tapaba esto.
2. **Un Volume solo se monta en UNA instancia**, y eso el Volume no lo tapa. El día que el servicio
   `web` tuviera dos réplicas, la segunda serviría 404 en cada imagen. La decisión de ADR-040 decía
   explícitamente «no se monta storage externo por ahora: no hace falta escalar todavía» — esto es
   ese «por ahora» cumpliéndose antes de lo previsto, y saliendo más barato moverlo con una sola
   réplica que con producción dependiendo de ello.

De regalo, cada imagen entraba a gunicorn solo para que Whitenoise la devolviera igual: trabajo del
proceso web gastado en archivos que no cambian desde que se importan.

**Decisión.** `media/` pasa a **Cloudflare R2** en producción, vía `django-storages[s3]`. R2 no cobra
por salida de datos, no tiene el límite de una instancia y sirve desde su CDN sin tocar gunicorn.
Todo lo específico vive en `config/settings/prod.py`; en desarrollo y en los tests `media/` sigue
siendo disco local, sin ninguna bandera que elegir.

1. **`STORAGES["default"]` → `storages.backends.s3.S3Storage`, solo en `prod.py`.** Los
   `ImageField`/`FileField` de los modelos no se enteran de dónde acaba el archivo, y
   `import_catalog` tampoco: sube a través de `default_storage` en vez de copiar contra
   `MEDIA_ROOT`, así que el mismo comando vale en los dos entornos. La versión anterior usaba
   `shutil.copy2`, que en R2 habría dejado el campo apuntando a un archivo que nunca se subió.
2. **Las variables se llaman `R2_*` aunque django-storages lea `AWS_*` por debajo.** El `.env` lo
   lee una persona, y no hay ninguna cuenta de AWS de por medio. `prod.py` hace la traducción.
3. **URLs públicas y permanentes, no firmadas.** `AWS_S3_CUSTOM_DOMAIN` con el dominio público del
   bucket y `AWS_QUERYSTRING_AUTH = False`: sin eso django-storages firma cada URL contra el
   endpoint de la API, que es lo contrario de lo que quiere un `<img src>` y de lo que cachea un CDN.
   `AWS_S3_FILE_OVERWRITE = True` porque los nombres son deterministas por `external_id`; con el
   valor por defecto, cada re-importación añadiría un sufijo aleatorio y dejaría 1324 huérfanos
   nuevos en el bucket.
4. **`R2_PUBLIC_DOMAIN` se valida al arrancar y no se corrige en silencio.** Sus dos errores
   típicos —escribirla con `https://` delante, o poner el endpoint de la API
   (`<id>.r2.cloudflarestorage.com`)— dan fallos **mudos**: la aplicación responde 200, el archivo
   está en el bucket y se abre pegando la URL a mano, y aun así no se ve ni una imagen. Se prefiere
   `ImproperlyConfigured` con el texto de cómo arreglarlo: corregir solo el esquema por nuestra
   cuenta dejaría vivo el del endpoint, cambiando un bloqueo de CSP por un 401 por imagen.
5. **La CSP de producción tiene que dejar entrar el bucket.** Con `media/` fuera del origen propio,
   el `img-src: 'self' data:` de `base.py` bloquea las 1324 imágenes — consola llena de errores de
   CSP y la aplicación contestando 200 a todo, que parece un problema de datos y no lo es. `prod.py`
   añade `https://{AWS_S3_CUSTOM_DOMAIN}`. No puede vivir en `base.py`: el dominio sale del entorno
   y en desarrollo no existe. Se descubrió al hacer el mapa corporal (ADR-045, hallazgo colateral 2).
6. **Los diccionarios se copian, no se mutan.** `STORAGES = {**STORAGES, …}` y los tres niveles de
   `CONTENT_SECURITY_POLICY`, nunca `STORAGES["default"] = …`. `from .base import *` no copia:
   deja `prod`, `dev` y `base` apuntando **al mismo objeto**. Mutarlo reescribe también el de
   `base`, y con él el de `dev` — que es el que corre en `pytest`. El backend de R2 se habría
   colado en los tests sin que nadie lo pidiera.
7. **`config/whitenoise.py` se borra.** `WhiteNoiseMiddlewareWithMedia` ya no tiene nada que servir.

**Consecuencias.**

- Un redeploy ya no borra el catálogo, y `web` puede escalar a varias réplicas cuando haga falta.
- **Cinco variables nuevas sin valor por defecto**: si falta una, la aplicación no arranca. Es
  intencionado —una app de producción a medio configurar es peor que una que no levanta— y por eso
  CI las pasa con valores de mentira que solo tienen que tener la forma correcta.
- **Hay que habilitar el acceso público del bucket en Cloudflare** (o conectarle un dominio propio).
  Sin eso no existe un `R2_PUBLIC_DOMAIN` válido y el resto de la configuración da igual.
- Aparece un modo de fallo que con el Volume no existía, y es el más caro de este bloque: **el shell
  de Railway no hereda el `DJANGO_SETTINGS_MODULE` que exporta `scripts/start-web.sh`**. Un
  `import_catalog` lanzado a mano desde ahí corre con `dev`, escribe las imágenes en el disco
  efímero, termina diciendo «1324 actualizados» tan tranquilo y deja un 404 por imagen. La causa
  queda a un despliegue de distancia del síntoma. Se ataja por dos lados: la variable se pone a
  nivel de servicio en Railway, e `import_catalog` **anuncia el destino antes de subir nada**
  (`bucket «…» (https://pub-….r2.dev)` o `disco local, /app/media`). Está en `.docs/05-runbook.md`.
- Lo demás de ADR-040 —gunicorn, el `Procfile` con sus tres procesos y `scripts/start-web.sh`—
  sigue vigente tal cual. Solo cae la parte de `media/`.
- Nada de esto se comprueba con `manage.py check --deploy`: lo cubre
  `apps/common/tests/test_deploy.py::TestMediaEnProduccion`, que importa `config.settings.prod` de
  verdad dentro de la suite que corre con `dev`.

---

## ADR-040 — Despliegue en Railway: gunicorn, Whitenoise sirve también `media/`, Volume para el catálogo
**Fecha:** 2026-09-15 · **Estado:** aceptada · **La parte de `media/` la sustituye ADR-041**

> Lo de gunicorn, el `Procfile` y `scripts/start-web.sh` sigue vigente tal cual. Lo de servir
> `media/` con Whitenoise **ya no**: se probó en producción, funcionó, y aun así se cambió a
> Cloudflare R2 al primer límite real (`config/whitenoise.py` ya no existe). Se deja el análisis
> completo abajo porque explica el problema original y por qué la primera solución bastaba para
> arrancar pero no para quedarse.

**Contexto.** El proyecto no tenía ni servidor WSGI de producción ni nada que le dijera a una PaaS
cómo arrancar: sin `gunicorn` en `requirements.txt`, sin `Procfile`. `manage.py runserver` no es
apto para producción y no hay ambigüedad ahí.

Tirando del hilo apareció algo más serio: **en producción las imágenes y GIFs del catálogo
devuelven 404 aunque el archivo exista en disco.** `config/urls.py` sirve `media/` con `static()`
**solo si `DEBUG=True`** — es la recomendación oficial de Django, `static()` no está pensada para
producción — y no hay ningún urlpattern equivalente para cuando `DEBUG=False`. El fallo es invisible
en desarrollo porque ahí `DEBUG=True` lo tapa; solo aparece el día que alguien despliega de verdad.

**Decisión.**

1. **`gunicorn`** en requirements. Sin opinión que defender: es el estándar para WSGI en producción.
2. **`scripts/start-web.sh`** migra, recolecta estáticos y arranca gunicorn, en ese orden, **dentro
   del propio proceso de arranque** — no como paso aparte del despliegue. No todas las plataformas
   tienen una release phase separada como la de Heroku, y así funciona igual en cualquiera.
   `--timeout 120`: `generate_routine()` llama al proveedor de IA **dentro** de la petición HTTP,
   con hasta tres intentos (ADR-039); el timeout por defecto de gunicorn (30 s) mataría el worker
   a mitad de una generación lenta.
3. **`Procfile`** con tres procesos — `web`, `worker`, `beat` — porque son eso: tres procesos. Sin
   `worker` la IA no procesa nada en segundo plano; sin `beat` el análisis de progreso programado
   no se dispara nunca. Los tres se dan de alta como servicios separados en Railway, apuntando al
   mismo repositorio.
4. **`config/whitenoise.py`**: `WhiteNoiseMiddlewareWithMedia` sirve `media/` igual que los
   estáticos —comprimido, con caché larga— en vez de montar un servicio aparte para una carpeta que
   no cambia tras importarse. Solo se sustituye en `prod.py`; en desarrollo sigue sirviendo
   `static()` como hasta ahora. **`MEDIA_ROOT`/`MEDIA_URL` se leen de `django.conf.settings` dentro
   del `__init__`, no importados arriba del módulo**: así respeta overrides hechos en tiempo de
   ejecución en vez de fijarse al valor que tuviera `config.settings.base` en el momento en que
   Python importó el archivo — el motivo real es simple, testabilidad, pero de paso es más correcto.
5. **`media/` necesita un Volume de Railway**, montado solo en el servicio `web` — es el único que
   lo lee, y un Volume no se comparte entre instancias. Sin él, cada redeploy borra los 138 MB del
   catálogo y hay que volver a correr `import_catalog`. **No se monta storage externo (S3) por
   ahora**: no hace falta escalar a varias réplicas todavía, y añadir credenciales de un proveedor
   más es superficie de ataque que no compensa hasta que haga falta.

**Un error de subclase real, documentado porque es fácil de repetir.** La primera versión de
`WhiteNoiseMiddlewareWithMedia` redeclaraba `def __init__(self, get_response=None, settings=None)`.
El valor por defecto de la clase base para `settings` es el `LazySettings` real de Django, no
`None`; redeclarar la firma pisaba ese valor por defecto con `None`, y el cargador de middleware de
Django instancia pasando solo `get_response`, así que `settings` siempre llegaba `None` y el
arranque reventaba. Se detectó cargando el WSGI app de verdad bajo `config.settings.prod`, no con
`manage.py check`, que no instancia middleware.

**Verificado por ejecución, no solo por `check`.** `manage.py check --deploy` pasaba con la
versión rota igual que con la buena: no instancia el WSGI app. Lo que lo encontró fue cargar
`config.wsgi.application` de verdad y, después, pedirle un archivo de `media/exercises/` real a
través de él (200, con las cabeceras de caché y el tamaño exacto del archivo en disco). Windows no
puede ejecutar gunicorn —usa `fork()`, no disponible ahí—, así que la verificación del proceso en
sí queda para cuando corra en el contenedor Linux de Railway.

> Lo que hay que recordar: **un `if settings.DEBUG` en una URL es una decisión de despliegue
> disfrazada de detalle de desarrollo.** No fallaba ningún test porque ningún test corre con
> `DEBUG=False` contra un archivo real de `media/`. Ahora `apps/common/tests/test_deploy.py` sí.

---

## ADR-039 — El calendario referencia rutinas por nombre: se resuelve con tolerancia, una sola vez
**Fecha:** 2026-09-15 · **Estado:** aceptada

**Contexto.** Una generación real falló así:

> El modelo no devolvió una rutina válida tras 2 intentos: estos días apuntan a rutinas que no has
> definido: Pierna, Tirón, Tren Superior; estos identificadores no están en la lista de candidatos:
> 0012

`RoutinePlan` describe las rutinas en una lista y el calendario en otra, y el día señala a su
rutina **por el nombre**. Eso es una cadena de texto libre que el modelo escribe **dos veces**, y
el esquema no puede hacer nada: Pydantic valida cada lista por su cuenta y no sabe que tienen que
casar. Una tilde de menos o una coletilla —«Pierna» donde arriba puso «Día de Pierna»— tira la
generación entera.

Y tirando del hilo salieron tres causas más, todas invisibles para la suite:

- **El prompt pedía un campo que ya no existe.** La regla 3 mandaba poner `is_rest_day` a true en
  los días de descanso; ese campo desapareció del esquema cuando la rutina pasó a asignarse a días
  (ADR-029). Se le pedía al modelo rellenar algo imposible, y lo que llegaba mal era justo el
  calendario. **Nunca dijo** que el nombre del día tuviera que copiar al de la rutina.
- **La corrección del reintento siempre decía lo mismo:** «usa identificadores de la lista»,
  incluso cuando el problema eran los nombres y los identificadores estaban bien. Se le repetía una
  instrucción que ya cumplía mientras el fallo real se quedaba sin explicar.
- **El intento fallido se guardaba sin la respuesta del modelo.** Solo el mensaje de error. Así que
  ante «apuntan a rutinas que no has definido: Pierna» no había forma de mirar cómo había llamado
  el modelo a esa rutina — el único dato que dice si el fallo es suyo o del emparejamiento.

**Decisión.**

1. **`resolve_routine_name()`**, en tres pasadas de menos a más permisiva: exacto → normalizado
   (sin tildes, sin mayúsculas, sin espacios de más) → contención única. **Se rinde antes que
   adivinar**: si un nombre encaja con dos rutinas es ambiguo y cuenta como no resuelto. Un día
   asignado a la rutina equivocada no se nota mirándolo —la semana se ve llena y coherente—, así
   que se prefiere el error visible.
2. **`resolve_schedule()` la usan la validación y el guardado.** `apply_plan` buscaba el nombre a
   pelo; bastaba que las dos formas de emparejar divergieran para que un plan aprobado se guardara
   con días vacíos, sin error y sin forma de saber por qué.
3. **El prompt corregido** (versión 2): fuera `is_rest_day`, y la regla que faltaba escrita —
   «copia el nombre carácter por carácter», descanso = nombre vacío.
4. **La corrección del reintento apunta al fallo**, elegida de una tabla por el texto del problema.
   Y **tres intentos** en vez de dos: la cuota se consume una vez por generación, no por llamada.
5. **El intento fallido guarda la salida del modelo.**

**Lo que NO se cambió.** El identificador `0012` existe en el catálogo (`assisted lying leg raise`,
equipamiento «assisted») pero no estaba entre los candidatos de esa persona, que no tiene ese
equipamiento. Rechazarlo es correcto: la lista cerrada es la defensa estructural de ADR-008 y
ADR-010, y ablandarla para que pasen ejercicios «que existen» rompería las dos.

> Lo que hay que recordar: **el prompt es parte del contrato del esquema, y no lo comprueba nadie.**
> Aquel `is_rest_day` sobrevivió a la migración del esquema porque ningún test lee el prompt. Ahora
> hay uno que comprueba que no pida campos inexistentes.

---

## ADR-038 — Desbordes horizontales: la tarjeta que se encoge y el calendario que se alinea
**Fecha:** 2026-09-15 · **Estado:** aceptada

**Contexto.** «Esto no es responsivo», con una captura: las tarjetas de Progreso cortadas por la
derecha, incluidas las que solo tenían texto, y un gráfico que era un rectángulo vacío de 224 px.

**El síntoma no estaba donde la causa.** Una tabla de `whitespace-nowrap` dentro de **una** tarjeta
ensanchaba su columna de rejilla; la columna ensanchaba la página; y entonces *todas* las tarjetas
—las trece— se salían de la pantalla. La que se veía peor no era la culpable.

La regla de CSS de fondo: **un hijo de rejilla trae `min-width: auto` y no puede encogerse por
debajo de su contenido**, y una pista `1fr` trae ese mismo mínimo automático. El
`overflow-x-auto` de la tabla no bastaba: quien no podía encogerse era la tarjeta, no la tabla.

El gráfico vacío era el mismo fallo un paso más allá: Chart.js mide su contenedor y le fija al
`<canvas>` ese ancho en píxeles. Con el contenedor ya desbordado, el lienzo se quedaba enorme y el
dibujo caía fuera de la pantalla — parecía que el gráfico no cargaba.

**Decisión.** Tres invariantes, y las tres se comprueban leyendo:

1. **`min-w-0` en `.card` y en `.chart-box`.** Son hijos de rejilla en casi todas las pantallas.
2. **Ninguna rejilla sin columnas declaradas para móvil.** `grid` + solo `sm:grid-cols-*` deja una
   columna implícita `auto`, que tampoco baja del contenido: se ve perfecta en el portátil donde se
   escribió y desborda en el teléfono. `grid-cols-1` la convierte en `minmax(0,1fr)`.
3. **Ninguna pista `fr` desnuda.** `grid-cols-[2fr_1fr_1fr]` → `minmax(0,2fr)…`.

`apps/common/tests/test_responsive.py` las vigila. **No afirman que se vea bien** —eso ningún test
lo puede decir—, afirman que no está el patrón que rompe.

**El calendario de actividad, aparte.** Dos fallos propios:

- Las etiquetas de mes se pintaban **todas seguidas** en una fila aparte, ignorando el índice de
  semana que Python ya calculaba: trece nombres encabalgados en el ancho de trece semanas,
  señalando a cualquier sitio menos a su mes. Ahora la etiqueta **viaja dentro de su columna**
  (`CalendarWeek`), en posición absoluta para sobresalir sin empujar, y un mes con menos de tres
  columnas se queda sin nombre antes que pisar al siguiente.
- Salían **en inglés**: `f"{fecha:%b}"` usa `strftime`, que mira la configuración regional del
  sistema operativo y no la de Django. Con `formats.date_format(fecha, "M")` salen «Sep», «Dic»,
  «Ene».
- Y **arranca por el final**: 53 columnas de semana no caben, así que se abría mostrando hace un
  año —meses vacíos de antes de registrarse— con lo que importa fuera de pantalla. Lo empuja
  `scroll-end.js`, que **no vive en `motion.js`** a propósito: aquel archivo se apaga entero con
  `prefers-reduced-motion` y esto no es una animación, es la posición inicial correcta.

> Lo que hay que recordar: **el desborde horizontal se diagnostica al revés que otros fallos.** Lo
> que se ve cortado casi nunca es lo que sobra de ancho.

---

## ADR-037 — Fuera las dos métricas que dependían del RPE
**Fecha:** 2026-09-15 · **Estado:** aceptada

**Contexto.** Al limpiar la pantalla de Progreso (ADR-036) quedó **una sola tarjeta en ámbar
permanente**, y tirando del hilo apareció el motivo: **ninguna plantilla pide el RPE**. La vista lo
lee del POST y el serializador de la API lo expone, pero por la web no hay dónde escribirlo. El
único campo de RPE del proyecto estaba en `styleguide.html` — el componente existía en la guía de
estilos y nunca se conectó a la pantalla real.

Consecuencias, las dos invisibles para la suite:

- **`average_rpe`** no podía tener datos jamás. Visible por defecto para todo el mundo.
- **`effective_sets_by_muscle`** calculaba bien su número, pero su cobertura era `series con RPE /
  series`: **0 siempre**. La tarjeta avisaba a perpetuidad de una precisión que no podía llegar.

**Decisión.** Retirar las dos antes que añadir un campo más a la pantalla de entrenar, que es la
que se usa de pie y con prisa y de la que ya se quitaron campos sin uso (ADR-030).

- `average_rpe` **se borra del registro**; `sync_metrics` desactiva la fila sin borrarla, así que
  las preferencias de quien la tuviera elegida sobreviven.
- `effective_sets_by_muscle` pierde `requires` y su cobertura pasa a 1. **No es una rebaja**:
  contar toda serie de trabajo es el «hard set» de la literatura, no una aproximación. La salvedad
  —que alguna serie pudo quedarse lejos del fallo— está ahora en la descripción, que es donde no
  cansa.
- **`SetLog.rpe` se queda.** La API lo acepta, el historial lo muestra y `is_effective_set` sigue
  descartando las series anotadas por debajo de 7. Si algún día se captura por la web, devolver la
  métrica es restaurar un bloque.
- `seed_demo` **deja una de cada seis sesiones sin cerrar**. Ese papel lo hacía el RPE: con todas
  las sesiones cronometradas la cobertura saldría al 100 % y el aviso ámbar no aparecería en
  ninguna pantalla de la demo. Nadie sabría que existe hasta que le tocara de verdad.

**Consecuencia.** Doce métricas en vez de trece, y el aviso de cobertura vuelve a significar algo.

> Lo que hay que recordar de aquí: **un requisito que ninguna pantalla puede satisfacer no es un
> aviso, es ruido permanente.** Y no se detecta desde dentro de la métrica —su aritmética estaba
> bien y sus tests en verde—, solo mirando la pantalla de alguien que acaba de registrarse.

---

## ADR-036 — Una tarjeta sin datos lo dice una sola vez, y un cero sin cobertura no es un cero
**Fecha:** 2026-09-15 · **Estado:** aceptada · **Matiza ADR-016**

**Contexto.** La pantalla de Progreso el primer día —la primera impresión de la aplicación— tenía
dos defectos, y el segundo es el grave.

**1. Ruido.** Cada tarjeta vacía decía tres veces lo mismo:

```
⚠ Solo el 0% de los datos necesarios está registrado. Para afinar este número, registra tu peso…
  Registra tu peso al menos dos días para ver la tendencia.
  ┌──────────────────────────┐
  │  Todavía no hay datos    │   ← 40 px de relleno, por once tarjetas
  └──────────────────────────┘
```

Por trece métricas: **once avisos ámbar idénticos**. Un aviso que sale siempre enseña a no leer los
avisos, y eso es precisamente lo que lo hace inútil el día que uno significa algo. Además «solo el
0 %» no es una cobertura parcial —es que no has empezado— y decirlo con un porcentaje suena a fallo
de la aplicación.

**2. Una mentira.** `stalled_exercises` devolvía `value=0` y la nota **«Sin estancamientos
detectados»** a quien no ha entrenado nunca. Con `coverage=0` ese cero no significa «ninguno»,
significa **«no lo sabemos»** — y pintarlo como un cero convierte la ignorancia en una
felicitación. Es exactamente la ambigüedad que `coverage` existe para deshacer (ADR-016), colada
por la puerta de atrás: la regla estaba en el dato y no en lo que se pinta.

**Decisión.**

- **`ComputedMetric.has_no_data`** = `is_empty` **o** `coverage == 0`. `is_empty` no bastaba:
  `value=0` no está vacío pero tampoco dice nada. Con esto no se pinta ni la insignia.
- **Una tarjeta sin datos enseña una sola frase**, `empty_hint`, elegida en Python y con test:
  gana la nota de la métrica cuando la hay (dice **cuánto** falta: «al menos dos días», «una rutina
  con días de entrenamiento»), si no se construye con los requisitos, y en último caso «Todavía no
  hay datos».
- **El aviso ámbar se reserva para cuando hay cifra y es poco fiable**, que es para lo que sirve.
  Un usuario nuevo pasa de once avisos a ninguno; con cobertura del 25 % sigue saliendo.
- `stalled_exercises` **no emite su nota sin cobertura**. Arreglado en el origen y no al pintar:
  esa nota también viaja al prompt del análisis, donde «sin estancamientos detectados» es peor
  todavía.

**Consecuencia.** El aviso de cobertura pasa de decorado permanente a señal. Y queda dicho que
**la regla de ADR-016 se aplica también al render**: cualquier sitio que enseñe un `value` tiene
que mirar antes el `coverage`.

---

## ADR-035 — Un solo control para volver
**Fecha:** 2026-09-15 · **Estado:** SUSTITUIDA por ADR-062

**Contexto.** Cada pantalla resolvía el «volver» por su cuenta: `← Plan` en texto pequeño en la
rutina, `← {{ programa }}` en la asignación, un botón normal en la ficha de ejercicio. Tres
tamaños, tres posiciones y ninguno llegaba a los 44 px táctiles.

**Decisión.** `templates/_back.html`: botón redondo de 44 px, con chevron y el destino como
etiqueta. En móvil se ve solo el icono y el destino va en `sr-only`, porque leerlo importa aunque
no quepa. Un test comprueba que **ninguna plantilla escriba la flecha a mano** — salvo la guía de
estilos, que cita el patrón retirado para explicar por qué existe este.

---

## ADR-034 — Dos modos de navegación: pestañas abajo o barra lateral
**Fecha:** 2026-09-15 · **Estado:** SUSTITUIDA por ADR-062 · **Sustituye el modo intermedio de ADR-019**

**Contexto.** Había tres modos: pestañas abajo en móvil, una barra superior fina entre 48 y 64 rem,
y esa misma barra en un monitor de 27 pulgadas. El resultado en escritorio era una columna estrecha
centrada bajo una tira de enlaces: **parecía un móvil estirado**.

**Decisión.** Dos modos, y el móvil no cambia:

- **`< lg` (64 rem):** barra de pestañas inferior, al alcance del pulgar.
- **`≥ lg`:** **barra lateral fija** de 15 rem, con los cinco destinos siempre visibles, la marca
  arriba y la cuenta abajo. Desaparece la barra superior.

Las pantallas que eran una lista larga se reparten en dos columnas desde `xl` (Plan, Rutina,
Ejercicios), y el contenido sube a `max-w-7xl`: con `6xl` menos la lateral quedaba estrecho.

**Los destinos se definen una sola vez**, en `apps/common/context_processors.py`, y los iconos en
`templates/_nav_icon.html`. Escribirlos en las dos barras garantizaba que un día dejaran de
coincidir; hay un test que lo vigila.

> El icono no se devuelve desde Python aunque fuera cómodo: obligaría a `mark_safe`, y la regla es
> que nada se marca como seguro. Aquí el SVG sería nuestro y no habría riesgo real, pero la regla
> vale justamente por no tener que juzgar caso por caso.

---

## ADR-033 — La fila de registrar serie se apila en móvil
**Fecha:** 2026-09-15 · **Estado:** aceptada · **Matizada por ADR-064**

**Contexto.** A 375 px quedan 319 px útiles. La fila metía número de serie (24 px) + dos steppers +
botón de confirmar (44 px), y **cada stepper necesita 88 px solo de botones**: sobraban ~25 px por
cifra. No se lee «92.5» en 25 px, y es la pantalla que se usa de pie y con prisa.

**Decisión.** Se apila por debajo de `sm`: los dos steppers con su etiqueta, y el botón de
confirmar **a ancho completo** debajo — es la acción que más se pulsa de toda la aplicación. Desde
`sm` vuelve a una línea.

**Consecuencia.** El barrido estructural no lo habría encontrado: no hay ancho fijo ni tabla sin
envolver, solo un `flex` que técnicamente cabe. Los defectos de responsive que quedan son de este
tipo —cabe pero no se lee— y solo se ven midiendo o mirando.

---

## ADR-032 — Ejercicios unilaterales: se anota un lado, el tonelaje cuenta dos
**Fecha:** 2026-09-15 · **Estado:** aceptada

**Contexto.** **224 de los 1324 ejercicios del catálogo (16 %) son unilaterales** y no había ningún
campo que lo recogiera. Con el modelo anterior cualquier convención falseaba una métrica:

| Cómo se registrara | Tonelaje | Series efectivas |
|---|---|---|
| Una fila para las dos manos | **la mitad** del peso movido | correcto |
| Una fila por brazo | correcto | **el doble** de series |

Y ese tonelaje viaja al prompt del análisis de progreso, así que el sesgo acababa en lo que la IA
dice.

**Decisión.** `Exercise.is_unilateral`. Se anota **un lado** y la interfaz lo dice («kg · por
lado»). El ×2 vive en una función nueva:

```python
effective_load(set_log, bw)   # lo que se levanta EN ESA SERIE  → fuerza, récords
total_work(set_log, bw)       # el trabajo total, ×2 si unilateral → tonelaje, densidad
```

**La parte delicada es dónde NO va.** `effective_load` alimentaba a la vez el tonelaje y el 1RM
estimado; meter ahí el ×2 habría doblado los récords personales. Un remo a una mano con 30 kg es un
1RM de **30**, no de 60 — y eso no se detecta leyendo el código, se descubre meses después al ver
un récord imposible. Hay un test que lo fija explícitamente.

**Las series efectivas no cambian:** los volúmenes de referencia de la literatura son por lado, así
que tres series de remo a una mano son tres series para la espalda, no seis.

**El marcado automático se queda corto a propósito.** La migración activa la bandera en los
**patrones inequívocos** (`one arm`, `single leg`, `split squat`…): 164 ejercicios. Los ambiguos
—`alternate`, donde los dos lados suelen ir dentro de la misma serie, y `lunge`— **se dejan sin
marcar**: un falso positivo infla el tonelaje un 100 %, y es peor pasarse que quedarse corto.
Cualquiera se corrige a mano, y los propios traen la casilla en el alta.

---

## ADR-031 — El ejercicio se configura al añadirlo, no en otra pantalla
**Fecha:** 2026-09-15 · **Estado:** aceptada

**Contexto.** Añadir un ejercicio a una rutina lo creaba con valores por defecto y obligaba a
abrir `routine_exercise_form.html` para poner series, repeticiones y descanso. El usuario lo
señaló con una captura: seis campos idénticos apilados, etiqueta encima de cada uno, sin imagen
del ejercicio y sin jerarquía. **Dos viajes para algo que se decide al elegir el ejercicio**: si
sabes que quieres press de banca, sabes que lo quieres a 4×6-8.

**Decisión.** La pantalla desaparece.

- En el **buscador**, «Añadir» despliega la configuración en la misma fila, con la miniatura
  delante, y se guarda todo en **una petición**.
- En la **rutina**, cada fila muestra `4×6-8 · 180s` y al tocarla se abre **el mismo control** con
  un botón de guardar. Editar deja de cambiar de página.
- Un solo parcial, `templates/workouts/_set_config.html`, en los dos sitios: en dos copias
  acabarían separándose.
- **El rango de repeticiones es un control, no dos campos**: dos cifras unidas por un guion dentro
  del mismo borde. Ocupaba la mitad de la pantalla de la captura.

**Se despliega con `<details>` y se guarda con un `<form>` normal**, así que funciona sin
JavaScript; los `[−][+]` son un añadido. Y respetan los topes del modelo (`data-max`): sin eso,
pulsar «+» sin parar enseñaba 25 series y el servidor guardaba 20 — el usuario veía un número y se
guardaba otro.

**Consecuencias.** Fuera `routine_exercise_edit`, su plantilla y `RoutineExerciseForm`. Los
valores llegan por `POST` y se **acotan** en vez de rechazarse: vienen de un formulario con
`min`/`max`, así que un disparate significa que alguien lo forzó a mano, y devolverle una pantalla
de error por un campo que no ha tecleado es peor que guardar el extremo más cercano. Un mínimo
mayor que el máximo arrastra el máximo, porque casi siempre es que se subió el mínimo sin tocar el
otro.

---

## ADR-030 — Se quitan los campos que no lee nadie
**Fecha:** 2026-09-15 · **Estado:** aceptada

**Contexto.** El usuario dijo que se estaban guardando datos sin relevancia. Se auditó campo por
campo con `grep` sobre todo el código, excluyendo tests y migraciones:

| Campo | Quién lo leía | |
|---|---|---|
| `RoutineExercise.notes` | **Nadie**: no aparecía en ninguna plantilla | Fuera |
| `RoutineExercise.target_rpe` | Solo la exportación. Salía siempre vacío | Fuera |
| `SetLog.duration_seconds` | **Nadie**. Ni una métrica | Fuera |
| `WorkoutSession.perceived_fatigue` | **Ninguna métrica**; solo el admin | Fuera |
| `ScheduleEntry.notes` | **Nadie**. Añadido en ADR-028 y nunca usado | Fuera |
| `SetLogForm` | **Ninguna vista**. Código muerto | Fuera |

**Decisión.** Se eliminan, y con ellos `rpe` y `notes` del esquema de la IA: pedirle al modelo
campos que después se descartan gasta tokens y arriesga una validación por nada.

**Lo que NO se toca**, y conviene dejarlo claro porque se parece:

- **`SetLog.rpe`** — el RPE que se anota en cada serie al entrenar. Lo usan `average_rpe` e
  `is_effective_set`. Lo que desapareció es el *objetivo* de la plantilla, no el dato real.
- **`SetLog.is_warmup` y `completed`** — los usa `is_working_set` para excluir calentamientos del
  volumen (ADR-014). Hoy no hay interfaz para marcarlos, pero eso es una **función que falta**, no
  una razón para borrar el campo: quitarlos rompería la metodología que el proyecto declara.
- **`WorkoutSession.notes` y `BodyWeightEntry.notes`** — son observaciones de verdad («me molestó
  el hombro») y se muestran.

**Consecuencias.** Los 500 tests pasaron sin tocar ni uno, lo que confirma la auditoría: nada
dependía de esos campos. Eso mismo destapó algo: los tests construían `PlannedExercise(rpe=…,
notes=…)` y **Pydantic ignora los campos de más en silencio**, así que pasaban sin probar el
esquema nuevo. Se limpiaron, y se añadió un test de que una generación **guardada con el esquema
viejo sigue abriéndose** — si algún día alguien pusiera `extra="forbid"`, las propuestas anteriores
reventarían con un 500 y nadie relacionaría la causa.

---

## ADR-029 — Animaciones con Anime.js, con una sola puerta
**Fecha:** 2026-09-15 · **Estado:** aceptada

**Contexto.** El usuario pidió efectos con una librería de JavaScript. El riesgo de eso es
conocido: animación decorativa que estorba, y peso extra en una aplicación que se usa desde el
móvil en un gimnasio.

**Decisión.** **Anime.js 4.5.0**, bundle UMD (118 KB, MIT) servido **local** en `static/vendor/`
como htmx y Chart.js — la CSP estricta (ADR-011) no permite terceros, y así no hace falta
empaquetador. Se carga **solo en las pantallas que animan**, nunca en `base.html`.

Tres reglas, y las tres tienen test (`apps/common/tests/test_motion.py`):

1. **Una sola puerta.** `prefers-reduced-motion` se comprueba **una vez**, al principio de
   `motion.js`, con un `return` que corta de raíz. Quien pide menos movimiento recibe **cero**, no
   menos: a algunas personas el movimiento les provoca mareo o migraña. Repartida por el archivo,
   es cuestión de tiempo que una animación nueva se olvide de mirarla — por eso el test cuenta que
   aparezca exactamente una vez.
2. **Solo `transform` y `opacity`.** Animar `width`, `top` o `height` recalcula la maquetación en
   cada fotograma y en un móvil de gama media se ve a trompicones.
3. **Nada depende de la animación.** El valor final de las cifras está en el HTML (`data-count-to`
   solo lo recorre), el temporizador funciona sin el anillo, y la semana se asigna con un
   formulario normal. Si el archivo no carga, no se pierde ninguna función.

**Dónde se usa y por qué ahí:** anillo del temporizador de descanso (se lee desde lejos sin
enfocar el número), golpe del ✓ al registrar una serie (confirma con las manos ocupadas), cifras
que cuentan en Progreso (dirige la mirada a lo que cambió) y entrada escalonada de listas (da orden
de lectura). Nada de animación de adorno.

---

## ADR-028 — La rutina es una plantilla que se asigna a días
**Fecha:** 2026-09-15 · **Estado:** aceptada · **Sustituye el modelo de ADR-001**

**Contexto.** El modelo original hacía de `Routine` un **programa semanal** con siete `RoutineDay`
dentro, y los ejercicios colgaban de *(programa, día)*. La consecuencia, que el usuario señaló:
«Empuje» el lunes y el jueves eran **dos listas de ejercicios distintas**. Cambiar una serie el
lunes dejaba el jueves como estaba, y las dos copias se separaban sin que nadie se enterase.

En openGym —la referencia del proyecto— se crea una rutina y **se asigna a un día**.

**Decisión.** Tres modelos en vez de dos:

```
Routine        «Empuje»            plantilla reutilizable, con sus ejercicios
Program        «Volumen invierno»  la semana; uno activo por usuario
ScheduleEntry  lunes → «Empuje»    la asignación; `routine=None` ES el descanso
```

- **Las rutinas cuelgan del usuario, no del programa**, así se reutilizan entre programas: cambiar
  de etapa es reasignar días, no rehacer listas de ejercicios.
- **No hay `is_rest_day`.** Un día sin rutina **es** descanso. Un booleano aparte permitiría el
  estado incoherente «descanso con rutina asignada», y alguien tendría que decidir cuál gana.
- `WorkoutSession.routine_day` → `WorkoutSession.routine`.
- Se mantiene el contenedor de programas (decisión del usuario) para poder alternar entre etapas.

**Migración: clean slate** (decisión del usuario). `0003_rutinas_asignables_a_dias` borra rutinas,
días y ejercicios planificados. **Se conservan usuarios, entrenamientos, series, pesos y el
catálogo**, o sea todo lo que alimenta las métricas de fuerza, volumen y composición. Las sesiones
anteriores quedan con `routine=NULL`, lo que solo afecta a la adherencia.

**Consecuencias.** 31 archivos tocados. La propiedad que justifica el cambio está fijada por tests
(`apps/workouts/tests/test_schedule.py::TestLaMismaRutinaEnVariosDias`): asignar «Empuje» a dos
días y editarla en un sitio cambia los dos, y **no se duplica ninguna fila de ejercicio**. Si eso
dejara de cumplirse, el cambio no habría servido para nada.

---

## ADR-027 — Los datos de salud no salen en el texto que se loguea
**Fecha:** 2026-09-15 · **Estado:** aceptada · **Origen:** revisión de seguridad (paso 15)

**Contexto.** `should_analyze()` devolvía un motivo legible que incluía la cifra:
`"el ritmo (-0.35 kg/sem) se aparta 0.60 kg/sem del objetivo"`. Ese texto se escribe en los logs
junto al nombre de usuario (`apps/aiassist/tasks.py`). El ritmo de cambio de peso de una persona
identificada **es un dato de salud**, y `.docs/06-security.md` §8 dice que no aparecen en logs.
`SensitiveDataFilter` solo redacta patrones de clave de API, así que el número pasaba tal cual.

Los logs suelen tener más lectores, más retención y menos cifrado que la base de datos. Ahí es
donde el dato se sale del perímetro que se diseñó para protegerlo.

**Decisión.** `motivo` deja de llevar cifras: `"el ritmo se aparta del objetivo"`. Los números
siguen donde hacen falta —el prompt y la notificación al propio usuario—, que es su sitio.
Comprobado por `TestElMotivoNoFiltraDatosDeSalud`, que además rechaza cualquier decimal.

**Consecuencias.** Se pierde algo de detalle al depurar. A cambio, la regla es simple de sostener:
**lo que se loguea no lleva números de salud**, y un test lo vigila.

---

## ADR-026 — `Exercise` se consulta siempre con `visible_to(user)`
**Fecha:** 2026-09-15 · **Estado:** aceptada · **Origen:** revisión de seguridad (paso 15)

**Contexto.** `Exercise` es el único modelo del proyecto que **mezcla filas públicas con filas de
alguien**: `is_global=True` para los 1324 importados, y `created_by` para los que cree cada
persona. `routine_generator.py` ya filtraba `is_global=True`, y `privacy.py` ya cuenta y borra los
«ejercicios propios» — la distinción estaba viva en el código.

Las vistas del catálogo, en cambio, usaban `Exercise.objects.all()`. Comprobado en la revisión:
un ejercicio con `is_global=False` de otra persona **salía en el listado y su ficha era accesible
por slug, incluso sin haber iniciado sesión**.

Hoy no hay ninguna pantalla para crear ejercicios propios, así que no había nada expuesto todavía.
Pero la referencia que estamos siguiendo tiene «Create your own exercise», así que el agujero
habría llegado con esa pantalla y nadie lo habría relacionado.

**Decisión.** La regla vive en el manager, no en cada vista:

```python
Exercise.objects.visible_to(request.user)   # global + los propios, nunca los de otro
```

Aplicado en el listado, la ficha, el selector HTMX, el alta en rutina, el registro de series y el
`ExerciseViewSet` de la API.

**Consecuencias.** Escribirlo bien cuesta lo mismo que escribirlo mal (`visible_to(user)` frente a
`all()`), que es la única forma de que una regla así sobreviva. Un anónimo sigue pudiendo navegar
el catálogo global: eso es producto, no seguridad, y se deja como estaba.

---

## ADR-025 — Lo que cambia el estado exige POST
**Fecha:** 2026-09-15 · **Estado:** aceptada · **Origen:** revisión de seguridad (paso 15)

**Contexto.** Siete vistas cambiaban el estado y respondían a **GET**: empezar y finalizar un
entrenamiento, borrar una serie, añadir y quitar un ejercicio de un día, y marcar avisos. Se
comprobó ejecutándolas: las siete mutaban con una petición GET.

**La protección CSRF de Django exime a GET por diseño**, así que esas vistas no tenían ninguna
defensa. `SameSite=Lax` evita el caso sin clic —la cookie no viaja en un `<img>`—, pero **sí viaja
en una navegación de primer nivel**, que es exactamente un enlace pulsado desde un correo o un
foro. Y ni siquiera hace falta mala intención: los prefetchers de enlaces de los clientes de
correo y de chat disparan GET solos.

**Decisión.** `@require_POST` en las siete, y los enlaces de las plantillas pasan a formularios con
`{% csrf_token %}`. De paso, `mark_read` y `mark_all_read` recibieron el `@login_required` que les
faltaba: sin él, una petición anónima acababa en un 500 al usar `AnonymousUser` como clave ajena.

**Consecuencias.** Un botón dentro de un `<form>` es más verboso que un `<a>`, y esa es toda la
contrapartida. La regla general queda: **si una vista escribe en la base de datos, exige POST**;
si no, es un enlace. Cubierto por `apps/workouts/tests/test_security_methods.py`.

Nota para revisiones futuras: los tests de autorización que usaban GET ahora reciben 405 antes de
llegar a comprobar el permiso. Se pasaron a POST para que sigan comprobando lo que decían
comprobar — un 405 verde habría dado una falsa sensación de cobertura.

---

## ADR-024 — Las clases construidas en tiempo de ejecución se declaran con `@source inline`
**Fecha:** 2026-09-14 · **Estado:** aceptada

**Contexto.** El calendario de actividad pinta `class="heat-cell heat-{{ dia.level }}"`. Tailwind
solo encuentra **cadenas literales**, así que `heat-1` … `heat-4` no aparecían por ninguna parte
para el escáner. Funcionaban igualmente, pero **por accidente**: la guía de estilos las nombraba
una a una en su leyenda. El día que alguien recortara esa guía, el calendario se habría quedado
en blanco sin que fallara ningún test.

**Decisión.** Declararlas explícitamente:

```css
@source inline("heat-{0,1,2,3,4}");
```

Comprobado que funciona de verdad: se renombraron las menciones de la guía de estilos, se
recompiló y las cinco clases seguían emitiéndose.

**Consecuencias.** Es la tercera vez que aparece la misma trampa —clases que existen fuera de las
plantillas—, después de `Notification.badge_class` en Python (ADR-019). **Regla general: toda
clase que no se escriba entera y literal en una plantilla necesita `@source` o `@source inline`.**

---

## ADR-023 — La regla de progresión: cuándo sugerir subir peso, y cuándo callarse
**Fecha:** 2026-09-14 · **Estado:** aceptada

**Contexto.** La pantalla de entrenar muestra una sugerencia del tipo «prueba 87,5 kg». Es lo
único de la aplicación que **le dice a alguien qué peso poner**, así que puede hacer daño: si
sugiere de más, empuja a fallar repeticiones; si sugiere siempre, enseña a ignorar el aviso.

**Decisión** (`apps/workouts/history.py`):

- **Solo sugiere si la última vez se completó el rango entero.** Una sola serie corta y no dice
  nada. Subir carga a quien no completó lo anterior es la receta del estancamiento, que es
  justamente lo que esta aplicación existe para detectar.
- **El salto depende del equipamiento**, porque es el disco que físicamente existe: 2,5 kg en
  barra, 2 kg en mancuerna, 5 kg en torre de poleas o máquina. Sugerir «+1 kg» en una barra es
  inútil si el disco más pequeño es de 1,25 y van de dos en dos.
- **En peso corporal sugiere repeticiones, no kilos.** Proponer carga a quien hace dominadas sin
  lastre no tiene dónde aplicarse.
- **Devolver «nada» es una respuesta válida y frecuente**, no un caso degenerado.

**Consecuencias.** La mayoría de los tests de esta regla comprueban cuándo **no** debe decir nada,
que es donde está el riesgo. Si algún día se quiere afinar —doble progresión, por ejemplo—, el
sitio es esa función y sus tests, no la plantilla.

---

## ADR-022 — La disposición de las pantallas se toma de openGym; su código, no
**Fecha:** 2026-09-14 · **Estado:** aceptada

**Contexto.** El rediseño responsive dejó las cinco secciones con **la misma forma**: encabezado
más rejilla de tarjetas. Ordenado, pero ninguna pantalla comunicaba para qué servía. El usuario lo
señaló y pidió seguir las pantallas de openGym, que es la referencia del proyecto desde el primer
día.

**openGym es AGPL v3**, un copyleft fuerte: usar su código obligaría a publicar todo esto bajo
AGPL.

**Decisión.** Se toma **la disposición** y se reimplementa desde cero:

- Las disposiciones —tira de semana, filas de día, tiles de cifra, calendario de actividad, modo
  foco— son **patrones funcionales de interfaz**, comunes en aplicaciones de fitness, y el
  copyright no los protege.
- **No se ha leído ni copiado nada de `gym/frontend/src/`**, ni sus SVG, ni sus textos. La única
  fuente usada han sido las cinco capturas de `gym/assets/screenshots/`.
- Los iconos son SVG propios; los textos, propios y en español.
- **El color NO se copia**: openGym es verde sobre negro y aquí se mantiene el azul con sus dos
  temas. Además tiene una ventaja concreta — en openGym el verde es a la vez acento y «correcto»;
  al conservar el azul, **el verde queda libre para significar solo «correcto»**, que en una
  aplicación de progreso es su uso más útil.

**Consecuencias.** Cada pantalla tiene ahora su propia forma, dictada por lo que se hace en ella.
Si algún día se quisiera ir más allá —reutilizar su código—, habría que relicenciar el proyecto
como AGPL, y esa sería una decisión distinta y consciente.

Nota aparte: las imágenes del catálogo siguen siendo © Gym Visual y su atribución se renderiza
(ADR-007, `NOTICE.md`). Eso no cambia.

---

## ADR-021 — `{% comment %}` para cualquier comentario de más de una línea
**Fecha:** 2026-09-14 · **Estado:** ~~aceptada~~ **SUSTITUIDA por ADR-073** (el código ya no lleva comentarios)

**Contexto.** Durante el rediseño se escribieron 19 comentarios `{# … #}` repartidos en varias
líneas. **El `{# #}` de Django no admite saltos de línea**: su lexer solo lo reconoce dentro de una
misma línea, así que los 19 se renderizaban *literalmente* y aparecían impresos en la página. No
lanzaban ninguna excepción y ningún test de vista los detectó.

**Decisión.** Una línea → `{# … #}`. Más de una → `{% comment %}…{% endcomment %}`. Y un test que
lo vigila: `apps/common/tests/test_templates.py`, que recorre las 25 plantillas y además comprueba
que ninguna página servida contiene `{#`, `{%` ni `}}` sin procesar.

**Consecuencias.** El test incluye una comprobación del propio motor de plantillas
(`test_un_comentario_multilinea_se_imprimiria`) para que quede demostrado que vigila un defecto
real y no una preferencia de estilo — si algún día Django cambiara ese comportamiento, ese test
avisaría de que la regla ya no hace falta.

**Cómo se encontró:** revisando las plantillas, no por un test en rojo. Es el tipo de defecto que
solo se ve mirando la página.

---

## ADR-020 — La cadena claro/oscuro se elige por paso, y el contraste se calcula
**Fecha:** 2026-09-14 · **Estado:** aceptada

**Contexto.** Al añadir tema claro, lo barato era invertir la escala del oscuro. Un acento que luce
sobre `#0f1115` se lava sobre blanco, y al revés, así que invertir produce texto ilegible en un tema
u otro sin que nadie lo note hasta verlo.

**Decisión.** Dos pasos por color, elegidos contra la superficie de *su* tema, y **comprobados con
un validador**, no a ojo. Los valores y sus ratios están anotados en `assets/app.css`: todos superan
4,5:1 como texto (acento 5,17:1 en claro y 6,85:1 en oscuro; el peor caso es 4,76:1).

**Consecuencias.** Hay un fallo que **no se arregla**: el validador marca verde-«correcto» ↔
rojo-«peligro» como indistinguibles en deuteranopia. Eso es inherente a la semántica —un verde de
«correcto» es una convención demasiado fuerte para cambiarla— así que se compensa donde toca:
**todo estado lleva texto, y los mensajes además icono**. El color nunca es el único portador. Esto
es una regla del sistema, no una recomendación: `/estilos/` existe para poder comprobarla de un
vistazo.

---

## ADR-019 — Tailwind v4 con binario standalone (sustituye a ADR-013)
**Fecha:** 2026-09-14 · **Estado:** ~~aceptada~~ **SUSTITUIDA por ADR-047**

> Lo de adoptar Tailwind v4 sigue en pie. Lo del **binario standalone y el CSS comiteado** ya no:
> con el frontend en React lo compila Vite dentro del bundle (ADR-047). En la Fase 10 se borraron
> `bin/tailwindcss.exe`, `static/css/app.css` y el job `estilos` de CI que vigilaba que el
> artefacto no se quedara viejo. `assets/app.css` —la fuente— no cambió.

**Contexto.** ADR-013 descartó Tailwind por tres razones. Al revisarlas para el rediseño responsive,
**dos ya no se sostenían**:

| Razón de ADR-013 | Estado comprobado hoy |
|---|---|
| v3 no publica CSS precompilado | Sigue siendo cierto: `tailwindcss@4/dist/tailwind.min.css` → 404. El `index.css` de v4 existe pero es **código fuente** (`@theme`, `@layer`), no CSS compilado |
| El Play CDN compila en el navegador | Sigue siendo cierto y sigue desaconsejado para producción |
| El CLI standalone mete un binario y un paso de build | **v4 publica binario standalone**, incluido `tailwindcss-windows-x64.exe`. Sin Node, sin npm, sin `package.json` |

Se sumaba que el trabajo pendiente —reescribir el CSS y las clases de las 25 plantillas— iba a
hacerse igualmente, así que el coste de cambiar nunca iba a ser más bajo.

**Decisión.** Tailwind v4.3.3 con el binario standalone. Fuente en `assets/app.css`
(`@theme` + `@layer base` + un puñado corto de `@utility`), salida en `static/css/app.css`.

**El artefacto generado se comitea**, y esa es la decisión que más consecuencias tiene: como
`STORAGES["staticfiles"]` usa `CompressedManifestStaticFilesStorage`, `collectstatic` hashea el CSS.
Al comitearlo, **producción no necesita el binario** y el despliegue sigue siendo exactamente lo que
era. El precio —que el artefacto se quede viejo— lo cubre el job `estilos` de CI, que recompila y
falla si el resultado difiere. La versión del binario va **clavada**: con `latest`, una publicación
de Tailwind rompería CI un martes cualquiera sin que nadie tocara el código.

**Consecuencias.** La CSP estricta (ADR-011) no se toca: Tailwind produce un `.css` servido desde el
propio dominio. `@source` apunta a `templates/` **y a `apps/`** — esto último no es opcional, porque
`Notification.badge_class` devuelve el nombre de la clase desde Python y sin escanear ahí esas
insignias se quedarían sin estilo el día que el nombre deje de aparecer en una plantilla.

**Lo que se pierde.** La regla «nada de estilos inline» de ADR-013 se mantiene, pero las plantillas
pasan a llevar clases utilitarias. Para evitar que eso las haga ilegibles se definieron ~20
`@utility` propias (`card`, `btn`, `table-stack`, `empty-state`…), elegidas **contando** usos, no
por intuición: `field` salía 16 veces, `empty` 16, `form-grid` 6.

**Sin plugins.** Ni `@tailwindcss/forms` ni `typography`. Los controles se estilan por elemento en
`@layer base`, que hacía falta de todos modos porque las plantillas renderizan `{{ form.campo }}` y
Django no pone clases. `prose` no aplica: el texto de la IA se escapa y nunca se renderiza como HTML.

---

## ADR-001 — Django + DRF en lugar de FastAPI o Flask
**Fecha:** 2026-09-14 · **Estado:** aceptada

**Contexto.** Se necesitaba backend, panel de administración configurable por un admin no técnico,
autenticación, ORM con migraciones y una UI web, todo en Python.

**Decisión.** Django 5 con DRF para la API y templates + HTMX para la UI.

**Consecuencias.** El panel de admin de la IA (proveedor, modelo, API key, prompts) sale casi gratis
del admin de Django, que es el requisito que más trabajo habría dado en FastAPI. A cambio, la UI es
menos reactiva que una SPA; HTMX cubre la diferencia en las pantallas que lo necesitan (registro de
series, búsqueda de ejercicios). Si en el futuro se quiere una app móvil, la API DRF ya está.

---

## ADR-002 — PostgreSQL sin pgvector
**Fecha:** 2026-09-14 · **Estado:** aceptada

**Contexto.** La idea inicial era PostgreSQL + pgvector para el RAG. Al decidir que el RAG se delega
a OpenAI Vector Stores (ADR-004), pgvector se quedaba sin nada que almacenar.

**Decisión.** PostgreSQL a secas para datos relacionales. Los embeddings los gestiona OpenAI.

**Consecuencias.** Menos infraestructura y ninguna pipeline de ingesta duplicada. Si algún día se
quisiera indexado local, habría que añadir la extensión y construir esa pipeline desde cero.

---

## ADR-003 — Tres proveedores de IA tras una interfaz común
**Fecha:** 2026-09-14 · **Estado:** aceptada

**Contexto.** El admin debe poder cambiar de proveedor, modelo y API key sin tocar código.

**Decisión.** Una clase abstracta `LLMProvider` en `apps/aiassist/providers/base.py` con un adaptador
por proveedor (Anthropic, OpenAI, Google). `factory.get_provider()` lee la configuración activa y
devuelve el adaptador correspondiente. **Ningún servicio instancia un SDK directamente.**

**Consecuencias.** Añadir un proveedor es un archivo nuevo, no una búsqueda global. El precio es que
las capacidades específicas de cada SDK hay que exponerlas en la interfaz o renunciar a ellas —
que es justo lo que pasa con el RAG (ADR-005).

---

## ADR-004 — El RAG se delega a OpenAI Vector Stores
**Fecha:** 2026-09-14 · **Estado:** aceptada

**Contexto.** La IA debe fundamentar sus rutinas en literatura de hipertrofia. Había que elegir entre
construir la pipeline de RAG (trocear, embeber, indexar, recuperar) o delegarla.

**Decisión.** El admin crea *vector stores* de OpenAI desde el panel y sube ahí los documentos.
OpenAI se encarga del troceado, los embeddings y el índice.

**Consecuencias.** Nos ahorramos toda la pipeline y su mantenimiento. A cambio, el RAG depende de
tener una cuenta de OpenAI activa, y el material queda alojado fuera. Límites heredados: 512 MB y
5M tokens por archivo; formatos `.pdf`, `.docx`, `.txt`, `.md`; troceado por defecto de 800 tokens
con solape de 400.

---

## ADR-005 — `file_search` nativo: el RAG solo funciona con OpenAI
**Fecha:** 2026-09-14 · **Estado:** aceptada, con reserva

**Contexto.** Habiendo puesto el RAG en OpenAI (ADR-004) pero soportando tres proveedores (ADR-003),
había dos formas de conectarlos:

- **a)** Recuperar siempre con `POST /v1/vector_stores/{id}/search` (endpoint independiente, verificado:
  devuelve chunks, score y atributos, hasta 50 resultados, con filtrado por metadatos) e inyectar los
  fragmentos en el prompt de cualquier proveedor.
- **b)** Usar la herramienta `file_search` nativa de la Responses API de OpenAI, que solo existe ahí.

**Decisión.** Opción (b), elegida explícitamente por el usuario.

**Consecuencias.** **Elegir Anthropic o Google como proveedor significa generar rutinas sin el
contexto de los libros.** Es una limitación conocida y aceptada, no un descuido.

Para no cerrar la puerta, `LLMProvider` declara `supports_rag` y los servicios comprueban esa bandera
antes de pasar los IDs de vector store. Migrar a la opción (a) más adelante es añadir la llamada al
endpoint de búsqueda e inyectar los fragmentos — sin tocar la estructura.

---

## ADR-006 — La aritmética en Python, no en el LLM
**Fecha:** 2026-09-14 · **Estado:** aceptada

**Contexto.** El análisis de progreso necesita 1RM estimado, volumen semanal por grupo muscular,
pendientes de progresión, adherencia y medias móviles de peso. Se podía pasar el historial crudo al
modelo y pedirle que calculara.

**Decisión.** Todo eso se calcula en `apps/workouts/metrics.py`. El LLM recibe los números ya hechos
y solo interpreta.

**Consecuencias.** Los cálculos son deterministas, testeables sin red y reproducibles. El prompt es
más corto y más barato. Un error de cálculo lo caza un test en vez de pasar inadvertido dentro de un
párrafo bien redactado. El coste es escribir y mantener ese módulo.

---

## ADR-007 — Catálogo de ejercicios desde `hasaneyldrm/exercises-dataset`
**Fecha:** 2026-09-14 · **Estado:** aceptada

**Contexto.** Hacía falta un catálogo de ejercicios con nombres, músculos, equipamiento e
instrucciones. Existía una copia local dentro de openGym (`C:\Users\USEROPC\gym`, AGPL v3) y estaba
también el repositorio original del que openGym la toma.

**Decisión.** Usar el repositorio original, clonado en `vendor/exercises-dataset` (ignorado por git).

**Consecuencias.** Se obtiene `data/exercises.json` limpio en vez de desenvolver archivos `.js`, un
JSON Schema oficial contra el que validar en el importador, y los **10 idiomas** de instrucciones en
lugar de solo español. Al no copiar nada de openGym, su licencia AGPL no afecta a este proyecto en
ningún punto.

Licencia en dos capas, con consecuencias reales:

| Capa | Licencia |
|---|---|
| Datos (JSON, nombres, instrucciones) | MIT |
| Imágenes y GIFs | © Gym Visual, redistribuidos con permiso **solo a 180×180** |

Por eso el campo `attribution` se persiste por ejercicio y **se renderiza en la UI** (es requisito de
licencia, no adorno) y las imágenes se sirven a 180×180 sin reescalar. Para uso personal o académico
no hay fricción; **para publicar como producto hay que sacar licencia propia en gymvisual.com**.
El material está desacoplado en dos campos del modelo, así que sustituirlo sería un reimport.

---

## ADR-008 — La IA elige de un catálogo cerrado, no inventa ejercicios
**Fecha:** 2026-09-14 · **Estado:** aceptada

**Contexto.** Un generador de rutinas que devuelve nombres libres obliga a adivinar a qué ejercicio
se refería ("press banca inclinado con mancuernas" vs. "incline dumbbell press"), y acaba creando
duplicados en la base de datos.

**Decisión.** Al prompt se le pasa una lista de candidatos reales filtrada por el equipamiento del
usuario y los grupos musculares del día (~200 como máximo). El esquema `RoutinePlan` obliga a
devolver `external_id` pertenecientes a esa lista; uno fuera de lista se rechaza y se reintenta una
vez con el error como feedback.

**Consecuencias.** El mapeo pasa de aproximado a exacto y no se crean ejercicios basura. Además
resulta ser una defensa contra prompt injection (ADR-010): aunque una inyección funcione, no hay
forma de que la salida se salga del esquema. El coste son los tokens de la lista de candidatos, que
se acota filtrando.

---

## ADR-009 — MultiFernet para las API keys, con clave independiente de `SECRET_KEY`
**Fecha:** 2026-09-14 · **Estado:** aceptada

**Contexto.** Las API keys de los proveedores se guardan en base de datos porque el admin las
configura desde el panel. Filtrarlas cuesta dinero real.

**Decisión.** Un `EncryptedTextField` sobre **MultiFernet** (no Fernet simple), con las claves en
`FIELD_ENCRYPTION_KEYS` como lista separada por comas, **independiente de `SECRET_KEY`**.

**Consecuencias.** MultiFernet cifra con la primera clave y descifra con cualquiera de la lista, lo
que permite rotar sin downtime: se añade la nueva al principio, se re-cifra con el comando
`rotate_encryption_key` y se retira la vieja.

La independencia respecto a `SECRET_KEY` es deliberada: rotar sesiones y rotar secretos son ciclos de
vida distintos, y derivar una de otra obliga a hacer ambas cosas a la vez.

---

## ADR-010 — Contra prompt injection, defensa estructural antes que textual
**Fecha:** 2026-09-14 · **Estado:** aceptada

**Contexto.** `injuries_notes`, las notas de rutinas y sesiones y los nombres de ejercicios
personalizados entran en el prompt. Un usuario puede escribir "ignora las instrucciones anteriores".

**Decisión.** La defensa principal no son instrucciones en el prompt, sino tres propiedades del
diseño:

1. **La salida está restringida por esquema** (ADR-008). Aunque la inyección funcione, no se puede
   devolver nada fuera de `RoutinePlan` con `external_id` de la lista de candidatos.
2. **El LLM no tiene herramientas con efectos secundarios.** No ejecuta SQL, no escribe archivos, no
   hace HTTP. Devuelve JSON que el servicio valida y persiste. Eso elimina la categoría entera de
   *inyección → acción*.
3. **El LLM nunca ve credenciales.** La API key vive en el cliente HTTP, jamás en el texto del
   prompt. No hay nada que extraer.

Encima van las capas textuales: delimitadores `<user_notes>` y `<retrieved_context>` declarados como
datos, límites de longitud y limpieza de caracteres de control.

**Consecuencias.** El peor caso de una inyección exitosa es una rutina mal planteada, no una fuga de
datos ni una escritura arbitraria. Las instrucciones textuales se pueden sortear; estas tres
propiedades no. Si algún día se le da tool calling con efectos secundarios al modelo, **esta decisión
deja de sostenerse** y hay que revisarla.

---

## ADR-011 — Tailwind y Chart.js servidos localmente, no por CDN
**Fecha:** 2026-09-14 · **Estado:** aceptada

**Contexto.** Lo cómodo en desarrollo es cargar ambos desde un CDN. Pero el plan incluye una CSP
estricta vía `django-csp`.

**Decisión.** Servirlos como estáticos del proyecto.

**Consecuencias.** La CSP puede ser restrictiva de verdad en lugar de tener que permitir dominios
externos. Se decide ahora y no al final, porque hacerlo después significa reescribir plantillas. El
coste es un paso de build para los estáticos.

---

## ADR-018 — Borrar una cuenta limpia también el rastro de la auditoría
**Fecha:** 2026-09-14 · **Estado:** aceptada

**Contexto.** `AIGeneration.user` es `SET_NULL` para conservar el gasto agregado cuando alguien se
da de baja. Pero esas filas guardan `prompt_rendered`, que incluye las lesiones, el peso y el
historial de la persona.

Borrar la cuenta y dejar eso ahí sería un borrado de mentira: los datos de salud seguirían en la
base de datos, solo que sin nombre encima.

**Decisión.** `delete_account()` sobrescribe `prompt_rendered`, `raw_response`, `parsed_output` y
`error` antes de borrar al usuario. Se conservan proveedor, modelo, tokens, latencia y fecha.

**Consecuencias.** La contabilidad de coste sigue cuadrando y no queda ningún dato personal.

**Fallo encontrado al implementarlo.** `Exercise.created_by` es CASCADE, pero
`RoutineExercise.exercise` y `SetLog.exercise` son PROTECT. Quien había creado un ejercicio propio
**y lo había usado** recibía `ProtectedError` al intentar darse de baja: precisamente el usuario más
implicado era el que no podía irse.

Se resuelve borrando en orden de dependencias (historial → ejercicio → usuario) en
`_release_custom_exercises()`. Los PROTECT siguen haciendo su trabajo —impedir que se borre un
ejercicio y queden series huérfanas—; lo único que hacía falta era respetar el orden.

---

## ADR-017 — Descifrar mal no es fatal al leer, es fatal al usar
**Fecha:** 2026-09-14 · **Estado:** aceptada · **Matiza ADR-009**

**Contexto.** El `EncryptedTextField` lanzaba una excepción cuando ninguna clave de
`FIELD_ENCRYPTION_KEYS` servía para descifrar un valor. Parecía lo correcto: fallo ruidoso, nada de
errores silenciosos.

Al probarlo salió el problema: la excepción se lanza en `from_db_value`, es decir **durante la
consulta**. Cargar la fila revienta, así que el listado del admin da error 500 y **te quedas
bloqueado sin poder entrar a pegar la clave otra vez**. El fallo ruidoso te deja sin la herramienta
para arreglarlo.

**Decisión.** `from_db_value` devuelve `UndecryptableSecret`, una subclase de `str` vacía —y por
tanto falsa— en lugar de lanzar. Quien intenta **usar** la clave sí falla: `get_provider()` la
comprueba y lanza `ProviderError` con instrucciones.

**Consecuencias.** El admin sigue funcionando y muestra `(no se pudo descifrar: vuelve a pegar la
clave)` en el listado, que es justo donde hace falta verlo. No hay errores 401 misteriosos del
proveedor, porque la factoría se niega antes de llamar. Y al ser falso como una cadena vacía, las
comprobaciones `if not api_key` lo tratan como ausente sin cambiar nada.

`decrypt()` sigue lanzando cuando se llama directamente: ahí el contexto es una rotación, donde un
fallo sí debe parar el proceso.

---

## ADR-015 — Las métricas son un catálogo, no funciones sueltas
**Fecha:** 2026-09-14 · **Estado:** aceptada · **Amplía ADR-006**

**Contexto.** El plan original tenía seis funciones en `metrics.py`. Al diseñarlo con más detalle
aparecieron tres necesidades que una lista de funciones no cubre: que la persona vea qué mide cada
número, que el admin controle qué se le envía a la IA, y que el prompt no tenga hardcodeadas las
etiquetas y unidades de cada métrica.

**Decisión.** App `apps/metrics/` con tres capas: registro en código con metadatos (`@metric`),
catálogo en base de datos sincronizado con `sync_metrics`, y preferencias por usuario. 12 métricas
en cuatro categorías.

**Consecuencias.** La página de catálogo se genera sola desde los metadatos, y el prompt del
análisis de progreso se autodescribe: el modelo recibe cada número con su etiqueta, su unidad y su
descripción sin que haya que mantener esa correspondencia a mano.

El precio es mantener sincronizados código y base de datos. Se mitiga con dos reglas en
`sync_metrics`: **no pisa la configuración del admin** (`is_active`, `send_to_ai`) al actualizar, y
**desactiva en vez de borrar** las métricas retiradas, porque borrarlas arrastraría por cascada las
preferencias de todos los usuarios.

---

## ADR-016 — `coverage`: toda métrica dice cuántos datos tiene detrás
**Fecha:** 2026-09-14 · **Estado:** aceptada

**Contexto.** Varios campos de los que dependen las métricas son opcionales: el RPE de las series,
las horas de inicio y fin de sesión, el peso corporal. Con ellos vacíos, una métrica devuelve cero.

El problema es que **un cero es ambiguo**: puede significar «no entrenas ese músculo» o «no anotas
el RPE». La IA no tendría forma de distinguirlos, y el modo de fallo es de los peores posibles —
diría a alguien que no está entrenando lo suficiente cuando el problema es que no lo está anotando.

**Decisión.** Cada `MetricResult` lleva `coverage` (0–1): qué proporción de los datos necesarios
existe realmente. Cada métrica declara además de qué datos opcionales depende (`requires`), para
poder decir en concreto qué falta.

**Consecuencias.** El panel avisa cuando la cobertura baja del 80 % y dice qué registrar para
afinar el número. El prompt del análisis lleva la cobertura de cada métrica. Y una métrica sin
datos devuelve `coverage = 0.0`, no `1.0`: «no hay nada que medir» no es «está todo medido».

---

## ADR-014 — Decisiones metodológicas de las métricas
**Fecha:** 2026-09-14 · **Estado:** aceptada

**Contexto.** Tres preguntas sin respuesta obvia que cambian todos los números que después
interpreta la IA. Se eligieron con el usuario.

**Decisiones.**

1. **Músculos secundarios: directas 1.0, indirectas 0.5.** Un press de banca suma 1 serie a
   pectoral y 0,5 a tríceps y deltoides. Contar solo el objetivo haría parecer que el tríceps no se
   entrena, con el riesgo de que la IA recomendara añadirle volumen cuando ya está saturado.
2. **Peso corporal en el tonelaje: se usa el último peso registrado como carga**, más el lastre si
   lo hay. Diez dominadas de alguien de 75 kg son 750 kg, no cero. Sin ningún peso registrado, esas
   series no cuentan y baja la cobertura, en lugar de inventar una cifra. Afecta al ~25 % del
   catálogo.
3. **Series efectivas: cuentan todas las de trabajo; el RPE solo descarta.** Es el «hard set» de la
   literatura. Contar solo las que tienen RPE ≥ 7 dejaría la métrica casi vacía para quien no anota
   RPE (ver ADR-016).

**Consecuencias.** Viven concentradas en `apps/metrics/loads.py` y no repartidas por el catálogo,
para que haya un solo sitio donde leerlas y cambiarlas. Cada una tiene su test.

Límites añadidos en la implementación, por el mismo motivo: **Epley solo con 12 repeticiones o
menos** (por encima sobreestima y genera récords fantasma que el análisis leería como un pico real;
esas series siguen contando para volumen y tonelaje), y quedan fuera de volumen, tonelaje y fuerza
los calentamientos, las series no completadas y el cardio.

---

## ADR-013 — CSS propio en lugar de Tailwind
**Fecha:** 2026-09-14 · **Estado:** ~~aceptada~~ **SUSTITUIDA por ADR-019** · Sustituyó a su vez la
elección de Tailwind del plan inicial

**Contexto.** El plan aprobado decía «Tailwind, servido localmente» (ADR-011). Al ir a implementarlo,
ninguna de las vías era buena:

- **Tailwind v3 ya no publica un CSS precompilado.** `dist/tailwind.min.css` devuelve 404 tanto en
  unpkg como en jsDelivr; se eliminó del paquete npm.
- **El Play CDN compila en el navegador.** Funciona, pero la propia documentación de Tailwind lo
  desaconseja explícitamente para producción, e inyecta `<style>` en tiempo de ejecución.
- **El CLI standalone** resuelve ambas cosas, pero mete un binario de decenas de MB y un paso de
  build en un proyecto Django que por lo demás no necesita cadena de herramientas de frontend.

**Decisión.** Un sistema de diseño propio en `static/css/app.css`: variables CSS para el tema y
clases de componente (`.card`, `.btn`, `.badge`, `.grid`, `.field`…). Unas 300 líneas.

**Consecuencias.** Sin paso de build, sin binarios, sin advertencias de «no apto para producción», y
la CSP puede seguir siendo estricta porque no hace falta ningún `<style>` inline nuestro. A cambio
se pierde la ergonomía de las clases utilitarias y, si en el futuro entra alguien acostumbrado a
Tailwind, tendrá que leer el CSS en vez de aplicar lo que ya sabe. Para el tamaño de esta aplicación
compensa; si creciera mucho, el cambio sería añadir el CLI y reescribir plantillas.

**Regla que se mantiene:** nada de estilos inline en las plantillas. Todo pasa por una clase.

---

## ADR-012 — SimpleJWT en lugar del `TokenAuthentication` de DRF
**Fecha:** 2026-09-14 · **Estado:** aceptada

**Contexto.** La API REST necesita autenticación por token para un futuro cliente móvil.

**Decisión.** `djangorestframework-simplejwt`, con access de vida corta y refresh rotatorio con
blacklist.

**Consecuencias.** El `TokenAuthentication` que trae DRF guarda el token **en claro** en la base de
datos y **no caduca nunca**: un volcado de BD entrega sesiones permanentes y no hay forma de
revocarlas. SimpleJWT permite expiración y revocación. El coste es gestionar el refresh en el cliente.
