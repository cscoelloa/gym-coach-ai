import { useSyncExternalStore } from "react";

type Estado = { disponible: boolean };

let estado: Estado = { disponible: false };
const oyentes = new Set<() => void>();
let enEspera: ServiceWorker | null = null;
let pidioActualizar = false;
let retenciones = 0;

function cambiar(siguiente: Estado) {
  estado = siguiente;
  for (const oyente of oyentes) oyente();
}

function intentarAuto() {
  if (!enEspera || retenciones > 0 || pidioActualizar) return;
  pidioActualizar = true;
  enEspera.postMessage({ tipo: "SALTAR_ESPERA" });
}

function hayVersionNueva(trabajador: ServiceWorker | null) {
  enEspera = trabajador;
  cambiar({ disponible: true });
  intentarAuto();
}

export function retenerActualizacion() {
  retenciones += 1;
  let liberado = false;
  return () => {
    if (liberado) return;
    liberado = true;
    retenciones -= 1;
    intentarAuto();
  };
}

const CADA = 60 * 1000;

export function registrarServiceWorker() {
  if (!import.meta.env.PROD || !("serviceWorker" in navigator)) return;

  const controladaAlEmpezar = Boolean(navigator.serviceWorker.controller);

  navigator.serviceWorker.addEventListener("controllerchange", () => {
    if (pidioActualizar) {
      window.location.reload();
    } else if (controladaAlEmpezar) {
      if (retenciones === 0) window.location.reload();
      else cambiar({ disponible: true });
    }
  });

  window.addEventListener("load", () => {
    navigator.serviceWorker
      .register("/sw.js", { updateViaCache: "none" })
      .then((registro) => {
        if (registro.waiting && navigator.serviceWorker.controller) {
          hayVersionNueva(registro.waiting);
        }

        registro.addEventListener("updatefound", () => {
          const nuevo = registro.installing;
          nuevo?.addEventListener("statechange", () => {
            if (nuevo.state === "installed" && navigator.serviceWorker.controller) {
              hayVersionNueva(nuevo);
            }
          });
        });

        let ultima = Date.now();
        document.addEventListener("visibilitychange", () => {
          if (document.visibilityState !== "visible" || Date.now() - ultima < CADA) return;
          ultima = Date.now();
          void registro.update().catch(() => {});
        });
      })
      .catch(() => {});
  });
}

export function aplicarActualizacion() {
  if (enEspera) {
    pidioActualizar = true;
    enEspera.postMessage({ tipo: "SALTAR_ESPERA" });
  } else {
    window.location.reload();
  }
}

export function useActualizacion(): Estado {
  return useSyncExternalStore(
    (avisar) => {
      oyentes.add(avisar);
      return () => oyentes.delete(avisar);
    },
    () => estado,
    () => estado,
  );
}

export async function borrarCachesDeLaApp() {
  if (typeof caches === "undefined") return;
  const nombres = await caches.keys();
  await Promise.all(
    nombres.filter((nombre) => nombre.startsWith("gym-")).map((nombre) => caches.delete(nombre)),
  );
}

export function _reiniciar() {
  enEspera = null;
  pidioActualizar = false;
  retenciones = 0;
  cambiar({ disponible: false });
}

export function _anunciar(trabajador: ServiceWorker | null) {
  hayVersionNueva(trabajador);
}
