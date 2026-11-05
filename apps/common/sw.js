const CONFIG = /*__CONFIG__*/ { version: "sin-version", precarga: [], cascara: "/entrar/", activo: false, icono: "" };

const PREFIJO = "gym-";
const CACHE = `${PREFIJO}${CONFIG.version}`;
const CASCARA = "/__cascara__";
const PACIENCIA_MS = 4000;

const NUNCA = ["/api/", "/admin/", "/media/", "/static/admin/", "/sw.js", "/manifest.webmanifest"];

self.addEventListener("install", (evento) => {
  if (!CONFIG.activo) {
    self.skipWaiting();
    return;
  }
  evento.waitUntil(precargar());
});

self.addEventListener("activate", (evento) => {
  evento.waitUntil(
    (async () => {
      const nombres = await caches.keys();
      await Promise.all(
        nombres
          .filter((nombre) => nombre.startsWith(PREFIJO) && (nombre !== CACHE || !CONFIG.activo))
          .map((nombre) => caches.delete(nombre)),
      );
      await self.clients.claim();
    })(),
  );
});

self.addEventListener("message", (evento) => {
  if (evento.data && evento.data.tipo === "SALTAR_ESPERA") self.skipWaiting();

  if (evento.data && evento.data.tipo === "CAPACIDADES" && evento.ports && evento.ports[0]) {
    evento.ports[0].postMessage({ push: 1 });
  }
});

self.addEventListener("fetch", (evento) => {
  if (!CONFIG.activo) return;

  const peticion = evento.request;
  if (peticion.method !== "GET") return;

  const url = new URL(peticion.url);
  if (url.origin !== self.location.origin) return;
  if (NUNCA.some((prefijo) => url.pathname === prefijo || url.pathname.startsWith(prefijo))) return;

  if (peticion.mode === "navigate") {
    evento.respondWith(navegar(evento));
  } else if (url.pathname.startsWith("/static/")) {
    evento.respondWith(estatico(peticion));
  }
});

async function precargar() {
  const cache = await caches.open(CACHE);
  await cache.addAll(CONFIG.precarga.map((url) => new Request(url, { cache: "reload" })));

  const respuesta = await fetch(CONFIG.cascara, {
    cache: "no-store",
    credentials: "omit",
    redirect: "error",
  });
  const html = await respuesta.clone().text();

  if (!respuesta.ok || respuesta.redirected || !html.includes(CONFIG.version)) {
    throw new Error("La cáscara no es de esta versión");
  }
  await cache.put(CASCARA, respuesta);
}

async function navegar(evento) {
  const cascara = await caches.match(CASCARA, { cacheName: CACHE });

  try {
    const respuesta = await conPaciencia(fetch(evento.request), cascara ? PACIENCIA_MS : 0);
    if (respuesta.status >= 500 && cascara) return cascara;
    if (!cascara) evento.waitUntil(precargar().catch(() => {}));
    return respuesta;
  } catch {
    return cascara || paginaSinConexion();
  }
}

async function estatico(peticion) {
  const guardada = await caches.match(peticion, { cacheName: CACHE });
  if (guardada) return guardada;

  const respuesta = await fetch(peticion);
  const delBuild = new URL(peticion.url).pathname.startsWith("/static/spa/assets/");
  if (respuesta.ok && respuesta.type === "basic" && delBuild && (await caches.has(CACHE))) {
    const cache = await caches.open(CACHE);
    await cache.put(peticion, respuesta.clone());
  }
  return respuesta;
}

function conPaciencia(promesa, ms) {
  if (!ms) return promesa;
  return Promise.race([
    promesa,
    new Promise((_, rechazar) => setTimeout(() => rechazar(new Error("sin respuesta")), ms)),
  ]);
}

function paginaSinConexion() {
  const html = `<!doctype html><html lang="es"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sin conexión · FitUp</title>
<style>
  body { margin: 0; min-height: 100vh; display: grid; place-items: center; text-align: center;
         font: 17px/1.4 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
         background: #f2f2f7; color: #1c1c1e; padding: 24px; box-sizing: border-box; }
  @media (prefers-color-scheme: dark) { body { background: #000000; color: #f5f5f7; } }
  h1 { font-size: 22px; margin: 0 0 8px; }
  p { margin: 0; opacity: .75; max-width: 22rem; }
</style>
<main><h1>Sin conexión</h1>
<p>FitUp necesita red la primera vez que se abre. Vuelve a intentarlo cuando tengas cobertura.</p></main>
</html>`;
  return new Response(html, {
    status: 503,
    headers: {
      "Content-Type": "text/html; charset=utf-8",
      "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'",
      "Cache-Control": "no-store",
    },
  });
}

function mismoOrigen(url) {
  try {
    return new URL(url, self.location.origin).origin === self.location.origin;
  } catch {
    return false;
  }
}

function esWebKit() {
  const agente = self.navigator.userAgent;
  return /AppleWebKit/.test(agente) && !/Chrome|Chromium|Edg/.test(agente);
}

self.addEventListener("push", (evento) => {
  let datos = {};
  try {
    datos = evento.data ? evento.data.json() : {};
  } catch {
    datos = {};
  }
  const url = mismoOrigen(datos.url) ? new URL(datos.url, self.location.origin) : null;

  evento.waitUntil(
    (async () => {
      const ventanas = await self.clients.matchAll({ type: "window", includeUncontrolled: true });
      const mirando =
        url &&
        ventanas.some(
          (ventana) =>
            ventana.focused &&
            ventana.visibilityState === "visible" &&
            new URL(ventana.url).pathname === url.pathname,
        );
      if (mirando && !esWebKit()) return;

      await self.registration.showNotification(datos.titulo || "FitUp", {
        body: datos.cuerpo || "",
        tag: datos.tag || "aviso",
        renotify: true,
        vibrate: [200, 100, 200],
        icon: CONFIG.icono || undefined,
        badge: CONFIG.icono || undefined,
        data: { url: url ? url.pathname : "/" },
        lang: "es",
      });
    })(),
  );
});

self.addEventListener("notificationclick", (evento) => {
  evento.notification.close();
  const destino = new URL(
    (evento.notification.data && evento.notification.data.url) || "/",
    self.location.origin,
  );
  if (destino.origin !== self.location.origin) return;

  evento.waitUntil(
    (async () => {
      const ventanas = await self.clients.matchAll({ type: "window", includeUncontrolled: true });
      const misma = ventanas.find((ventana) => new URL(ventana.url).pathname === destino.pathname);
      if (misma) return misma.focus();

      const cualquiera = ventanas[0];
      if (cualquiera) {
        await cualquiera.focus();
        try {
          return await cualquiera.navigate(destino.href);
        } catch {
        }
      }
      return self.clients.openWindow(destino.href);
    })(),
  );
});
