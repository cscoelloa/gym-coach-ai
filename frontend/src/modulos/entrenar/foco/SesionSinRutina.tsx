import { Button } from "@/ds/Button";
import { EmptyState } from "@/ds/EmptyState";
import { ProgressBar } from "@/ds/ProgressBar";

import type { Foco } from "../api";

export function SesionSinRutina({ datos, onTerminar }: { datos: Foco; onTerminar: () => void }) {
  return (
    <>
      <ProgressBar
        etiqueta={`Ejercicio ${datos.indice} de ${datos.total_ejercicios || 1}`}
        hecho={datos.avance.hechas}
        total={datos.avance.objetivo}
        unidad="series"
        marca
      />
      <div className="mt-6">
        <EmptyState
          titulo="Esta sesión no sigue una rutina"
          acciones={
            <Button variante="primary" onClick={onTerminar}>
              Terminar
            </Button>
          }
        >
          Puedes registrar series sueltas desde el historial, o empezar desde una rutina del plan.
        </EmptyState>
      </div>
    </>
  );
}
