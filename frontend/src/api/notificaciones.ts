import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "./cliente";
import type { Paginado } from "./tipos";

export type Notificacion = {
  id: number;
  kind: "stall_detected" | "weight_off_track" | "progress_ready" | "routine_ready";
  kind_label: string;
  severity: "info" | "warning";
  title: string;
  body: string;
  payload: Record<string, unknown>;
  is_read: boolean;
  emailed_at: string | null;
  created_at: string;
};

const CLAVE = ["notificaciones"] as const;

export function useNotificaciones(pagina = 1, soloSinLeer = false) {
  return useQuery({
    queryKey: [...CLAVE, "lista", pagina, soloSinLeer],
    queryFn: () =>
      api<Paginado<Notificacion>>(
        `/api/notificaciones/?page=${pagina}${soloSinLeer ? "&unread=true" : ""}`,
      ),
  });
}

export function useSinLeer() {
  return useQuery({
    queryKey: [...CLAVE, "sin-leer"],
    queryFn: async () => {
      const pagina = await api<Paginado<Notificacion>>("/api/notificaciones/?unread=true");
      return pagina.count;
    },
    staleTime: 60_000,
  });
}

export function useMarcarLeida() {
  const cache = useQueryClient();

  return useMutation({
    mutationFn: (id: number) =>
      api<Notificacion>(`/api/notificaciones/${id}/`, {
        metodo: "PATCH",
        cuerpo: { is_read: true },
      }),
    onSuccess: () => cache.invalidateQueries({ queryKey: CLAVE }),
  });
}

export function useMarcarTodasLeidas() {
  const cache = useQueryClient();

  return useMutation({
    mutationFn: () =>
      api<{ updated: number }>("/api/notificaciones/read_all/", { metodo: "POST" }),
    onSuccess: () => cache.invalidateQueries({ queryKey: CLAVE }),
  });
}
