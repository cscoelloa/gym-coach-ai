import { esRutaDeLaSpa } from "@/rutas";

import type { NombreDeIcono } from "./Icono";

export type Destino = {
  clave: string;
  etiqueta: string;
  url: string;
  icono: NombreDeIcono;
  centro?: boolean;
};

export const DESTINOS: readonly Destino[] = [
  { clave: "dashboard", etiqueta: "Inicio", url: "/", icono: "inicio" },
  { clave: "routines", etiqueta: "Plan", url: "/plan/", icono: "plan" },
  {
    clave: "sessions",
    etiqueta: "Entrenar",
    url: "/entrenamientos/",
    icono: "entrenar",
    centro: true,
  },
  { clave: "progress", etiqueta: "Progreso", url: "/progreso/", icono: "progreso" },
  { clave: "exercises", etiqueta: "Ejercicios", url: "/ejercicios/", icono: "ejercicios" },
];

export function esDestino(camino: string): boolean {
  return DESTINOS.some((destino) => destino.url === camino);
}

export type Padre = { url: string; etiqueta: string };

const PADRES: ReadonlyArray<[RegExp, string]> = [
  [/^\/entrenamientos\/[^/]+\/cierre\/$/, "/entrenamientos/"],
  [/^\/rutinas\//, "/plan/"],
  [/^\/programas\//, "/plan/"],
  [/^\/ia\/generar\/$/, "/plan/"],
  [/^\/ia\/propuestas\//, "/plan/"],
  [/^\/ia\/analisis\/$/, "/progreso/"],
  [/^\/metricas\/$/, "/progreso/"],
  [/^\/peso\/$/, "/"],
  [/^\/notificaciones\/$/, "/"],
  [/^\/perfil\/$/, "/"],
  [/^\/estilos\/$/, "/"],
  [/^\/gestion\/$/, "/"],
];

const NOMBRES: Record<string, string> = {
  "/perfil/": "Perfil",
  "/gestion/": "Gestión",
};

function nombreDe(url: string): string {
  return DESTINOS.find((destino) => destino.url === url)?.etiqueta ?? NOMBRES[url] ?? "Atrás";
}

export function padreDe(camino: string): Padre {
  for (const [patron, url] of PADRES) {
    if (patron.test(camino)) return { url, etiqueta: nombreDe(url) };
  }

  const trozos = camino.split("/").filter(Boolean);
  while (trozos.length > 0) {
    trozos.pop();
    const candidato = trozos.length ? `/${trozos.join("/")}/` : "/";
    if (esRutaDeLaSpa(candidato)) return { url: candidato, etiqueta: nombreDe(candidato) };
  }
  return { url: "/", etiqueta: "Inicio" };
}
