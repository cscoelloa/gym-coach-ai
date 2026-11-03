import { Stepper } from "./Stepper";

export type ConfigDeEjercicio = {
  target_sets: number;
  target_reps_min: number;
  target_reps_max: number;
  rest_seconds: number;
};

export type ConfigEnTexto = Record<keyof ConfigDeEjercicio, string>;

export function aNumeros(config: ConfigEnTexto): ConfigDeEjercicio {
  const entero = (valor: string, respaldo: number, minimo: number, maximo: number) => {
    const n = Number.parseInt(valor, 10);
    if (!Number.isFinite(n)) return respaldo;
    return Math.max(minimo, Math.min(n, maximo));
  };

  return {
    target_sets: entero(config.target_sets, 3, 1, 20),
    target_reps_min: entero(config.target_reps_min, 8, 1, 100),
    target_reps_max: entero(config.target_reps_max, 12, 1, 100),
    rest_seconds: entero(config.rest_seconds, 90, 0, 900),
  };
}

export function ConfigDeSeries({
  valores,
  onCambio,
}: {
  valores: ConfigEnTexto;
  onCambio: (valores: ConfigEnTexto) => void;
}) {
  const cambiar = (campo: keyof ConfigEnTexto) => (valor: string) =>
    onCambio({ ...valores, [campo]: valor });

  return (
    <div className="@container">
      <div className="grid grid-cols-2 gap-3 @lg:grid-cols-3">
        <Stepper
          etiqueta="Series"
          valor={valores.target_sets}
          onCambio={cambiar("target_sets")}
          minimo={1}
        />

        <div>
          <span className="config-label">Repeticiones</span>
          <div className="stepper justify-center gap-1 px-2">
            <input
              className="reps-input"
              type="number"
              min={1}
              max={100}
              inputMode="numeric"
              aria-label="Repeticiones mínimas"
              value={valores.target_reps_min}
              onChange={(evento) => cambiar("target_reps_min")(evento.target.value)}
            />
            <span className="select-none text-ink-muted" aria-hidden="true">
              –
            </span>
            <input
              className="reps-input"
              type="number"
              min={1}
              max={100}
              inputMode="numeric"
              aria-label="Repeticiones máximas"
              value={valores.target_reps_max}
              onChange={(evento) => cambiar("target_reps_max")(evento.target.value)}
            />
          </div>
        </div>

        <div className="col-span-2 @lg:col-span-1">
          <Stepper
            etiqueta="Descanso (s)"
            valor={valores.rest_seconds}
            onCambio={cambiar("rest_seconds")}
            paso={15}
            minimo={0}
          />
        </div>
      </div>
    </div>
  );
}
