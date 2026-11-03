import { Card } from "@/ds/Card";
import { CabeceraDeSeries } from "@/ds/SetRow";

import type { FilaDeSerie } from "../api";
import { Fila } from "./Fila";

export function SeriesDelEjercicio({
  filas,
  unilateral,
  onCorregir,
}: {
  filas: FilaDeSerie[];
  unilateral: boolean;
  onCorregir: (fila: FilaDeSerie) => void;
}) {
  return (
    <Card className="focus-area-series p-2.5 sm:p-3">
      <CabeceraDeSeries />
      <div className="space-y-1.5">
        {filas.map((fila) => (
          <Fila key={fila.numero} fila={fila} unilateral={unilateral} onCorregir={onCorregir} />
        ))}
      </div>
    </Card>
  );
}
