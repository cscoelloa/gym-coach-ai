import { useEffect, useRef } from "react";

import { HeatCell } from "./WeekStrip";

export type DiaDelCalendario = {
  fecha: string;
  nivel: number;
  minutos: number;
  sesiones: number;
};

export type SemanaDelCalendario = {
  etiqueta: string;
  dias: (DiaDelCalendario | null)[];
};

const FECHA = new Intl.DateTimeFormat("es-ES", { day: "numeric", month: "short", year: "numeric" });

function comoFecha(iso: string): Date {
  const [anio, mes, dia] = iso.split("-").map(Number);
  return new Date(anio!, mes! - 1, dia!);
}

function resumen(dia: { fecha: string; sesiones: number; minutos: number }): string {
  const cuando = FECHA.format(comoFecha(dia.fecha));
  if (!dia.sesiones) return `${cuando}: sin entrenar`;
  const cuantos = `${dia.sesiones} entrenamiento${dia.sesiones === 1 ? "" : "s"}`;
  return dia.minutos ? `${cuando}: ${cuantos}, ${dia.minutos} min` : `${cuando}: ${cuantos}`;
}

export function CalendarioDeActividad({
  semanas,
  niveles,
}: {
  semanas: SemanaDelCalendario[];
  niveles: number[];
}) {
  const caja = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const nodo = caja.current;
    if (nodo) nodo.scrollLeft = nodo.scrollWidth;
  }, [semanas.length]);

  return (
    <div className="cal-scroll" ref={caja}>
      <div className="inline-block min-w-full">
        <div className="mb-1 flex h-3.5 gap-0.5 text-[0.625rem] text-ink-muted" aria-hidden="true">
          {semanas.map((semana, indice) => (
            <span className="relative w-2.5 shrink-0 sm:w-3" key={indice}>
              {semana.etiqueta && (
                <span className="absolute left-0 top-0 whitespace-nowrap">{semana.etiqueta}</span>
              )}
            </span>
          ))}
        </div>

        <div className="flex gap-0.5">
          {semanas.map((semana, indice) => (
            <div className="flex flex-col gap-0.5" key={indice}>
              {semana.dias.map((dia, posicion) =>
                dia ? (
                  <HeatCell
                    key={dia.fecha}
                    nivel={dia.nivel as 0 | 1 | 2 | 3 | 4}
                    titulo={resumen(dia)}
                  />
                ) : (
                  <span className="heat-cell opacity-0" key={`hueco-${posicion}`} />
                ),
              )}
            </div>
          ))}
        </div>

        <div className="mt-2 flex items-center justify-end gap-1 text-[0.625rem] text-ink-muted">
          <span>Menos tiempo</span>
          {niveles.map((nivel) => (
            <HeatCell key={nivel} nivel={nivel as 0 | 1 | 2 | 3 | 4} />
          ))}
          <span>Más tiempo</span>
        </div>
      </div>
    </div>
  );
}
