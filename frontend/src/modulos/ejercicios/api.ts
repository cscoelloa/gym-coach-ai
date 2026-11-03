import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/api/cliente";
import type { Paginado } from "@/api/tipos";
import type { Opcion } from "@/ds/GrupoDeChips";

export type Musculo = { slug: string; name: string };

export type Ejercicio = {
  id: number;
  external_id: string;
  name: string;
  slug: string;
  body_part: string;
  body_part_label: string;
  equipment: string;
  equipment_label: string;
  target_muscle: Musculo | null;
  secondary_muscles: Musculo[];
  is_cardio: boolean;
  is_bodyweight: boolean;
  is_unilateral?: boolean;
  image: string | null;
  animation: string | null;
  attribution: string;
  steps: string[];
};

export type FiltrosDeCatalogo = {
  q: string;
  body_part: string;
  equipment: string;
  muscle: string;
};

export const SIN_FILTROS: FiltrosDeCatalogo = {
  q: "",
  body_part: "",
  equipment: "",
  muscle: "",
};

export type { Opcion } from "@/ds/GrupoDeChips";

export type Facetas = {
  total: number;
  body_part: Opcion[];
  equipment: Opcion[];
  muscle: Opcion[];
};

function consulta(filtros: Partial<FiltrosDeCatalogo>, extra: Record<string, string> = {}) {
  const params = new URLSearchParams();
  for (const [clave, valor] of Object.entries({ ...filtros, ...extra })) {
    if (valor) params.set(clave, valor);
  }
  const texto = params.toString();
  return texto ? `?${texto}` : "";
}

export function useEjercicios(filtros: FiltrosDeCatalogo, pagina = 1) {
  return useQuery({
    queryKey: ["ejercicios", filtros, pagina],
    queryFn: () =>
      api<Paginado<Ejercicio>>(
        `/api/ejercicios/${consulta(filtros, pagina > 1 ? { page: String(pagina) } : {})}`,
      ),
    placeholderData: (anterior) => anterior,
  });
}

export function useFacetas(filtros: FiltrosDeCatalogo) {
  return useQuery({
    queryKey: ["ejercicios", "facetas", filtros],
    queryFn: () => api<Facetas>(`/api/ejercicios/facetas/${consulta(filtros)}`),
    placeholderData: (anterior) => anterior,
  });
}

export type Taxonomia = {
  body_part: { valor: string; etiqueta: string }[];
  equipment: { valor: string; etiqueta: string }[];
};

export function useTaxonomia() {
  return useQuery({
    queryKey: ["ejercicios", "taxonomia"],
    queryFn: () => api<Taxonomia>("/api/ejercicios/taxonomia/"),
    staleTime: Infinity,
    gcTime: Infinity,
  });
}

export function useEjercicio(slug: string) {
  return useQuery({
    queryKey: ["ejercicios", "ficha", slug],
    queryFn: () => api<Ejercicio>(`/api/ejercicios/${slug}/`),
    staleTime: 5 * 60_000,
  });
}

export type EjercicioNuevo = {
  name: string;
  body_part: string;
  equipment: string;
  is_bodyweight: boolean;
  is_unilateral: boolean;
};

export function useCrearEjercicio() {
  const cache = useQueryClient();

  return useMutation({
    mutationFn: (datos: EjercicioNuevo) =>
      api<Ejercicio>("/api/ejercicios/", { metodo: "POST", cuerpo: datos }),
    onSuccess: () => cache.invalidateQueries({ queryKey: ["ejercicios"] }),
  });
}
