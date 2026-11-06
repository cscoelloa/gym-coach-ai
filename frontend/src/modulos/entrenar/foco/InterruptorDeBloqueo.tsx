import { Icono } from "@/ds/Icono";

import type { Entreno } from "./useEntrenar";

export function InterruptorDeBloqueo({ bloqueo }: { bloqueo: Entreno["bloqueo"] }) {
  if (!bloqueo.disponible) return null;

  return (
    <button
      type="button"
      className={`icon-button ${bloqueo.activo ? "bg-primary-soft text-primary" : "bg-surface-200 text-ink"}`}
      aria-pressed={bloqueo.activo}
      onClick={bloqueo.cambiar}
    >
      <Icono nombre="candado" className="size-5" />
      <span className="sr-only">Mostrar el descanso en la pantalla de bloqueo</span>
    </button>
  );
}
