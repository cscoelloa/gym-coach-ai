import { useQuery } from "@tanstack/react-query";
import { useEffect, useState, useSyncExternalStore } from "react";

import { api } from "@/api/cliente";

export type Clave = { activo: boolean; clave: string | null };

export type EstadoDeAvisos =
  | "no"
  | "instalar"
  | "cargando"
  | "bloqueado"
  | "inactivo"
  | "activo";

export type ResultadoDeActivar = "activo" | "denegado" | "actualizar" | "error";

function esIOS(): boolean {
  const agente = navigator.userAgent;
  return /iPhone|iPad|iPod/.test(agente) || (/Macintosh/.test(agente) && navigator.maxTouchPoints > 1);
}

function instalada(): boolean {
  return (
    window.matchMedia?.("(display-mode: standalone)").matches ||
    (navigator as Navigator & { standalone?: boolean }).standalone === true
  );
}

export function soporte(): "si" | "no" | "instalar" {
  if (!("serviceWorker" in navigator) || typeof Notification === "undefined") {
    return esIOS() && !instalada() ? "instalar" : "no";
  }
  if (!("PushManager" in window)) return esIOS() && !instalada() ? "instalar" : "no";
  return "si";
}

function aBytes(base64url: string): Uint8Array<ArrayBuffer> {
  const relleno = "=".repeat((4 - (base64url.length % 4)) % 4);
  const crudo = atob((base64url + relleno).replace(/-/g, "+").replace(/_/g, "/"));
  const bytes = new Uint8Array(new ArrayBuffer(crudo.length));
  for (let i = 0; i < crudo.length; i++) bytes[i] = crudo.charCodeAt(i);
  return bytes;
}

function mismaClave(suscripcion: PushSubscription, clave: string): boolean {
  const suya = suscripcion.options?.applicationServerKey;
  if (!suya) return true;
  const a = new Uint8Array(suya);
  const b = aBytes(clave);
  return a.length === b.length && a.every((byte, i) => byte === b[i]);
}

function sabeRecibirAvisos(registro: ServiceWorkerRegistration): Promise<boolean> {
  const activo = registro.active;
  if (!activo) return Promise.resolve(false);
  return new Promise((resolver) => {
    const canal = new MessageChannel();
    const plazo = setTimeout(() => resolver(false), 1500);
    canal.port1.onmessage = (evento) => {
      clearTimeout(plazo);
      resolver(Boolean(evento.data?.push));
    };
    activo.postMessage({ tipo: "CAPACIDADES" }, [canal.port2]);
  });
}

async function registro(): Promise<ServiceWorkerRegistration | undefined> {
  if (!("serviceWorker" in navigator)) return undefined;
  return navigator.serviceWorker.getRegistration();
}

type Local = { suscrito: boolean | null; permiso: NotificationPermission | null };

let local: Local = { suscrito: null, permiso: null };
const oyentes = new Set<() => void>();
let reenviada = false;

function cambiar(siguiente: Partial<Local>) {
  local = { ...local, ...siguiente };
  for (const oyente of oyentes) oyente();
}

async function comprobar(clave: string) {
  const permiso = Notification.permission;
  const sus = await (await registro())?.pushManager?.getSubscription();

  if (sus && permiso !== "granted") {
    await sus.unsubscribe().catch(() => false);
    return cambiar({ suscrito: false, permiso });
  }
  if (sus && !reenviada && mismaClave(sus, clave)) {
    reenviada = true;
    await api("/api/avisos/suscripcion/", { metodo: "POST", cuerpo: sus.toJSON() }).catch(() => {});
  }
  cambiar({ suscrito: Boolean(sus && mismaClave(sus, clave)), permiso });
}

export async function activarAvisos(clave: string): Promise<ResultadoDeActivar> {
  const permiso = await Notification.requestPermission();
  cambiar({ permiso });
  if (permiso !== "granted") return "denegado";

  const trabajador = await registro();
  if (!trabajador) return "error";
  if (!(await sabeRecibirAvisos(trabajador))) return "actualizar";

  try {
    let sus = await trabajador.pushManager.getSubscription();
    if (sus && !mismaClave(sus, clave)) {
      await sus.unsubscribe();
      sus = null;
    }
    sus ??= await trabajador.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: aBytes(clave),
    });
    await api("/api/avisos/suscripcion/", { metodo: "POST", cuerpo: sus.toJSON() });
    reenviada = true;
    cambiar({ suscrito: true });
    return "activo";
  } catch {
    return "error";
  }
}

export async function olvidarEsteDispositivo({ avisarAlServidor = true } = {}) {
  try {
    const sus = await (await registro())?.pushManager?.getSubscription();
    if (!sus) return;
    if (avisarAlServidor) {
      await api("/api/avisos/suscripcion/", {
        metodo: "DELETE",
        cuerpo: { endpoint: sus.endpoint },
      }).catch(() => {});
    }
    await sus.unsubscribe().catch(() => false);
  } catch {
  } finally {
    reenviada = false;
    cambiar({ suscrito: false });
  }
}

function suscribir(avisame: () => void) {
  oyentes.add(avisame);
  return () => oyentes.delete(avisame);
}

export function useAvisos() {
  const apoyo = soporte();
  const clave = useQuery({
    queryKey: ["avisos", "clave"],
    queryFn: () => api<Clave>("/api/avisos/clave/"),
    enabled: apoyo === "si",
    staleTime: Infinity,
  });
  const estadoLocal = useSyncExternalStore(suscribir, () => local, () => local);
  const [ocupado, setOcupado] = useState(false);
  const [resultado, setResultado] = useState<ResultadoDeActivar | null>(null);
  const publica = clave.data?.activo ? clave.data.clave : null;

  useEffect(() => {
    if (publica) void comprobar(publica).catch(() => cambiar({ suscrito: false }));
  }, [publica]);

  let estado: EstadoDeAvisos;
  if (apoyo !== "si") estado = apoyo;
  else if (clave.isPending) estado = "cargando";
  else if (!publica) estado = "no";
  else if ((estadoLocal.permiso ?? Notification.permission) === "denied") estado = "bloqueado";
  else if (estadoLocal.suscrito === null) estado = "cargando";
  else estado = estadoLocal.suscrito ? "activo" : "inactivo";

  async function activar() {
    if (!publica) return;
    setOcupado(true);
    try {
      setResultado(await activarAvisos(publica));
    } finally {
      setOcupado(false);
    }
  }

  async function desactivar() {
    setOcupado(true);
    try {
      await olvidarEsteDispositivo();
      setResultado(null);
    } finally {
      setOcupado(false);
    }
  }

  return { estado, activar, desactivar, ocupado, resultado };
}

export function _reiniciar() {
  reenviada = false;
  local = { suscrito: null, permiso: null };
}
