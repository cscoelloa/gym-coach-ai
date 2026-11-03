import { lazy, Suspense } from "react";

export type SerieDePeso = {
  labels: string[];
  values: number[];
  goal: number | null;
};

const Lienzo = lazy(() =>
  import("./grafica/Lienzo").then((modulo) => ({ default: modulo.Lienzo })),
);

export function GraficaDePeso({ serie, unidad = "kg" }: { serie: SerieDePeso; unidad?: string }) {
  return (
    <Suspense fallback={<div className="chart-box" aria-busy="true" />}>
      <Lienzo serie={serie} unidad={unidad} />
    </Suspense>
  );
}
