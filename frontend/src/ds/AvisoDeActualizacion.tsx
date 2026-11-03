import { useConfirmarSalida } from "@/lib/cambiosPendientes";
import { aplicarActualizacion, useActualizacion } from "@/lib/pwa";

import { Button } from "./Button";
import { Icono } from "./Icono";

export function AvisoDeActualizacion() {
  const { disponible } = useActualizacion();
  const guardia = useConfirmarSalida();

  if (!disponible) return null;

  return (
    <div className="toast" role="status">
      <span className="flex size-9 shrink-0 items-center justify-center rounded-full bg-primary-soft text-primary">
        <Icono nombre="recargar" className="size-5" />
      </span>
      <p className="min-w-0 flex-1 text-[15px]/[20px]">
        <span className="font-semibold">Hay una versión nueva.</span>{" "}
        <span className="text-ink-muted">Se aplica al recargar.</span>
      </p>
      <Button
        tamano="sm"
        variante="primary"
        onClick={async () => {
          if (await guardia.confirmar()) aplicarActualizacion();
        }}
      >
        Actualizar
      </Button>
    </div>
  );
}
