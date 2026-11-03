import { useState } from "react";

import { Aviso } from "@/ds/Aviso";
import { useUnRato } from "@/ds/AvisoPasajero";
import { Button } from "@/ds/Button";
import { Campo } from "@/ds/Campo";
import { Card } from "@/ds/Card";
import { Cargando, ErrorDePantalla } from "@/ds/estados";

import { useGuardarProgramacion, useProgramacion, type Programacion as ProgramacionDeObjetivo } from "../api";
import { erroresDe, mensajeDe } from "./errores";

export function Programacion() {
  const { data, isPending, error, refetch } = useProgramacion();

  if (isPending) return <Cargando />;
  if (error || !data) return <ErrorDePantalla onReintentar={() => void refetch()} />;

  return (
    <div className="card-list">
      {data.map((reglas) => (
        <ReglasDeUnObjetivo key={reglas.id} reglas={reglas} />
      ))}
      <p className="body-sm text-ink-muted">
        Estos números son los que se comprueban en la respuesta del modelo. Si un plan no los
        cumple se rechaza y se le pide que lo corrija, así que subirlos mucho puede agotar los
        intentos.
      </p>
    </div>
  );
}

const CAMPOS_DE_PROGRAMACION = [
  { campo: "sets_min", etiqueta: "Series mínimas por ejercicio" },
  { campo: "sets_max", etiqueta: "Series máximas por ejercicio" },
  { campo: "reps_min", etiqueta: "Repeticiones mínimas" },
  { campo: "reps_max", etiqueta: "Repeticiones máximas" },
  { campo: "rest_min_compound", etiqueta: "Descanso mínimo en compuestos (s)" },
  { campo: "rest_min_isolation", etiqueta: "Descanso mínimo en aislamiento (s)" },
  { campo: "sets_min_per_muscle_day", etiqueta: "Series mínimas por músculo y día" },
] as const;

function ReglasDeUnObjetivo({ reglas }: { reglas: ProgramacionDeObjetivo }) {
  const guardar = useGuardarProgramacion();
  const verGuardado = useUnRato(guardar.isSuccess && guardar.submittedAt);
  const [borrador, setBorrador] = useState<Record<string, string>>(() =>
    Object.fromEntries(
      CAMPOS_DE_PROGRAMACION.map(({ campo }) => [campo, String(reglas[campo])]),
    ),
  );

  return (
    <Card>
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2>{reglas.goal_label}</h2>
        <span className="caption text-ink-muted">{reglas.resumen}</span>
      </div>

      <div className="mt-4 grid gap-x-4 sm:grid-cols-2">
        {CAMPOS_DE_PROGRAMACION.map(({ campo, etiqueta }) => (
          <Campo
            key={campo}
            etiqueta={etiqueta}
            type="number"
            min={0}
            inputMode="numeric"
            value={borrador[campo] ?? ""}
            onChange={(evento) =>
              setBorrador({ ...borrador, [campo]: evento.target.value })
            }
            errores={erroresDe(guardar.error, campo)}
          />
        ))}
      </div>

      <div className="form-actions">
        <Button
          variante="primary"
          disabled={guardar.isPending}
          onClick={() =>
            guardar.mutate({
              id: reglas.id,
              ...Object.fromEntries(
                CAMPOS_DE_PROGRAMACION.map(({ campo }) => [campo, Number(borrador[campo])]),
              ),
            })
          }
        >
          {guardar.isPending ? "Guardando…" : "Guardar"}
        </Button>
        {verGuardado && (
          <span role="status" className="aviso-pasajero caption text-success">
            Guardado.
          </span>
        )}
      </div>
      {guardar.error && <Aviso tono="error" urgente>{mensajeDe(guardar.error)}</Aviso>}
    </Card>
  );
}
