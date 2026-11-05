import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/api/cliente";
import type { Paginado } from "@/api/tipos";
import type { DescansoDelServidor } from "@/lib/descanso";

export type FilaDeSerie = {
  numero: number;
  serie_id: number | null;
  activa: boolean;
  peso: string;
  reps: number | null;
  rpe: number | null;
};

export type Foco = {
  sesion: {
    id: number;
    fecha: string;
    notas: string;
    terminada: boolean;
    rutina: { id: number; nombre: string } | null;
  };
  indice: number;
  total_ejercicios: number;
  planificados: { id: number; nombre: string; series: number; hechas: number }[];
  siguiente: number | null;
  actual: {
    id: number;
    ejercicio_id: number;
    nombre: string;
    slug: string;
    imagen: string | null;
    animacion: string | null;
    atribucion: string;
    series: number;
    reps_min: number;
    reps_max: number;
    descanso: number;
    unilateral: boolean;
    completo: boolean;
  } | null;
  filas: FilaDeSerie[];
  ultima_vez: { fecha: string; series: [string, number | null][]; por_lado: boolean } | null;
  mejor: string | null;
  sugerencia: string | null;
  avance: { hechas: number; objetivo: number };
  descanso_en_curso: DescansoDelServidor | null;
};

export type ResumenDeCierre = {
  sesion: { id: number; fecha: string; rutina: string | null; notas: string };
  duracion_minutos: number | null;
  series: number;
  ejercicios: number;
  tonelaje_kg: number;
  series_sin_cobertura: number;
  records: { ejercicio: string; kg: string }[];
  musculos: string[];
};

export type SesionEnHistorial = {
  id: number;
  date: string;
  routine: number | null;
  routine_name: string | null;
  started_at: string | null;
  finished_at: string | null;
  notes: string;
  set_count: number;
  duracion_minutos: number | null;
  tonelaje_kg: number;
};

export function useFoco(sesion: number, indice: number | null) {
  return useQuery({
    queryKey: ["entrenar", sesion, indice ?? "retomar"],
    queryFn: () =>
      api<Foco>(
        `/api/entrenamientos/${sesion}/foco/${indice === null ? "" : `?ejercicio=${indice}`}`,
      ),
    enabled: Number.isFinite(sesion),
    staleTime: 0,
  });
}

export function useResumenDeCierre(sesion: number) {
  return useQuery({
    queryKey: ["entrenar", sesion, "resumen"],
    queryFn: () => api<ResumenDeCierre>(`/api/entrenamientos/${sesion}/resumen/`),
    enabled: Number.isFinite(sesion),
  });
}

export function useHistorial(pagina = 1) {
  return useQuery({
    queryKey: ["entrenamientos", pagina],
    queryFn: () =>
      api<Paginado<SesionEnHistorial>>(
        `/api/entrenamientos/${pagina > 1 ? `?page=${pagina}` : ""}`,
      ),
  });
}

function invalidarSesion(cache: ReturnType<typeof useQueryClient>, sesion: number) {
  cache.invalidateQueries({ queryKey: ["entrenar", sesion] });
  cache.invalidateQueries({ queryKey: ["entrenamientos"] });
  cache.invalidateQueries({ queryKey: ["inicio"] });
}

export function useEmpezar() {
  const cache = useQueryClient();

  return useMutation({
    mutationFn: (rutina?: number) =>
      api<{ id: number }>("/api/entrenamientos/", {
        metodo: "POST",
        cuerpo: rutina ? { routine: rutina } : {},
      }),
    onSuccess: () => {
      cache.invalidateQueries({ queryKey: ["entrenamientos"] });
      cache.invalidateQueries({ queryKey: ["inicio"] });
    },
  });
}

export type SerieNueva = {
  session: number;
  exercise: number;
  weight_kg?: string;
  reps?: number;
  rpe?: number;
};

export type SerieRegistrada = { id: number; descanso: DescansoDelServidor | null };

export function useRegistrarSerie(sesion: number) {
  const cache = useQueryClient();

  return useMutation({
    mutationFn: (datos: SerieNueva) =>
      api<SerieRegistrada>("/api/series/", { metodo: "POST", cuerpo: datos }),
    onSuccess: () => invalidarSesion(cache, sesion),
  });
}

export function useCorregirSerie(sesion: number) {
  const cache = useQueryClient();

  return useMutation({
    mutationFn: ({ id, weight_kg, reps }: { id: number; weight_kg: string | null; reps: number | null }) =>
      api(`/api/series/${id}/`, { metodo: "PATCH", cuerpo: { weight_kg, reps } }),
    onSuccess: () => invalidarSesion(cache, sesion),
  });
}

export function useBorrarSerie(sesion: number) {
  const cache = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => api<void>(`/api/series/${id}/`, { metodo: "DELETE" }),
    onSuccess: () => invalidarSesion(cache, sesion),
  });
}

export function useAccionDeDescanso(sesion: number) {
  const cache = useQueryClient();

  return useMutation({
    mutationFn: (accion: "alargar" | "saltar") =>
      api<{ descanso: DescansoDelServidor | null }>(
        `/api/entrenamientos/${sesion}/descanso/`,
        { metodo: "POST", cuerpo: { accion } },
      ),
    onSuccess: ({ descanso }) => {
      cache.setQueriesData<Foco>({ queryKey: ["entrenar", sesion] }, (previo) =>
        previo && "descanso_en_curso" in previo
          ? { ...previo, descanso_en_curso: descanso }
          : previo,
      );
    },
  });
}

export function useFinalizar(sesion: number) {
  const cache = useQueryClient();

  return useMutation({
    mutationFn: () =>
      api<ResumenDeCierre>(`/api/entrenamientos/${sesion}/finalizar/`, { metodo: "POST" }),
    onSuccess: () => invalidarSesion(cache, sesion),
  });
}

export function useGuardarNotas(sesion: number) {
  const cache = useQueryClient();

  return useMutation({
    mutationFn: (notes: string) =>
      api(`/api/entrenamientos/${sesion}/`, { metodo: "PATCH", cuerpo: { notes } }),
    onSuccess: () => invalidarSesion(cache, sesion),
  });
}

export function useEjerciciosRecientes() {
  return useQuery({
    queryKey: ["entrenar", "recientes"],
    queryFn: () =>
      api<{ id: number; nombre: string }[]>("/api/entrenamientos/ejercicios_recientes/"),
    staleTime: 5 * 60_000,
  });
}
