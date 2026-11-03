import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/api/cliente";
import { CLAVE_SESION } from "@/api/sesion";

export type Perfil = {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  goal: string;
  experience_level: string;
  sex: string;
  birth_date: string | null;
  height_cm: number | null;
  age: number | null;
  target_weight_kg: string | null;
  weekly_weight_change_target_kg: string | null;
  available_days_per_week: number;
  available_equipment: string[];
  injuries_notes: string;
};

export type Opcion = { valor: string; etiqueta: string };

export type OpcionesDePerfil = {
  goal: Opcion[];
  experience_level: Opcion[];
  sex: Opcion[];
  available_equipment: Opcion[];
};

export function usePerfil() {
  return useQuery({
    queryKey: ["perfil"],
    queryFn: () => api<Perfil>("/api/perfil/"),
  });
}

export function useOpcionesDePerfil() {
  return useQuery({
    queryKey: ["perfil", "opciones"],
    queryFn: () => api<OpcionesDePerfil>("/api/perfil/opciones/"),
    staleTime: Infinity,
    gcTime: Infinity,
  });
}

export function useGuardarPerfil() {
  const cache = useQueryClient();

  return useMutation({
    mutationFn: (datos: Partial<Perfil>) =>
      api<Perfil>("/api/perfil/", { metodo: "PATCH", cuerpo: datos }),
    onSuccess: (perfil) => {
      cache.setQueryData(["perfil"], perfil);
      cache.invalidateQueries({ queryKey: CLAVE_SESION });
      cache.invalidateQueries({ queryKey: ["ia", "generar"] });
      cache.invalidateQueries({ queryKey: ["inicio"] });
    },
  });
}

export function useBorrarCuenta() {
  return useMutation({
    mutationFn: (confirmacion: string) =>
      api<{ rutinas: number; entrenamientos: number; registros_de_peso: number }>("/api/cuenta/", {
        metodo: "DELETE",
        cuerpo: { confirmacion },
      }),
    retry: false,
  });
}
