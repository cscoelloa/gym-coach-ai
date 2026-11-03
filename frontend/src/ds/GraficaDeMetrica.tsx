import { lazy, Suspense } from "react";

export type PuntoDeMetrica = {
  label: string;
  value: number;
};

const Lienzo = lazy(() =>
  import("./grafica/LienzoDeMetrica").then((modulo) => ({ default: modulo.LienzoDeMetrica })),
);

export function GraficaDeMetrica({
  serie,
  tipo,
  unidad,
}: {
  serie: PuntoDeMetrica[];
  tipo: "line" | "bar";
  unidad?: string;
}) {
  return (
    <Suspense fallback={<div className="chart-box" aria-busy="true" />}>
      <Lienzo serie={serie} tipo={tipo} unidad={unidad} />
    </Suspense>
  );
}
