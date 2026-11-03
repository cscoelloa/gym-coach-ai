import { Badge } from "@/ds/Badge";
import { SetRow } from "@/ds/SetRow";

import type { FilaDeSerie } from "../api";

export function Fila({
  fila,
  unilateral,
  onCorregir,
}: {
  fila: FilaDeSerie;
  unilateral: boolean;
  onCorregir: (fila: FilaDeSerie) => void;
}) {
  if (fila.serie_id === null) {
    return (
      <SetRow
        numero={fila.numero}
        peso={fila.peso || null}
        reps={fila.reps}
        estado={fila.activa ? "activa" : "pendiente"}
      />
    );
  }

  return (
    <button
      type="button"
      className="block w-full rounded-lg text-left active:opacity-70"
      onClick={() => onCorregir(fila)}
    >
      <span className="sr-only">Corregir la serie {fila.numero}: </span>
      <SetRow numero={fila.numero} peso={fila.peso || null} reps={fila.reps} estado="hecha">
        {unilateral && <Badge tono="neutral">por lado</Badge>}
      </SetRow>
    </button>
  );
}
