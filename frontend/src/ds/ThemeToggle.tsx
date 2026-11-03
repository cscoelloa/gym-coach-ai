import { useTema, type PreferenciaDeTema } from "@/lib/tema";

import { Icono } from "./Icono";
import { SegmentedControl, type Segmento } from "./SegmentedControl";

const OPCIONES: ReadonlyArray<Segmento<PreferenciaDeTema>> = [
  { valor: "system", etiqueta: "Sistema", icono: <Icono nombre="sistema" className="size-4" /> },
  { valor: "light", etiqueta: "Claro", icono: <Icono nombre="sol" className="size-4" /> },
  { valor: "dark", etiqueta: "Oscuro", icono: <Icono nombre="luna" className="size-4" /> },
];

export function ThemeToggle({ className = "w-full" }: { className?: string }) {
  const { preferencia, cambiar } = useTema();

  return (
    <SegmentedControl
      opciones={OPCIONES}
      valor={preferencia}
      onCambio={cambiar}
      etiqueta="Tema de la interfaz"
      className={className}
    />
  );
}
