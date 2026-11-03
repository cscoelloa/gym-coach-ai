import { useId } from "react";

export function Stepper({
  etiqueta,
  valor,
  onCambio,
  paso = 1,
  minimo = 0,
  decimal = false,
  tamano = "md",
}: {
  etiqueta: string;
  valor: string;
  onCambio: (valor: string) => void;
  paso?: number;
  minimo?: number;
  decimal?: boolean;
  tamano?: "md" | "lg";
}) {
  const id = useId();

  function mover(direccion: 1 | -1) {
    const actual = Number.parseFloat(valor);
    const base = Number.isFinite(actual) ? actual : minimo;
    const siguiente = Math.max(minimo, base + direccion * paso);
    onCambio(decimal ? String(Number(siguiente.toFixed(2))) : String(Math.round(siguiente)));
  }

  return (
    <div>
      <span className="config-label" id={`${id}-etiqueta`}>
        {etiqueta}
      </span>
      <div className={`stepper ${tamano === "lg" ? "stepper-lg" : ""}`.trim()}>
        <button
          type="button"
          className="stepper-btn"
          onClick={() => mover(-1)}
          aria-label={`Bajar ${etiqueta}`}
        >
          −
        </button>
        <input
          id={id}
          className="stepper-input"
          type="number"
          inputMode={decimal ? "decimal" : "numeric"}
          step={decimal ? "any" : 1}
          min={minimo}
          value={valor}
          onChange={(evento) => onCambio(evento.target.value)}
          aria-labelledby={`${id}-etiqueta`}
        />
        <button
          type="button"
          className="stepper-btn"
          onClick={() => mover(1)}
          aria-label={`Subir ${etiqueta}`}
        >
          +
        </button>
      </div>
    </div>
  );
}

export function ConfirmarSerie({
  hecha = false,
  etiqueta,
  onClick,
  disabled,
}: {
  hecha?: boolean;
  etiqueta: string;
  onClick?: () => void;
  disabled?: boolean;
}) {
  return (
    <button
      type="button"
      className={`set-check ${hecha ? "set-check-done" : ""}`.trim()}
      aria-label={etiqueta}
      aria-pressed={hecha}
      onClick={onClick}
      disabled={disabled}
    >
      <svg
        className="size-5"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth={2}
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
      >
        <path d="m5 12 5 5L20 7" />
      </svg>
    </button>
  );
}
