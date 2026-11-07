import { useEffect, useState } from "react";

import { SIN_FILTROS, type FiltrosDeCatalogo } from "@/modulos/ejercicios/api";

export function useBusquedaDeEjercicios() {
  const [filtros, setFiltros] = useState<FiltrosDeCatalogo>(SIN_FILTROS);
  const [texto, setTexto] = useState("");
  const [pagina, setPagina] = useState(1);
  const [abierta, setAbierta] = useState(false);

  useEffect(() => {
    if (texto === filtros.q) return;
    const espera = setTimeout(() => {
      setFiltros((previos) => ({ ...previos, q: texto }));
      setPagina(1);
    }, 300);
    return () => clearTimeout(espera);
  }, [texto, filtros.q]);

  function cambiar(cambios: Partial<FiltrosDeCatalogo>) {
    setFiltros((previos) => ({ ...previos, ...cambios }));
    setPagina(1);
  }

  function limpiar() {
    setTexto("");
    setFiltros(SIN_FILTROS);
    setPagina(1);
  }

  return { filtros, texto, pagina, abierta, setTexto, setPagina, setAbierta, cambiar, limpiar };
}

export type BusquedaDeEjercicios = ReturnType<typeof useBusquedaDeEjercicios>;
