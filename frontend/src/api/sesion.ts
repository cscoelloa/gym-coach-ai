import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { olvidarEsteDispositivo } from "@/lib/avisos";
import { borrarCachesDeLaApp } from "@/lib/pwa";

import { api, ErrorDeApi } from "./cliente";

export type UsuarioDeSesion = {
  id: number;
  username: string;
  first_name: string;
  is_staff: boolean;
};

export const CLAVE_SESION = ["sesion"] as const;

export function useSesion() {
  return useQuery({
    queryKey: CLAVE_SESION,
    queryFn: async (): Promise<UsuarioDeSesion | null> => {
      try {
        return await api<UsuarioDeSesion>("/api/auth/session/");
      } catch (error) {
        if (error instanceof ErrorDeApi && error.esSinSesion) return null;
        throw error;
      }
    },
    retry: false,
    networkMode: "always",
    staleTime: Infinity,
  });
}

type Credenciales = { username: string; password: string; next?: string };
type Entrada = { usuario: UsuarioDeSesion; redirect: string };

export function useEntrar() {
  const cache = useQueryClient();

  return useMutation({
    mutationFn: (credenciales: Credenciales) =>
      api<Entrada>("/api/auth/session/", { metodo: "POST", cuerpo: credenciales }),
    onSuccess: (datos) => cache.setQueryData(CLAVE_SESION, datos.usuario),
  });
}

type Registro = {
  username: string;
  email: string;
  password: string;
  password2: string;
};

export function useRegistrarse() {
  const cache = useQueryClient();

  return useMutation({
    mutationFn: (datos: Registro) =>
      api<Entrada>("/api/auth/registro/", { metodo: "POST", cuerpo: datos }),
    onSuccess: (datos) => cache.setQueryData(CLAVE_SESION, datos.usuario),
  });
}

export function useSalir() {
  const cache = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      await olvidarEsteDispositivo();
      await api<void>("/api/auth/session/", { metodo: "DELETE" });
    },
    onSuccess: () => {
      cache.clear();
      void borrarCachesDeLaApp();
    },
  });
}
