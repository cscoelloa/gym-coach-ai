import { Aviso } from "@/ds/Aviso";
import { Button } from "@/ds/Button";
import { Icono } from "@/ds/Icono";
import { ProgressBar } from "@/ds/ProgressBar";

import type { Foco } from "../api";
import type { Entreno } from "./useEntrenar";

export function AvanceDelEntreno({ datos, e }: { datos: Foco; e: Entreno }) {
  const ultimo = datos.indice >= datos.total_ejercicios || e.todoHecho;

  return (
    <div className="focus-area-progreso">
      <div className="focus-progress-row flex items-end gap-2">
        <button
          type="button"
          className="icon-button bg-surface-200 text-ink-muted disabled:opacity-40"
          disabled={datos.indice <= 1}
          onClick={() => e.irAEjercicio(datos.indice - 1)}
        >
          <Icono nombre="chevronIzquierda" className="size-5" />
          <span className="sr-only">Anterior</span>
        </button>
        <div className="min-w-0 flex-1 pb-1">
          <ProgressBar
            etiqueta={`Ejercicio ${datos.indice} de ${datos.total_ejercicios || 1}`}
            hecho={datos.avance.hechas}
            total={datos.avance.objetivo}
            unidad="series"
            marca
          />
        </div>
        {!ultimo ? (
          <button
            type="button"
            className="icon-button bg-primary-soft text-primary"
            onClick={() => e.irAEjercicio(datos.indice + 1)}
          >
            <Icono nombre="chevronDerecha" className="size-5" />
            <span className="sr-only">Siguiente</span>
          </button>
        ) : (
          <Button
            variante="primary"
            tamano="sm"
            disabled={e.finalizar.isPending}
            onClick={e.terminar}
          >
            {e.finalizar.isPending ? (
              "Cerrando…"
            ) : (
              <>
                Terminar<span className="sr-only"> entrenamiento</span>
              </>
            )}
          </Button>
        )}
      </div>
      {e.finalizar.error && (
        <div className="mt-3">
          <Aviso tono="error" urgente>
            No se pudo terminar el entrenamiento. Inténtalo de nuevo.
          </Aviso>
        </div>
      )}
    </div>
  );
}
