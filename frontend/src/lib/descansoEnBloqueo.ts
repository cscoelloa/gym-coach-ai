import { useEffect, useState } from "react";

import { formatearCuenta } from "@/ds/RestTimer";

import silencio from "./silencio.wav";

const CLAVE = "gym-descanso-bloqueo";
const ESPERA_SIN_DESCANSO_MS = 5000;
const CONTROLES_SIN_USO = [
  "seekbackward",
  "seekforward",
  "seekto",
  "previoustrack",
  "nexttrack",
] as const;

let audio: HTMLAudioElement | null = null;
let sonando = false;
let mostrando = false;
let apagado: ReturnType<typeof setTimeout> | null = null;

export function soportado(): boolean {
  return (
    typeof navigator !== "undefined" &&
    "mediaSession" in navigator &&
    typeof MediaMetadata !== "undefined" &&
    typeof Audio !== "undefined"
  );
}

function caratula(): MediaImage[] {
  const icono = document.querySelector<HTMLLinkElement>('link[rel="apple-touch-icon"]');
  return icono ? [{ src: icono.href, sizes: "180x180", type: "image/png" }] : [];
}

function seguirSonando() {
  if (audio && sonando) void audio.play()?.catch(() => {});
}

function registrarControles() {
  const sesion = navigator.mediaSession;
  sesion.setActionHandler("play", seguirSonando);
  sesion.setActionHandler("pause", seguirSonando);
  for (const accion of CONTROLES_SIN_USO) {
    try {
      sesion.setActionHandler(accion, null);
    } catch {
    }
  }
}

function cancelarApagado() {
  if (apagado !== null) clearTimeout(apagado);
  apagado = null;
}

export function ocultar() {
  cancelarApagado();
  mostrando = false;
  sonando = false;
  audio?.pause();
  if (!soportado()) return;
  navigator.mediaSession.metadata = null;
  navigator.mediaSession.playbackState = "none";
}

export function armar() {
  if (!soportado()) return;
  if (!audio) {
    audio = new Audio(silencio);
    audio.loop = true;
    audio.addEventListener("playing", registrarControles);
  }
  if (navigator.audioSession) navigator.audioSession.type = "playback";
  sonando = true;
  void audio.play()?.catch(() => {
    sonando = false;
  });
  cancelarApagado();
  if (!mostrando) {
    apagado = setTimeout(() => {
      if (!mostrando) ocultar();
    }, ESPERA_SIN_DESCANSO_MS);
  }
}

export function mostrar(restante: number, total: number) {
  if (!soportado() || !sonando) return;
  cancelarApagado();
  mostrando = true;

  const sesion = navigator.mediaSession;
  const titulo = `Descanso · ${formatearCuenta(restante)}`;
  if (sesion.metadata) sesion.metadata.title = titulo;
  else sesion.metadata = new MediaMetadata({ title: titulo, artist: "FitUp", artwork: caratula() });
  sesion.playbackState = "playing";

  const duracion = Math.max(total, restante, 1);
  try {
    sesion.setPositionState({ duration: duracion, position: duracion - restante, playbackRate: 1 });
  } catch {
  }
}

function leer(): boolean {
  try {
    return localStorage.getItem(CLAVE) === "1";
  } catch {
    return false;
  }
}

export function useDescansoEnBloqueo(restante: number | null, total: number) {
  const disponible = soportado();
  const [activo, setActivo] = useState(() => disponible && leer());

  useEffect(() => {
    if (!activo) return;
    if (restante === null) ocultar();
    else mostrar(restante, total);
  }, [activo, restante, total]);

  useEffect(() => () => ocultar(), []);

  function cambiar() {
    const siguiente = !activo;
    setActivo(siguiente);
    try {
      localStorage.setItem(CLAVE, siguiente ? "1" : "0");
    } catch {
    }
    if (!siguiente) return ocultar();
    armar();
    if (restante !== null) mostrar(restante, total);
  }

  function armarSiHaceFalta() {
    if (activo) armar();
  }

  return { disponible, activo, cambiar, armar: armarSiHaceFalta };
}

export function _reiniciar() {
  cancelarApagado();
  audio = null;
  sonando = false;
  mostrando = false;
}
