import { useState } from "react";

import { Button } from "@/ds/Button";
import { Icono } from "@/ds/Icono";
import { useAvisos } from "@/lib/avisos";

const OFERTA_DESCARTADA = "gym-avisos-oferta";

function leerDescartada(): boolean {
  try {
    return localStorage.getItem(OFERTA_DESCARTADA) === "no";
  } catch {
    return false;
  }
}

export function OfertaDeAvisos() {
  const avisos = useAvisos();
  const [descartada, setDescartada] = useState(leerDescartada);

  if (descartada || avisos.estado !== "inactivo") return null;

  function descartar() {
    setDescartada(true);
    try {
      localStorage.setItem(OFERTA_DESCARTADA, "no");
    } catch {
    }
  }

  return (
    <div className="flex items-center gap-3 rounded-xl bg-primary-soft px-3 py-2">
      <Icono nombre="campana" className="size-5 shrink-0 text-primary" />
      <p className="body-sm min-w-0 flex-1 text-ink">
        {avisos.resultado === "actualizar"
          ? "Actualiza la aplicación para poder activar los avisos."
          : avisos.resultado === "error"
            ? "No se pudieron activar los avisos. Inténtalo más tarde."
            : "¿Te aviso cuando acabe el descanso, aunque cierres la aplicación?"}
      </p>
      <Button
        variante="primary"
        tamano="sm"
        disabled={avisos.ocupado}
        onClick={() => void avisos.activar()}
      >
        Activar
      </Button>
      <button type="button" className="icon-button size-9 text-ink-muted" onClick={descartar}>
        <Icono nombre="cerrar" className="size-4" />
        <span className="sr-only">Ahora no</span>
      </button>
    </div>
  );
}
