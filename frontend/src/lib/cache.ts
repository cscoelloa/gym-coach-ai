import { onlineManager, QueryClient } from "@tanstack/react-query";

import { ErrorDeApi } from "@/api/cliente";

export function crearCache({ reintentar = true }: { reintentar?: boolean } = {}) {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: (intentos, error) => {
          if (!reintentar) return false;
          if (error instanceof ErrorDeApi && error.estado >= 400 && error.estado < 500) {
            return false;
          }
          if (error instanceof ErrorDeApi && error.estado === 0 && !onlineManager.isOnline()) {
            return false;
          }
          return intentos < 2;
        },
        refetchOnWindowFocus: true,
        staleTime: 30_000,
      },
      mutations: {
        networkMode: "always",
        retry: false,
      },
    },
  });
}
