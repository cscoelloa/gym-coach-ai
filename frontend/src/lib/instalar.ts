import { useSyncExternalStore } from "react";

export type ModoDeInstalacion = "prompt" | "ios" | null;

let aviso: BeforeInstallPromptEvent | null = null;
let instalada = false;
const oyentes = new Set<() => void>();
let modoActual: ModoDeInstalacion = null;

function enStandalone(): boolean {
  return (
    window.matchMedia?.("(display-mode: standalone)")?.matches === true ||
    navigator.standalone === true
  );
}

export function esIos(agente = navigator.userAgent, plataforma = navigator.platform): boolean {
  if (/iPad|iPhone|iPod/.test(agente)) return true;
  return plataforma === "MacIntel" && navigator.maxTouchPoints > 1;
}

function calcular(): ModoDeInstalacion {
  if (instalada || enStandalone()) return null;
  if (aviso) return "prompt";
  if (esIos()) return "ios";
  return null;
}

function avisar() {
  modoActual = calcular();
  for (const oyente of oyentes) oyente();
}

export function escucharInstalacion() {
  window.addEventListener("beforeinstallprompt", (evento) => {
    aviso = evento;
    avisar();
  });
  window.addEventListener("appinstalled", () => {
    aviso = null;
    instalada = true;
    avisar();
  });
  modoActual = calcular();
}

async function instalar() {
  if (!aviso) return;
  const evento = aviso;
  aviso = null;
  await evento.prompt();
  await evento.userChoice.catch(() => undefined);
  avisar();
}

export function useInstalacion(): { modo: ModoDeInstalacion; instalar: () => Promise<void> } {
  const modo = useSyncExternalStore(
    (oyente) => {
      oyentes.add(oyente);
      return () => oyentes.delete(oyente);
    },
    () => modoActual,
    () => null,
  );
  return { modo, instalar };
}

export function _reiniciar() {
  aviso = null;
  instalada = false;
  avisar();
}
