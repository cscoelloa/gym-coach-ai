import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/api/cliente";
import type { SemanaDelCalendario } from "@/ds/CalendarioDeActividad";
import type { PuntoDeMetrica } from "@/ds/GraficaDeMetrica";
import type { SerieDePeso } from "@/ds/GraficaDePeso";

export type { DiaDelCalendario, SemanaDelCalendario } from "@/ds/CalendarioDeActividad";

export type Progreso = {
  hoy: string;
  cifras: {
    total_sesiones: number;
    sesiones_este_mes: number;
    racha_semanas: number;
    peso_30_dias: number | null;
  };
  calendario: { semanas: SemanaDelCalendario[]; niveles: number[] };
  peso: { serie: SerieDePeso | null };
  mapa_corporal: {
    niveles: Record<string, number>;
    series: Record<string, number>;
    total_series: number;
    desde: string;
  };
  por_dia_de_semana: { weekday: number; inicial: string; sesiones: number }[];
  semanas_por_dia: number;
};

export type MetricaCalculada = {
  key: string;
  label: string;
  description: string;
  unit: string;
  category: string;
  category_label: string;
  chart: "line" | "bar" | "table" | "scalar";
  value: number | string | null;
  series: PuntoDeMetrica[];
  columns: string[];
  rows: (string | number)[][];
  coverage: number;
  coverage_pct: number;
  notes: string[];
  has_no_data: boolean;
  is_reliable: boolean;
  empty_hint: string;
  needs: string[];
};

export type MetricaDelCatalogo = {
  key: string;
  label: string;
  description: string;
  unit: string;
  category: string;
  category_label: string;
  chart: string;
  visible: boolean;
};

export function useProgreso() {
  return useQuery({
    queryKey: ["progreso"],
    queryFn: () => api<Progreso>("/api/progreso/"),
  });
}

export function useMisMetricas() {
  return useQuery({
    queryKey: ["mis-metricas"],
    queryFn: () => api<MetricaCalculada[]>("/api/mis-metricas/"),
    staleTime: 5 * 60_000,
  });
}

export function useCatalogoDeMetricas() {
  return useQuery({
    queryKey: ["metricas"],
    queryFn: () => api<MetricaDelCatalogo[]>("/api/metricas/"),
  });
}

export function useGuardarMetricas() {
  const cache = useQueryClient();

  return useMutation({
    mutationFn: (keys: string[]) =>
      api<{ visibles: string[] }>("/api/metricas/preferencias/", {
        metodo: "PUT",
        cuerpo: { keys },
      }),
    onSuccess: () => {
      cache.invalidateQueries({ queryKey: ["metricas"] });
      cache.invalidateQueries({ queryKey: ["mis-metricas"] });
    },
  });
}
