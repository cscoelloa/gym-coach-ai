import type { CSSProperties } from "react";

import { useDescanso } from "@/lib/descanso";

import { EnlaceDeDestino } from "./EnlaceDeDestino";
import { formatearCuenta } from "./RestTimer";

const CIRCUNFERENCIA = 50.27;

export function DescansoEnCurso() {
  const descanso = useDescanso();
  if (!descanso || descanso.sesionId === null) return null;

  const consumido =
    descanso.total > 0 ? Math.min(1, Math.max(0, 1 - descanso.restante / descanso.total)) : 1;
  const cuenta = formatearCuenta(descanso.restante);

  return (
    <EnlaceDeDestino a={`/entrenamientos/${descanso.sesionId}/`} className="rest-pill">
      <svg className="size-5 -rotate-90" viewBox="0 0 20 20" aria-hidden="true">
        <circle cx="10" cy="10" r="8" className="rest-pill-track" />
        <circle
          cx="10"
          cy="10"
          r="8"
          className="rest-pill-arc"
          strokeDasharray={CIRCUNFERENCIA}
          style={{ "--resto": CIRCUNFERENCIA * consumido } as CSSProperties}
        />
      </svg>
      <span className="num" aria-hidden="true">
        {cuenta}
      </span>
      <span className="sr-only">Descanso: quedan {cuenta}. Volver al entrenamiento</span>
    </EnlaceDeDestino>
  );
}
