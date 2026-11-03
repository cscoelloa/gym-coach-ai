import { useQuery } from "@tanstack/react-query";

import { api } from "./cliente";

export type RegionDelMapa = {
  id: string;
  musculo: string | null;
  etiqueta: string;
  d: string;
};

export type VistaDelMapa = {
  nombre: "front" | "back";
  titulo: string;
  viewbox: string;
  regiones: RegionDelMapa[];
};

export type MapaCorporal = {
  vistas: VistaDelMapa[];
  musculos: string[];
};

export function useMapaCorporal() {
  return useQuery({
    queryKey: ["mapa-corporal"],
    queryFn: () => api<MapaCorporal>("/api/mapa-corporal/"),
    staleTime: Infinity,
    gcTime: Infinity,
  });
}
