import type { ReactNode } from "react";

import { Icono, type NombreDeIcono } from "./Icono";

export type TonoDeStat = "primary" | "data" | "success" | "warning";

export function StatTile({
  etiqueta,
  valor,
  unidad,
  vacio,
  icono,
  tono = "primary",
  children,
}: {
  etiqueta: string;
  valor?: string | number | null;
  unidad?: string;
  vacio?: string;
  icono?: NombreDeIcono;
  tono?: TonoDeStat;
  children?: ReactNode;
}) {
  const sinDatos = valor === null || valor === undefined || valor === "";

  return (
    <div className="stat-tile">
      <span className="stat-tile-label">
        {icono && (
          <span className="stat-tile-icon" data-tono={tono} aria-hidden="true">
            <Icono nombre={icono} className="size-4" />
          </span>
        )}
        {etiqueta}
      </span>
      <span className="stat-tile-value">
        {sinDatos ? "—" : valor}
        {!sinDatos && unidad && <span className="stat-tile-unit">{unidad}</span>}
      </span>
      {sinDatos && vacio ? (
        <p className="empty-hint">{vacio}</p>
      ) : (
        children && <div className="stat-tile-foot">{children}</div>
      )}
    </div>
  );
}

export function NotaDeStat({ children }: { children: ReactNode }) {
  return <span className="stat-tile-note">{children}</span>;
}
