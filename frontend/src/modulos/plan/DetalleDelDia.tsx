import { useState } from "react";
import { useNavigate, useParams } from "react-router";

import { Button, EnlaceBoton } from "@/ds/Button";
import { Cargando, ErrorDePantalla } from "@/ds/estados";
import { Icono } from "@/ds/Icono";
import { useEmpezar } from "@/modulos/entrenar/api";

import { usePlan, useRutina } from "./api";
import { DiaDelPlan } from "./DiaDelPlan";

export function DetalleDelDia({
  diaElegido,
  onListo,
}: { diaElegido?: number; onListo?: () => void } = {}) {
  const params = useParams();
  const weekday = diaElegido === undefined ? Number(params.weekday) : diaElegido;
  const navegar = useNavigate();
  const plan = usePlan();
  const empezar = useEmpezar();
  const [cambiando, setCambiando] = useState(false);

  const dia = plan.data?.semana.find((d) => d.weekday === weekday);
  const rutina = useRutina(dia?.rutina?.id ?? NaN);
  const enHoja = Boolean(onListo);

  if (plan.isPending) return <Cargando />;
  if (plan.error || !plan.data) return <ErrorDePantalla onReintentar={plan.refetch} />;

  if (!dia || !dia.rutina || cambiando) {
    return <DiaDelPlan diaElegido={diaElegido} onListo={onListo} />;
  }

  const rid = dia.rutina.id;

  return (
    <div className="space-y-4">
      {!enHoja && (
        <div>
          <p className="section-kicker">{plan.data.programa?.nombre}</p>
          <h1>{dia.etiqueta}</h1>
        </div>
      )}

      <div className="flex flex-col gap-2 sm:flex-row">
        <Button
          variante="primary"
          tamano="lg"
          bloque
          disabled={empezar.isPending}
          onClick={() =>
            empezar.mutate(rid, { onSuccess: (s) => navegar(`/entrenamientos/${s.id}/`) })
          }
        >
          <Icono nombre="entrenar" className="size-5" />
          {empezar.isPending ? "Empezando…" : "Entrenar"}
        </Button>
        <EnlaceBoton a={`/rutinas/${rid}/`} variante="secondary" tamano="lg" bloque>
          Editar rutina
        </EnlaceBoton>
      </div>

      {rutina.isPending ? (
        <p role="status" className="body-sm py-6 text-center text-ink-muted">
          Cargando la rutina…
        </p>
      ) : rutina.error || !rutina.data ? (
        <ErrorDePantalla onReintentar={rutina.refetch} />
      ) : rutina.data.exercises.length ? (
        <ol className="compact-list">
          {rutina.data.exercises.map((ej) => (
            <li key={ej.id} className="compact-row">
              {ej.exercise_detail.image ? (
                <img src={ej.exercise_detail.image} className="ex-media" alt="" loading="lazy" />
              ) : (
                <span className="ex-glyph">
                  <Icono nombre="entrenar" />
                </span>
              )}
              <span className="min-w-0 flex-1">
                <span className="ex-name block truncate">{ej.exercise_detail.name}</span>
                {ej.exercise_detail.target_muscle ? (
                  <span className="tag-musculo">{ej.exercise_detail.target_muscle.name}</span>
                ) : (
                  <span className="caption text-ink-muted">
                    {ej.exercise_detail.body_part_label}
                  </span>
                )}
              </span>
              <span className="caption num shrink-0 text-ink-muted">
                {ej.target_sets} × {ej.target_reps_min}–{ej.target_reps_max} · {ej.rest_seconds} s
              </span>
            </li>
          ))}
        </ol>
      ) : (
        <div className="empty-state">
          <p className="empty-title">Esta rutina todavía no tiene ejercicios.</p>
          <EnlaceBoton a={`/rutinas/${rid}/`} variante="primary" tamano="sm">
            Añadir ejercicios
          </EnlaceBoton>
        </div>
      )}

      <button
        type="button"
        className="body-sm py-2 font-medium text-primary"
        onClick={() => setCambiando(true)}
      >
        Cambiar la rutina de este día
      </button>
    </div>
  );
}
