import { Aviso } from "@/ds/Aviso";
import { Button } from "@/ds/Button";
import type { ConfigDeEjercicio } from "@/ds/ConfigDeSeries";
import type { Ejercicio } from "@/modulos/ejercicios/api";

import { useRutinasConEjercicios } from "./api";
import { FilaDeEjercicio } from "./FilaDeEjercicio";

export function DeMisRutinas({
  excluir,
  q,
  anadidos,
  onElegir,
}: {
  excluir?: number;
  q: string;
  anadidos: Map<number, string>;
  onElegir: (ejercicio: Ejercicio, config: ConfigDeEjercicio) => void;
}) {
  const rutinas = useRutinasConEjercicios(excluir, q);

  if (rutinas.isPending) {
    return (
      <p role="status" className="body-sm py-6 text-center text-ink-muted">
        Buscando en tus rutinas…
      </p>
    );
  }

  if (rutinas.error) {
    return (
      <Aviso tono="error">
        No se pudieron cargar tus rutinas.{" "}
        <Button tamano="sm" onClick={() => void rutinas.refetch()}>
          Reintentar
        </Button>
      </Aviso>
    );
  }

  if (!rutinas.data.length) {
    return (
      <p className="body-sm py-6 text-center text-ink-muted">
        Ningún ejercicio de tus rutinas coincide con la búsqueda.
      </p>
    );
  }

  return (
    <div className="space-y-5" aria-busy={rutinas.isFetching}>
      {rutinas.data.map((rutina) => (
        <section key={rutina.id} aria-labelledby={`de-rutina-${rutina.id}`}>
          <h3 id={`de-rutina-${rutina.id}`} className="section-kicker mb-2 px-1">
            {rutina.name} · {rutina.exercises.length}
          </h3>
          <div className="compact-list">
            {rutina.exercises.map((fila) => (
              <FilaDeEjercicio
                key={fila.id}
                ejercicio={fila.exercise_detail}
                detalle={
                  <span className="caption num text-ink-muted">
                    {fila.target_sets} × {fila.target_reps_min}–{fila.target_reps_max} ·{" "}
                    {fila.rest_seconds} s
                  </span>
                }
                esquema={anadidos.get(fila.exercise)}
                deshabilitada={rutinas.isPlaceholderData}
                onElegir={() =>
                  onElegir(fila.exercise_detail, {
                    target_sets: fila.target_sets,
                    target_reps_min: fila.target_reps_min,
                    target_reps_max: fila.target_reps_max,
                    rest_seconds: fila.rest_seconds,
                  })
                }
              />
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}
