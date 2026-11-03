import type { ReactNode } from "react";

export type EstadoDeSerie = "hecha" | "activa" | "pendiente";

const CLASE: Record<EstadoDeSerie, string> = {
  hecha: "set-row set-row-done",
  activa: "set-row set-row-active",
  pendiente: "set-row",
};

function Tic() {
  return (
    <svg
      className="size-4"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M20 6 9 17l-5-5" />
    </svg>
  );
}

export function SetRow({
  numero,
  peso,
  reps,
  estado = "pendiente",
  unidadPeso = "kg",
  children,
}: {
  numero: number;
  peso: string | number | null;
  reps: number | null;
  estado?: EstadoDeSerie;
  unidadPeso?: string;
  children?: ReactNode;
}) {
  return (
    <div className={CLASE[estado]}>
      <span className="set-row-index">{numero}</span>
      <div className="set-row-cell">
        <span className="set-row-num">{peso ?? "—"}</span>
        <span className="set-row-unit">{unidadPeso}</span>
      </div>
      <div className="set-row-cell">
        <span className="set-row-num">{reps ?? "—"}</span>
        <span className="set-row-unit">reps</span>
      </div>
      <span className="set-row-check">{estado === "hecha" && <Tic />}</span>
      {children && <div className="set-row-tags">{children}</div>}
    </div>
  );
}

export function CabeceraDeSeries() {
  return (
    <div className="set-row-head">
      <span>#</span>
      <span>Carga</span>
      <span>Reps</span>
      <span />
    </div>
  );
}
