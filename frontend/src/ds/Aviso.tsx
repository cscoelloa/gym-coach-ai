import type { ReactNode } from "react";

import { Icono, type NombreDeIcono } from "./Icono";

export type TonoDeAviso = "error" | "aviso" | "exito" | "informacion";

const ICONO: Record<TonoDeAviso, NombreDeIcono> = {
  error: "error",
  aviso: "aviso",
  exito: "comprobado",
  informacion: "informacion",
};

const TONO: Record<TonoDeAviso, { fondo: string; icono: string }> = {
  error: { fondo: "bg-danger-soft", icono: "text-danger" },
  aviso: { fondo: "bg-warning-soft", icono: "text-warning" },
  exito: { fondo: "bg-success-soft", icono: "text-success" },
  informacion: { fondo: "bg-data-soft", icono: "text-data" },
};

export function Aviso({
  tono = "informacion",
  urgente = false,
  children,
}: {
  tono?: TonoDeAviso;
  urgente?: boolean;
  children: ReactNode;
}) {
  return (
    <p
      role={urgente ? "alert" : "status"}
      className={`body-sm mt-4 flex items-start gap-2.5 rounded-xl px-3.5 py-3 text-ink ${TONO[tono].fondo}`}
    >
      <Icono nombre={ICONO[tono]} className={`mt-0.5 size-[18px] shrink-0 ${TONO[tono].icono}`} />
      <span className="min-w-0">{children}</span>
    </p>
  );
}
