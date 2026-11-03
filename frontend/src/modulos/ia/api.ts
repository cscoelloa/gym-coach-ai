import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api, ErrorDeApi } from "@/api/cliente";

export type MetadatosDeGeneracion = {
  id: number;
  fecha: string;
  proveedor: string;
  modelo: string;
  latencia_ms: number;
  tokens_entrada: number;
  tokens_salida: number;
};

export type EjercicioPropuesto = {
  external_id: string;
  nombre: string;
  slug: string | null;
  imagen: string | null;
  en_catalogo: boolean;
  series: number;
  reps_min: number;
  reps_max: number;
  descanso: number;
};

export type Propuesta = {
  generacion: MetadatosDeGeneracion;
  nombre: string;
  descripcion: string;
  motivo: string;
  rutinas: { nombre: string; ejercicios: EjercicioPropuesto[] }[];
  semana: { weekday: number; etiqueta: string; rutina: string | null }[];
  ya_aplicada: boolean;
};

export type MusculoElegible = { valor: string; etiqueta: string; n: number };

export type DiaDelReparto = {
  weekday: number;
  muscles: string[];
  emphasis: string | null;
  exercises: number;
};

export type ObjetivoDeEntreno = { valor: string; etiqueta: string; resumen: string };

export type FormularioDeGeneracion = {
  restantes: number;
  dias_por_defecto: number;
  tiene_equipamiento: boolean;
  musculos: MusculoElegible[];
  dias_sugeridos: number[];
  ejercicios: { min: number; max: number; por_defecto: number };
  max_musculos_por_dia: number;
  objetivos: ObjetivoDeEntreno[];
  objetivo_por_defecto: string;
};

export type Analisis = {
  summary: string;
  patterns: string[];
  stalled: { exercise: string; weeks_stalled: number; likely_cause: string }[];
  recommendations: string[];
  proposed_changes: { target: string; change: string; reason: string }[];
  data_caveats: string[];
};

export type EstadoDelAnalisis = {
  restantes: number;
  sesiones: number;
  sesiones_necesarias: number;
  generacion: MetadatosDeGeneracion | null;
  analisis: Analisis | null;
};

export type CodigoDeErrorDeIa =
  | "cuota"
  | "proveedor"
  | "sin_candidatos"
  | "sin_datos"
  | "no_aplicable"
  | "parametros"
  | "reparto"
  | "descanso";

export function codigoDe(error: unknown): CodigoDeErrorDeIa | null {
  return error instanceof ErrorDeApi ? (error.codigo as CodigoDeErrorDeIa | null) : null;
}

export function useFormularioDeGeneracion() {
  return useQuery({
    queryKey: ["ia", "generar"],
    queryFn: () => api<FormularioDeGeneracion>("/api/ia/generar/"),
  });
}

export function useGenerar() {
  const cache = useQueryClient();

  return useMutation({
    mutationFn: (datos: { notes: string; split: DiaDelReparto[]; training_goal: string }) =>
      api<Propuesta>("/api/ia/generar/", { metodo: "POST", cuerpo: datos }),
    retry: false,
    onSettled: () => {
      cache.invalidateQueries({ queryKey: ["ia", "generar"] });
    },
  });
}

export function usePropuesta(id: number) {
  return useQuery({
    queryKey: ["ia", "propuesta", id],
    queryFn: () => api<Propuesta>(`/api/ia/propuestas/${id}/`),
    enabled: Number.isFinite(id),
  });
}

export function useAceptar(id: number) {
  const cache = useQueryClient();

  return useMutation({
    mutationFn: () =>
      api<{ programa: { id: number; nombre: string } }>(
        `/api/ia/propuestas/${id}/aceptar/`,
        { metodo: "POST" },
      ),
    retry: false,
    onSuccess: () => {
      cache.invalidateQueries({ queryKey: ["plan"] });
      cache.invalidateQueries({ queryKey: ["inicio"] });
      cache.invalidateQueries({ queryKey: ["ia", "propuesta", id] });
    },
  });
}

export function useDescartar(id: number) {
  return useMutation({
    mutationFn: () => api<void>(`/api/ia/propuestas/${id}/descartar/`, { metodo: "POST" }),
    retry: false,
  });
}

export function useAnalisis() {
  return useQuery({
    queryKey: ["ia", "analisis"],
    queryFn: () => api<EstadoDelAnalisis>("/api/ia/analisis/"),
  });
}

export function usePedirAnalisis() {
  const cache = useQueryClient();

  return useMutation({
    mutationFn: () =>
      api<EstadoDelAnalisis>("/api/ia/analisis/", { metodo: "POST" }),
    retry: false,
    onSuccess: (datos) => {
      cache.setQueryData(["ia", "analisis"], datos);
      cache.invalidateQueries({ queryKey: ["notificaciones"] });
    },
  });
}
