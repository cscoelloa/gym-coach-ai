import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/api/cliente";
import type { Paginado } from "@/api/tipos";

export type Proveedor = {
  id: number;
  provider: string;
  provider_label: string;
  model: string;
  effective_model: string;
  masked_api_key: string;
  has_usable_key: boolean;
  max_tokens: number;
  effort: string;
  timeout_seconds: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type Prompt = {
  id: number;
  key: string;
  key_label: string;
  name: string;
  system_prompt: string;
  user_template: string;
  version: number;
  is_active: boolean;
  available_variables: string[];
  created_at: string;
};

export type VistaPreviaDePrompt = {
  system: string;
  mensaje: string;
  variables: string[];
  desconocidas: string[];
};

export type Almacen = {
  id: number;
  name: string;
  description: string;
  openai_vector_store_id: string;
  is_ready: boolean;
  is_active: boolean;
  documentos: { total: number; indexados: number; fallidos: number };
  created_at: string;
};

export type Programacion = {
  id: number;
  goal: string;
  goal_label: string;
  sets_min: number;
  sets_max: number;
  reps_min: number;
  reps_max: number;
  rest_min_compound: number;
  rest_min_isolation: number;
  sets_min_per_muscle_day: number;
  resumen: string;
};

export type LimitesDeSubida = { extensiones: string[]; max_bytes: number };

export type Documento = {
  id: number;
  vector_store: number;
  almacen: string;
  title: string;
  file: string;
  status: "pending" | "indexing" | "indexed" | "failed";
  status_label: string;
  error: string;
  attributes: Record<string, unknown>;
  subido_por: string | null;
  created_at: string;
};

export type GeneracionEnLista = {
  id: number;
  usuario: string | null;
  kind: string;
  kind_label: string;
  provider: string;
  model: string;
  status: string;
  status_label: string;
  input_tokens: number;
  output_tokens: number;
  latency_ms: number;
  error: string;
  created_at: string;
};

export type GeneracionDetalle = GeneracionEnLista & {
  prompt_rendered: string;
  raw_response: string;
  parsed_output: unknown;
};

export type ResumenDeGeneraciones = {
  dias: number;
  total: number;
  errores: number;
  tokens: number;
  por_tipo: { tipo: string; etiqueta: string; total: number; errores: number }[];
};

export type UsuarioDeGestion = {
  id: number;
  username: string;
  email: string;
  first_name: string;
  is_active: boolean;
  is_staff: boolean;
  date_joined: string;
  last_login: string | null;
  entrenamientos: number;
  rutinas: number;
  generaciones: number;
  bloqueado: boolean;
};

export type MetricaDeGestion = {
  id: number;
  key: string;
  label: string;
  description: string;
  unit: string;
  category: string;
  category_label: string;
  chart: string;
  is_active: boolean;
  send_to_ai: boolean;
  default_visible: boolean;
  en_paneles: number;
};

export type Catalogo = {
  total: number;
  propios: number;
  con_imagen: number;
  musculos: number;
  por_zona: { valor: string; etiqueta: string; n: number }[];
  por_material: { valor: string; etiqueta: string; n: number }[];
};

export type ResumenDelPanel = {
  dias: number;
  proveedor: { nombre: string; modelo: string; clave_usable: boolean } | null;
  generaciones: { total: number; errores: number };
  documentos: { total: number; fallidos: number; pendientes: number };
  usuarios: { total: number; nuevos: number; bloqueados: number };
  metricas: { activas: number; total: number };
};

const BASE = "/api/gestion";

export function useResumenDelPanel() {
  return useQuery({
    queryKey: ["gestion", "resumen"],
    queryFn: () => api<ResumenDelPanel>(`${BASE}/resumen/`),
  });
}

export function useProveedores() {
  return useQuery({
    queryKey: ["gestion", "proveedores"],
    queryFn: () => api<Proveedor[]>(`${BASE}/proveedores/`),
  });
}

export function useGuardarProveedor() {
  const cache = useQueryClient();

  return useMutation({
    mutationFn: ({ id, ...datos }: Partial<Proveedor> & { api_key?: string; id?: number }) =>
      api<Proveedor>(id ? `${BASE}/proveedores/${id}/` : `${BASE}/proveedores/`, {
        metodo: id ? "PATCH" : "POST",
        cuerpo: datos,
      }),
    onSuccess: () => {
      cache.invalidateQueries({ queryKey: ["gestion"] });
    },
  });
}

export function useProbarProveedor() {
  const cache = useQueryClient();

  return useMutation({
    mutationFn: (id: number) =>
      api<{ ok: boolean; latencia_ms: number; tokens: number; modelo: string }>(
        `${BASE}/proveedores/${id}/probar/`,
        { metodo: "POST" },
      ),
    retry: false,
    onSettled: () => {
      cache.invalidateQueries({ queryKey: ["gestion", "generaciones"] });
      cache.invalidateQueries({ queryKey: ["gestion", "resumen"] });
    },
  });
}

export function usePrompts() {
  return useQuery({
    queryKey: ["gestion", "prompts"],
    queryFn: () => api<Prompt[]>(`${BASE}/prompts/`),
  });
}

export function useGuardarPrompt() {
  const cache = useQueryClient();

  return useMutation({
    mutationFn: ({ id, ...datos }: Partial<Prompt> & { id: number }) =>
      api<Prompt>(`${BASE}/prompts/${id}/`, { metodo: "PATCH", cuerpo: datos }),
    onSuccess: () => cache.invalidateQueries({ queryKey: ["gestion", "prompts"] }),
  });
}

export function useVistaPreviaDePrompt() {
  return useMutation({
    mutationFn: (id: number) =>
      api<VistaPreviaDePrompt>(`${BASE}/prompts/${id}/vista_previa/`, {
        metodo: "POST",
        cuerpo: {},
      }),
    retry: false,
  });
}

export function useAlmacenes() {
  return useQuery({
    queryKey: ["gestion", "almacenes"],
    queryFn: () => api<Almacen[]>(`${BASE}/almacenes/`),
  });
}

export function useDocumentos(filtros: { almacen?: number; estado?: string } = {}) {
  const parametros = new URLSearchParams();
  if (filtros.almacen) parametros.set("almacen", String(filtros.almacen));
  if (filtros.estado) parametros.set("estado", filtros.estado);
  const cola = parametros.toString();

  return useQuery({
    queryKey: ["gestion", "documentos", cola],
    queryFn: () => api<Documento[]>(`${BASE}/documentos/${cola ? `?${cola}` : ""}`),
    refetchInterval: (consulta) =>
      consulta.state.data?.some((documento) => documento.status === "indexing") ? 4000 : false,
  });
}

export function useReindexar() {
  const cache = useQueryClient();

  return useMutation({
    mutationFn: (id: number) =>
      api<Documento>(`${BASE}/documentos/${id}/reindexar/`, { metodo: "POST" }),
    retry: false,
    onSettled: () => cache.invalidateQueries({ queryKey: ["gestion"] }),
  });
}

export function useLimitesDeSubida() {
  return useQuery({
    queryKey: ["gestion", "documentos", "limites"],
    queryFn: () => api<LimitesDeSubida>(`${BASE}/documentos/limites/`),
    staleTime: Infinity,
  });
}

export function useProgramacion() {
  return useQuery({
    queryKey: ["gestion", "programacion"],
    queryFn: () => api<Programacion[]>(`${BASE}/programacion/`),
  });
}

export function useGuardarProgramacion() {
  const cache = useQueryClient();

  return useMutation({
    mutationFn: ({ id, ...datos }: Partial<Programacion> & { id: number }) =>
      api<Programacion>(`${BASE}/programacion/${id}/`, { metodo: "PATCH", cuerpo: datos }),
    retry: false,
    onSettled: () => cache.invalidateQueries({ queryKey: ["gestion"] }),
  });
}

export function useCrearAlmacen() {
  const cache = useQueryClient();

  return useMutation({
    mutationFn: (datos: { name: string; description: string }) =>
      api<Almacen>(`${BASE}/almacenes/`, { metodo: "POST", cuerpo: datos }),
    retry: false,
    onSettled: () => cache.invalidateQueries({ queryKey: ["gestion"] }),
  });
}

export function useCrearEnOpenAI() {
  const cache = useQueryClient();

  return useMutation({
    mutationFn: (id: number) =>
      api<{ openai_vector_store_id: string }>(`${BASE}/almacenes/${id}/crear_en_openai/`, {
        metodo: "POST",
      }),
    retry: false,
    onSettled: () => cache.invalidateQueries({ queryKey: ["gestion"] }),
  });
}

export function useSubirDocumento() {
  const cache = useQueryClient();

  return useMutation({
    mutationFn: ({
      almacen,
      titulo,
      archivo,
    }: {
      almacen: number;
      titulo: string;
      archivo: File;
    }) => {
      const cuerpo = new FormData();
      cuerpo.append("vector_store", String(almacen));
      cuerpo.append("title", titulo);
      cuerpo.append("file", archivo);
      return api<Documento>(`${BASE}/documentos/`, { metodo: "POST", cuerpo });
    },
    retry: false,
    onSettled: () => cache.invalidateQueries({ queryKey: ["gestion"] }),
  });
}

export function useBorrarDocumento() {
  const cache = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => api<void>(`${BASE}/documentos/${id}/`, { metodo: "DELETE" }),
    retry: false,
    onSettled: () => cache.invalidateQueries({ queryKey: ["gestion"] }),
  });
}

export function useGeneraciones(filtros: {
  tipo?: string;
  estado?: string;
  usuario?: string;
  page?: string;
}) {
  const parametros = new URLSearchParams();
  for (const [clave, valor] of Object.entries(filtros)) {
    if (valor) parametros.set(clave, valor);
  }
  const cola = parametros.toString();

  return useQuery({
    queryKey: ["gestion", "generaciones", cola],
    queryFn: () => api<Paginado<GeneracionEnLista>>(`${BASE}/generaciones/${cola ? `?${cola}` : ""}`),
    placeholderData: (anterior) => anterior,
  });
}

export function useGeneracion(id: number | null) {
  return useQuery({
    queryKey: ["gestion", "generacion", id],
    queryFn: () => api<GeneracionDetalle>(`${BASE}/generaciones/${id}/`),
    enabled: id !== null,
  });
}

export function useResumenDeGeneraciones() {
  return useQuery({
    queryKey: ["gestion", "generaciones", "resumen"],
    queryFn: () => api<ResumenDeGeneraciones>(`${BASE}/generaciones/resumen/`),
  });
}

export function useUsuariosDeGestion(buscar: string) {
  return useQuery({
    queryKey: ["gestion", "usuarios", buscar],
    queryFn: () =>
      api<UsuarioDeGestion[]>(
        `${BASE}/usuarios/${buscar ? `?buscar=${encodeURIComponent(buscar)}` : ""}`,
      ),
  });
}

export function useCambiarUsuario() {
  const cache = useQueryClient();

  return useMutation({
    mutationFn: ({ id, ...datos }: { id: number; is_active?: boolean; is_staff?: boolean }) =>
      api<UsuarioDeGestion>(`${BASE}/usuarios/${id}/`, { metodo: "PATCH", cuerpo: datos }),
    onSuccess: () => cache.invalidateQueries({ queryKey: ["gestion", "usuarios"] }),
  });
}

export function useDesbloquear() {
  const cache = useQueryClient();

  return useMutation({
    mutationFn: (id: number) =>
      api<{ desbloqueado: boolean; intentos_borrados: number }>(
        `${BASE}/usuarios/${id}/desbloquear/`,
        { metodo: "POST" },
      ),
    onSuccess: () => cache.invalidateQueries({ queryKey: ["gestion"] }),
  });
}

export function useMetricasDeGestion() {
  return useQuery({
    queryKey: ["gestion", "metricas"],
    queryFn: () => api<MetricaDeGestion[]>(`${BASE}/metricas/`),
  });
}

export function useCambiarMetrica() {
  const cache = useQueryClient();

  return useMutation({
    mutationFn: ({ id, ...datos }: { id: number } & Partial<MetricaDeGestion>) =>
      api<MetricaDeGestion>(`${BASE}/metricas/${id}/`, { metodo: "PATCH", cuerpo: datos }),
    onSuccess: () => {
      cache.invalidateQueries({ queryKey: ["gestion", "metricas"] });
      cache.invalidateQueries({ queryKey: ["metricas"] });
      cache.invalidateQueries({ queryKey: ["mis-metricas"] });
    },
  });
}

export function useCatalogoDeGestion() {
  return useQuery({
    queryKey: ["gestion", "catalogo"],
    queryFn: () => api<Catalogo>(`${BASE}/catalogo/`),
  });
}
