import { useEffect, useRef } from "react";

import { Icono } from "@/ds/Icono";

import type { Foco } from "../api";

export function ChipsDeEjercicios({
  datos,
  onElegir,
}: {
  datos: Foco;
  onElegir: (indice: number) => void;
}) {
  const actual = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    actual.current?.scrollIntoView?.({ inline: "center", block: "nearest", behavior: "smooth" });
  }, [datos.indice]);

  return (
    <nav className="focus-area-chips focus-chips" aria-label="Ejercicios de la rutina">
      {datos.planificados.map((item, posicion) => {
        const esActual = posicion + 1 === datos.indice;
        const hecho = item.series > 0 && item.hechas >= item.series;
        return (
          <button
            key={item.id}
            ref={esActual ? actual : undefined}
            type="button"
            className="focus-chip"
            data-hecho={hecho ? "true" : "false"}
            {...(esActual ? { "aria-current": "step" as const } : {})}
            onClick={() => onElegir(posicion + 1)}
          >
            {hecho ? (
              <Icono nombre="comprobado" className="size-4 shrink-0" />
            ) : (
              <span className="num shrink-0 opacity-70">{posicion + 1}</span>
            )}
            <span className="max-w-[10rem] truncate capitalize">{item.nombre}</span>
            <span className="num shrink-0 opacity-70">
              {item.hechas}/{item.series}
            </span>
          </button>
        );
      })}
    </nav>
  );
}
