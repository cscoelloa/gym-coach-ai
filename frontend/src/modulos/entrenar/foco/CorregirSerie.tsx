import { useState } from "react";

import { Aviso } from "@/ds/Aviso";
import { Button } from "@/ds/Button";
import { Panel } from "@/ds/Panel";
import { Stepper } from "@/ds/Stepper";

import { useBorrarSerie, useCorregirSerie, type FilaDeSerie } from "../api";

export function CorregirSerie({
  sesionId,
  fila,
  onCerrar,
}: {
  sesionId: number;
  fila: FilaDeSerie;
  onCerrar: () => void;
}) {
  const corregir = useCorregirSerie(sesionId);
  const borrar = useBorrarSerie(sesionId);
  const [peso, setPeso] = useState(fila.peso);
  const [reps, setReps] = useState(fila.reps !== null ? String(fila.reps) : "");
  const ocupado = corregir.isPending || borrar.isPending;

  return (
    <Panel titulo={`Serie ${fila.numero}`} onCerrar={onCerrar}>
      <div className="grid grid-cols-2 gap-3">
        <Stepper etiqueta="kg" valor={peso} onCambio={setPeso} paso={2.5} decimal tamano="lg" />
        <Stepper etiqueta="Reps" valor={reps} onCambio={setReps} minimo={1} tamano="lg" />
      </div>
      {(corregir.error || borrar.error) && (
        <div className="mt-4">
          <Aviso tono="error" urgente>
            No se pudo guardar el cambio. Inténtalo otra vez.
          </Aviso>
        </div>
      )}
      <div className="mt-6 flex flex-col gap-2">
        <Button
          variante="primary"
          tamano="lg"
          bloque
          disabled={ocupado}
          onClick={() =>
            corregir.mutate(
              { id: fila.serie_id!, weight_kg: peso || null, reps: reps ? Number(reps) : null },
              { onSuccess: onCerrar },
            )
          }
        >
          {corregir.isPending ? "Guardando…" : "Guardar"}
        </Button>
        <Button
          variante="danger"
          bloque
          disabled={ocupado}
          onClick={() => borrar.mutate(fila.serie_id!, { onSuccess: onCerrar })}
        >
          Borrar la serie {fila.numero}
        </Button>
      </div>
    </Panel>
  );
}
