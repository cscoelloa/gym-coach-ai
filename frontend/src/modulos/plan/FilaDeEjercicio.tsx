import type { ReactNode } from "react";

import { Icono } from "@/ds/Icono";
import type { Ejercicio } from "@/modulos/ejercicios/api";

export function FilaDeEjercicio({
  ejercicio,
  detalle,
  esquema,
  deshabilitada = false,
  onElegir,
}: {
  ejercicio: Ejercicio;
  detalle: ReactNode;
  esquema?: string;
  deshabilitada?: boolean;
  onElegir: () => void;
}) {
  return (
    <button
      className="compact-row"
      data-anadido={esquema ? "true" : "false"}
      disabled={deshabilitada}
      onClick={onElegir}
    >
      {ejercicio.image ? (
        <img src={ejercicio.image} className="ex-media" alt="" loading="lazy" />
      ) : (
        <span className="ex-glyph">
          <Icono nombre="entrenar" />
        </span>
      )}
      <span className="min-w-0 flex-1">
        <span className="ex-name block truncate">{ejercicio.name}</span>
        {detalle}
      </span>
      {esquema ? (
        <span className="flex shrink-0 items-center gap-1.5 text-primary">
          <span className="tag num">{esquema}</span>
          <Icono nombre="comprobado" className="size-5" />
        </span>
      ) : (
        <Icono nombre="mas" className="size-5 text-primary" />
      )}
    </button>
  );
}
