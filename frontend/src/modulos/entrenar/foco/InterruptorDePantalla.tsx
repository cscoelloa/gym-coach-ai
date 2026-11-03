import { Icono } from "@/ds/Icono";
import { usePantallaEncendida } from "@/lib/pantallaEncendida";

export function InterruptorDePantalla() {
  const pantalla = usePantallaEncendida();
  if (!pantalla.disponible) return <span aria-hidden="true" />;

  return (
    <button
      type="button"
      className={`icon-button ${pantalla.activa ? "bg-primary-soft text-primary" : "bg-surface-200 text-ink-muted"}`}
      aria-pressed={pantalla.activa}
      onClick={pantalla.cambiar}
    >
      <Icono nombre="pantallaEncendida" className="size-5" />
      <span className="sr-only">Mantener la pantalla encendida</span>
    </button>
  );
}
