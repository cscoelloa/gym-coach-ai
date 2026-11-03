import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/api/cliente";
import type { Paginado } from "@/api/tipos";
import type { SerieDePeso } from "@/ds/GraficaDePeso";

export type RegistroDePeso = {
  id: number;
  date: string;
  weight_kg: string;
  body_fat_pct: string | null;
  notes: string;
  created_at: string;
};

export type ResumenDePeso = {
  ultimo: RegistroDePeso | null;
  cambio: number | null;
  objetivo: string;
  meta_kg: number | null;
  serie: SerieDePeso | null;
};

const CLAVE = ["peso"] as const;

export function useResumenDePeso() {
  return useQuery({
    queryKey: [...CLAVE, "resumen"],
    queryFn: () => api<ResumenDePeso>("/api/peso/resumen/"),
  });
}

export function useRegistrosDePeso(pagina = 1) {
  return useQuery({
    queryKey: [...CLAVE, "lista", pagina],
    queryFn: () =>
      api<Paginado<RegistroDePeso>>(`/api/peso/${pagina > 1 ? `?page=${pagina}` : ""}`),
    placeholderData: (anterior) => anterior,
  });
}

export type PesoAGuardar = {
  date: string;
  weight_kg: string;
  body_fat_pct?: string;
  notes?: string;
};

export function useGuardarPeso() {
  const cache = useQueryClient();

  return useMutation({
    mutationFn: ({ datos, existente }: { datos: PesoAGuardar; existente?: number }) =>
      existente
        ? api<RegistroDePeso>(`/api/peso/${existente}/`, { metodo: "PATCH", cuerpo: datos })
        : api<RegistroDePeso>("/api/peso/", { metodo: "POST", cuerpo: datos }),
    onSuccess: () => {
      cache.invalidateQueries({ queryKey: CLAVE });
      cache.invalidateQueries({ queryKey: ["inicio"] });
    },
  });
}

export function useBorrarPeso() {
  const cache = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => api<void>(`/api/peso/${id}/`, { metodo: "DELETE" }),
    onSuccess: () => {
      cache.invalidateQueries({ queryKey: CLAVE });
      cache.invalidateQueries({ queryKey: ["inicio"] });
    },
  });
}
