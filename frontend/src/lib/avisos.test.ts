import { http, HttpResponse } from "msw";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { servidor } from "@/test/servidor";

import { _reiniciar, activarAvisos, olvidarEsteDispositivo } from "./avisos";

const CLAVE = btoa(String.fromCharCode(4, ...new Array(64).fill(1)))
  .replace(/\+/g, "-")
  .replace(/\//g, "_")
  .replace(/=+$/, "");

const JSON_DE_LA_SUSCRIPCION = {
  endpoint: "https://fcm.googleapis.com/fcm/send/abc",
  keys: { p256dh: "p", auth: "a" },
};

function navegador({ contesta = true, permiso = "granted" as NotificationPermission } = {}) {
  const suscripcion = {
    endpoint: JSON_DE_LA_SUSCRIPCION.endpoint,
    options: { applicationServerKey: null },
    toJSON: () => JSON_DE_LA_SUSCRIPCION,
    unsubscribe: vi.fn(async () => true),
  };
  let actual: typeof suscripcion | null = null;
  const pushManager = {
    getSubscription: vi.fn(async () => actual),
    subscribe: vi.fn(async () => {
      actual = suscripcion;
      return suscripcion;
    }),
  };
  const registro = {
    pushManager,
    active: {
      postMessage: (_mensaje: unknown, [puerto]: MessagePort[]) => {
        if (contesta) puerto!.postMessage({ push: 1 });
      },
    },
  };

  vi.stubGlobal("Notification", {
    permission: "default",
    requestPermission: vi.fn(async () => permiso),
  });
  Object.defineProperty(navigator, "serviceWorker", {
    value: { getRegistration: async () => registro },
    configurable: true,
  });

  return {
    pushManager,
    suscripcion,
    yaSuscrito() {
      actual = suscripcion;
    },
  };
}

beforeEach(() => _reiniciar());
afterEach(() => {
  vi.unstubAllGlobals();
  // @ts-expect-error: se quita lo que puso el test.
  delete navigator.serviceWorker;
});

describe("activarAvisos", () => {
  it("con permiso suscribe y se lo manda al servidor", async () => {
    const { pushManager } = navegador();
    let recibido: unknown = null;
    servidor.use(
      http.post("/api/avisos/suscripcion/", async ({ request }) => {
        recibido = await request.json();
        return new HttpResponse(null, { status: 204 });
      }),
    );

    expect(await activarAvisos(CLAVE)).toBe("activo");

    expect(pushManager.subscribe).toHaveBeenCalledWith(
      expect.objectContaining({ userVisibleOnly: true }),
    );
    expect(recibido).toEqual(JSON_DE_LA_SUSCRIPCION);
  });

  it("sin permiso no se suscribe ni pregunta al servidor", async () => {
    const { pushManager } = navegador({ permiso: "denied" });

    expect(await activarAvisos(CLAVE)).toBe("denegado");
    expect(pushManager.subscribe).not.toHaveBeenCalled();
  });

  it("con un service worker que no sabe recibirlos, pide actualizar en vez de suscribirse", async () => {
    const { pushManager } = navegador({ contesta: false });

    expect(await activarAvisos(CLAVE)).toBe("actualizar");
    expect(pushManager.subscribe).not.toHaveBeenCalled();
  });
});

describe("olvidarEsteDispositivo", () => {
  it("borra la suscripción en el servidor y en el navegador", async () => {
    const { suscripcion, yaSuscrito } = navegador();
    yaSuscrito();
    let borrado: unknown = null;
    servidor.use(
      http.delete("/api/avisos/suscripcion/", async ({ request }) => {
        borrado = await request.json();
        return new HttpResponse(null, { status: 204 });
      }),
    );

    await olvidarEsteDispositivo();

    expect(borrado).toEqual({ endpoint: JSON_DE_LA_SUSCRIPCION.endpoint });
    expect(suscripcion.unsubscribe).toHaveBeenCalledOnce();
  });

  it("si el servidor no contesta, el navegador se da de baja igual", async () => {
    const { suscripcion, yaSuscrito } = navegador();
    yaSuscrito();
    servidor.use(http.delete("/api/avisos/suscripcion/", () => HttpResponse.error()));

    await olvidarEsteDispositivo();

    expect(suscripcion.unsubscribe).toHaveBeenCalledOnce();
  });

  it("sin service worker no hace nada ni falla", async () => {
    await expect(olvidarEsteDispositivo()).resolves.toBeUndefined();
  });
});
