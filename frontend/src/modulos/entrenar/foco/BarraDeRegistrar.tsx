import { Aviso } from "@/ds/Aviso";
import { Button } from "@/ds/Button";
import { RestTimer } from "@/ds/RestTimer";
import { Stepper } from "@/ds/Stepper";

import { OfertaDeAvisos } from "./OfertaDeAvisos";
import { textoDeLaSiguiente } from "./textos";
import type { Entreno } from "./useEntrenar";

export function BarraDeRegistrar({ e }: { e: Entreno }) {
  return (
    <div className="focus-area-dock focus-dock">
      {e.descanso.restante !== null && <OfertaDeAvisos />}
      {e.descanso.restante !== null && (
        <RestTimer
          compacto
          restante={e.descanso.restante}
          total={e.descanso.total}
          siguiente={e.activa ? textoDeLaSiguiente(e.activa) : undefined}
        >
          <Button variante="ghost" tamano="sm" onClick={e.alargarDescanso}>
            +30 s
          </Button>
          <Button variante="secondary" tamano="sm" onClick={e.saltarDescanso}>
            Saltar
          </Button>
        </RestTimer>
      )}

      <div className="grid grid-cols-2 gap-3">
        <Stepper
          etiqueta="kg"
          valor={e.peso}
          onCambio={e.setPeso}
          paso={2.5}
          decimal
          tamano="lg"
        />
        <Stepper etiqueta="Reps" valor={e.reps} onCambio={e.setReps} minimo={1} tamano="lg" />
      </div>

      <Button
        variante="primary"
        tamano="lg"
        bloque
        disabled={e.registrar.isPending || !e.enLinea}
        onClick={e.registrarSerie}
      >
        {e.registrar.isPending ? "Guardando…" : "Registrar serie"}
      </Button>

      {!e.enLinea && (
        <p className="body-sm text-center text-ink-muted">
          Sin conexión: para registrar la serie hace falta red.
        </p>
      )}
      {e.enLinea && e.registrar.error && (
        <Aviso tono="error" urgente>
          No se pudo registrar la serie. Comprueba la conexión e inténtalo de nuevo.
        </Aviso>
      )}
    </div>
  );
}
