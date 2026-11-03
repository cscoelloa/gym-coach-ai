import type { ReactNode } from "react";

export type Segmento<T extends string> = {
  valor: T;
  etiqueta: string;
  icono?: ReactNode;
};

export function SegmentedControl<T extends string>({
  opciones,
  valor,
  onCambio,
  etiqueta,
  className = "",
}: {
  opciones: ReadonlyArray<Segmento<T>>;
  valor: T;
  onCambio: (valor: T) => void;
  etiqueta: string;
  className?: string;
}) {
  return (
    <div className={`segmented ${className}`.trim()} role="group" aria-label={etiqueta}>
      {opciones.map((opcion) => (
        <button
          key={opcion.valor}
          type="button"
          className={`segmented-option ${valor === opcion.valor ? "segmented-on" : ""}`.trim()}
          aria-pressed={valor === opcion.valor}
          onClick={() => onCambio(opcion.valor)}
        >
          {opcion.icono}
          {opcion.etiqueta}
        </button>
      ))}
    </div>
  );
}
