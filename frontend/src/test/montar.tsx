import { QueryClientProvider } from "@tanstack/react-query";
import { render } from "@testing-library/react";
import type { ReactElement, ReactNode } from "react";
import { createMemoryRouter, RouterProvider } from "react-router";
import { crearCache } from "@/lib/cache";
import { CambiosPendientes } from "@/lib/cambiosPendientes";

export function montar(
  elemento: ReactElement,
  { ruta = "/" }: { ruta?: string } = {},
) {
  const cache = crearCache({ reintentar: false });

  const router = createMemoryRouter([{ path: "*", element: <CambiosPendientes>{elemento}</CambiosPendientes> }], { initialEntries: [ruta] });

  function Envoltorio({ children: _children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={cache}>
        <RouterProvider router={router} />
      </QueryClientProvider>
    );
  }

  return render(elemento, { wrapper: Envoltorio });
}
