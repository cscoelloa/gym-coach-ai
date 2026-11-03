import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/api/cliente";
import type { Paginado } from "@/api/tipos";
import type { ConfigDeEjercicio } from "@/ds/ConfigDeSeries";
import type { Ejercicio } from "@/modulos/ejercicios/api";

export type DiaDelPlan = {
  weekday: number;
  etiqueta: string;
  entrada_id: number | null;
  rutina: { id: number; nombre: string } | null;
};

export type RutinaEnBiblioteca = {
  id: number;
  nombre: string;
  descripcion: string;
  n_ejercicios: number;
  dias: string[];
};

export type Plan = {
  hoy_weekday: number;
  programa: { id: number; nombre: string; descripcion: string } | null;
  programas: { id: number; nombre: string; activo: boolean }[];
  semana: DiaDelPlan[];
  rutinas: RutinaEnBiblioteca[];
};

const CLAVE = ["plan"] as const;

export function usePlan() {
  return useQuery({ queryKey: CLAVE, queryFn: () => api<Plan>("/api/plan/") });
}

function invalidarPlan(cache: ReturnType<typeof useQueryClient>) {
  cache.invalidateQueries({ queryKey: CLAVE });
  cache.invalidateQueries({ queryKey: ["inicio"] });
}

export function useAsignarRutina() {
  const cache = useQueryClient();

  return useMutation({
    mutationFn: ({ entrada, rutina }: { entrada: number; rutina: number | null }) =>
      api(`/api/dias/${entrada}/`, { metodo: "PATCH", cuerpo: { routine: rutina } }),
    onSuccess: () => invalidarPlan(cache),
  });
}

export function useCrearPrograma() {
  const cache = useQueryClient();

  return useMutation({
    mutationFn: (datos: { name: string; description?: string }) =>
      api<{ id: number }>("/api/programas/", { metodo: "POST", cuerpo: datos }),
    onSuccess: () => invalidarPlan(cache),
  });
}

export function useActivarPrograma() {
  const cache = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => api(`/api/programas/${id}/activate/`, { metodo: "POST" }),
    onSuccess: () => invalidarPlan(cache),
  });
}

export function useBorrarPrograma() {
  const cache = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => api<void>(`/api/programas/${id}/`, { metodo: "DELETE" }),
    onSuccess: () => invalidarPlan(cache),
  });
}

export type EjercicioDeRutina = {
  id: number;
  routine: number;
  exercise: number;
  exercise_detail: Ejercicio;
  order: number;
  target_sets: number;
  target_reps_min: number;
  target_reps_max: number;
  rest_seconds: number;
};

export type Rutina = {
  id: number;
  name: string;
  description: string;
  source: string;
  source_label: string;
  created_at: string;
  exercises: EjercicioDeRutina[];
};

export type BorradorDeRutina = {
  name: string;
  description: string;
  exercises: (ConfigDeEjercicio & { id?: number; exercise: number })[];
};

export function useGuardarRutinaCompleta() {
  const cache = useQueryClient();
  return useMutation({
    mutationFn: ({ id, datos }: { id?: number; datos: BorradorDeRutina }) =>
      api<Rutina>(id ? `/api/rutinas/${id}/` : "/api/rutinas/", {
        metodo: id ? "PATCH" : "POST", cuerpo: datos,
      }),
    onSuccess: (rutina) => {
      cache.setQueryData(["rutinas", rutina.id], rutina);
      invalidarPlan(cache);
    },
  });
}

export function useRutina(id: number) {
  return useQuery({
    queryKey: ["rutinas", id],
    queryFn: () => api<Rutina>(`/api/rutinas/${id}/`),
    enabled: Number.isFinite(id),
  });
}

export function useCrearRutina() {
  const cache = useQueryClient();

  return useMutation({
    mutationFn: (datos: { name: string; description?: string }) =>
      api<Rutina>("/api/rutinas/", { metodo: "POST", cuerpo: datos }),
    onSuccess: () => invalidarPlan(cache),
  });
}

export function useBorrarRutina() {
  const cache = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => api<void>(`/api/rutinas/${id}/`, { metodo: "DELETE" }),
    onSuccess: () => invalidarPlan(cache),
  });
}

export type { ConfigDeEjercicio } from "@/ds/ConfigDeSeries";

function invalidarRutina(cache: ReturnType<typeof useQueryClient>, rutina: number) {
  cache.invalidateQueries({ queryKey: ["rutinas", rutina] });
  cache.invalidateQueries({ queryKey: CLAVE });
}

export function useAnadirEjercicio(rutina: number) {
  const cache = useQueryClient();

  return useMutation({
    mutationFn: ({
      ejercicio,
      config,
    }: {
      ejercicio: number;
      config?: Partial<ConfigDeEjercicio>;
    }) =>
      api<EjercicioDeRutina>("/api/rutina-ejercicios/", {
        metodo: "POST",
        cuerpo: { routine: rutina, exercise: ejercicio, ...config },
      }),
    onSuccess: () => invalidarRutina(cache, rutina),
  });
}

export function useGuardarEjercicio(rutina: number) {
  const cache = useQueryClient();

  return useMutation({
    mutationFn: ({ id, config }: { id: number; config: Partial<ConfigDeEjercicio> }) =>
      api<EjercicioDeRutina>(`/api/rutina-ejercicios/${id}/`, {
        metodo: "PATCH",
        cuerpo: config,
      }),
    onSuccess: () => invalidarRutina(cache, rutina),
  });
}

export function useQuitarEjercicio(rutina: number) {
  const cache = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => api<void>(`/api/rutina-ejercicios/${id}/`, { metodo: "DELETE" }),
    onSuccess: () => invalidarRutina(cache, rutina),
  });
}

export function useMoverEjercicio(rutina: number) {
  const cache = useQueryClient();

  return useMutation({
    mutationFn: ({ id, direccion }: { id: number; direccion: "subir" | "bajar" }) =>
      api<EjercicioDeRutina[]>(`/api/rutina-ejercicios/${id}/mover/`, {
        metodo: "POST",
        cuerpo: { direccion },
      }),
    onSuccess: () => invalidarRutina(cache, rutina),
  });
}

export function useBuscadorDeEjercicios(filtros: Record<string, string>, pagina = 1) {
  const params = new URLSearchParams({ mi_material: "1" });
  params.set("page", String(pagina));
  for (const [clave, valor] of Object.entries(filtros)) {
    if (valor) params.set(clave, valor);
  }

  return useQuery({
    queryKey: ["ejercicios", "buscador", filtros, pagina],
    queryFn: () => api<Paginado<Ejercicio>>(`/api/ejercicios/?${params}`),
    placeholderData: (anterior) => anterior,
  });
}
