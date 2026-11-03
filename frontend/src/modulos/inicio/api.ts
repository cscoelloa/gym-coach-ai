import { useQuery } from "@tanstack/react-query";

import { api } from "@/api/cliente";
import type { NivelesPorMusculo } from "@/ds/BodyMap";
import type { SerieDePeso } from "@/ds/GraficaDePeso";

export type DiaDeLaSemanaApi = {
  fecha: string;
  inicial: string;
  numero: number;
  hoy: boolean;
  futuro: boolean;
  entrenado: boolean;
  planificado: boolean;
};

export type HoyToca = {
  estado: "sesion_abierta" | "sin_programa" | "descanso" | "rutina";
  sesion: { id: number; fecha: string } | null;
  rutina: { id: number; nombre: string; ejercicios: string[] } | null;
};

export type Inicio = {
  hoy: string;
  semana: DiaDeLaSemanaApi[];
  hoy_toca: HoyToca;
  peso: {
    ultimo: { fecha: string; kg: number } | null;
    cambio: number | null;
    objetivo: string;
    meta_kg: number | null;
    serie: SerieDePeso | null;
  };
  racha: {
    semanas: number;
    hechas_esta_semana: number;
    planificadas_esta_semana: number;
    total_sesiones: number;
  };
  mapa_corporal: NivelesPorMusculo;
};

export function useInicio() {
  return useQuery({
    queryKey: ["inicio"],
    queryFn: () => api<Inicio>("/api/inicio/"),
  });
}
