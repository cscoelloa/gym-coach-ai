import { useEnLinea } from "@/lib/conexion";

import { Icono } from "./Icono";

export function AvisoDeConexion() {
  const enLinea = useEnLinea();

  return (
    <div role="status">
      {!enLinea && (
        <p className="flex items-center justify-center gap-2 bg-warning-soft px-4 py-1.5 text-center text-[13px]/[18px] font-medium text-warning">
          <Icono nombre="sinConexion" className="size-4 shrink-0" />
          Sin conexión. Ves lo último que cargaste; para guardar hace falta red.
        </p>
      )}
    </div>
  );
}
