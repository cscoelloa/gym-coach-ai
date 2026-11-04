import { useLocation, useNavigate } from "react-router";

import { padreDe } from "./navegacion";

export function useVolver() {
  const { pathname, key } = useLocation();
  const navegar = useNavigate();
  const padre = padreDe(pathname);
  const conHistorial = key !== "default";

  return {
    etiqueta: conHistorial ? "Atrás" : padre.etiqueta,
    volver: () => (conHistorial ? navegar(-1) : navegar(padre.url, { replace: true })),
  };
}
