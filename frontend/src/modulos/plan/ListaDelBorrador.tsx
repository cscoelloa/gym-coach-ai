import { Button } from "@/ds/Button";
import { Icono } from "@/ds/Icono";

import type { ControlDelEditor } from "./useEditorDeRutina";

export function ListaDelBorrador({ e }: { e: ControlDelEditor }) {
  const { borrador, campos } = e;

  return (
    <section aria-label="Ejercicios de la rutina">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-x-3 gap-y-2">
        <h2 className="title-lg whitespace-nowrap">
          Ejercicios <span className="num text-ink-subtle">{borrador.exercises.length}</span>
        </h2>
        <Button tamano="sm" className="whitespace-nowrap" onClick={() => e.setHoja("buscar")}>
          <Icono nombre="mas" className="size-4" />
          Añadir ejercicio
        </Button>
      </div>

      {!borrador.exercises.length && (
        <div className="empty-state">
          <Icono nombre="entrenar" className="size-7" />
          <p className="empty-title">Empieza con tu primer ejercicio.</p>
          <p>Elige, configura y guarda cuando esté lista.</p>
        </div>
      )}

      {borrador.exercises.length > 0 && (
        <ol className="compact-list">
          {borrador.exercises.map((fila, indice) => (
            <li key={fila.clave}>
              <div className="compact-row py-2 pr-2">
                <button
                  type="button"
                  className="flex min-h-14 min-w-0 flex-1 items-center gap-3 text-left"
                  onClick={() => e.editar(fila)}
                >
                  {fila.exercise_detail.image ? (
                    <img className="ex-media" src={fila.exercise_detail.image} alt="" />
                  ) : (
                    <span className="ex-glyph">
                      <Icono nombre="entrenar" />
                    </span>
                  )}
                  <span className="min-w-0">
                    <span className="ex-name block truncate">{fila.exercise_detail.name}</span>
                    <span className="mt-0.5 flex flex-wrap items-center gap-x-2 gap-y-1">
                      {fila.exercise_detail.target_muscle && (
                        <span className="tag-musculo">
                          {fila.exercise_detail.target_muscle.name}
                        </span>
                      )}
                      <span className="caption num text-ink-muted">
                        {fila.target_sets} × {fila.target_reps_min}–{fila.target_reps_max} ·{" "}
                        {fila.rest_seconds} s
                      </span>
                    </span>
                  </span>
                </button>
                <div className="flex shrink-0 flex-col">
                  <button
                    type="button"
                    className="order-button h-10 w-11"
                    aria-label={`Subir ${fila.exercise_detail.name}`}
                    disabled={indice === 0}
                    onClick={() => e.mover(indice, -1)}
                  >
                    <Icono nombre="chevronArriba" className="size-4" />
                  </button>
                  <button
                    type="button"
                    className="order-button h-10 w-11"
                    aria-label={`Bajar ${fila.exercise_detail.name}`}
                    disabled={indice === borrador.exercises.length - 1}
                    onClick={() => e.mover(indice, 1)}
                  >
                    <Icono nombre="chevronAbajo" className="size-4" />
                  </button>
                </div>
              </div>
              {Object.entries(campos)
                .filter(([campo]) => campo.startsWith(`exercises.${indice}.`))
                .map(([campo, mensajes]) => (
                  <p role="alert" key={campo} className="caption px-4 pb-2 text-danger">
                    {mensajes.join(" ")}
                  </p>
                ))}
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}
