import { useState } from "react";
import { Link, useNavigate } from "react-router";

import { Badge } from "@/ds/Badge";
import { Button, EnlaceBoton } from "@/ds/Button";
import { Card, PageHeader } from "@/ds/Card";
import { EmptyState } from "@/ds/EmptyState";
import { Cargando, ErrorDePantalla } from "@/ds/estados";
import { Icono } from "@/ds/Icono";
import { Paginacion } from "@/ds/Paginacion";
import { comoFecha, QueTocaHoy } from "@/modulos/inicio";
import { useInicio } from "@/modulos/inicio/api";

import { useEmpezar, useHistorial } from "./api";

const DIA = new Intl.DateTimeFormat("es-ES", { day: "2-digit" });
const MES = new Intl.DateTimeFormat("es-ES", { month: "short" });
const DIA_SEMANA = new Intl.DateTimeFormat("es-ES", { weekday: "long" });

function Hoy() {
  const { data } = useInicio();
  if (!data) return null;

  return (
    <Card className="card-accent mb-4">
      <QueTocaHoy toca={data.hoy_toca} hoy={data.hoy} />
    </Card>
  );
}

export function Entrenamientos() {
  const [pagina, setPagina] = useState(1);
  const navegar = useNavigate();
  const { data, isPending, error, refetch } = useHistorial(pagina);
  const empezar = useEmpezar();

  return (
    <div className="mx-auto max-w-3xl lg:max-w-6xl">
      <PageHeader titulo="Entrenar" entradilla="Lo de hoy, y todo lo que llevas hecho." />

      <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)] lg:items-start lg:gap-8">
        <div className="lg:sticky lg:top-20">
          <Hoy />

          <div className="mb-8 flex flex-wrap items-center justify-between gap-3 rounded-2xl border-2 border-dashed border-line px-4 py-3">
            <p className="body-sm min-w-0 text-ink-muted">¿Sin plan hoy? Ve registrando sobre la marcha.</p>
            <Button
              variante="secondary"
              disabled={empezar.isPending}
              onClick={() =>
                empezar.mutate(undefined, {
                  onSuccess: (sesion) => navegar(`/entrenamientos/${sesion.id}/`),
                })
              }
            >
              {empezar.isPending ? "Empezando…" : "Entrenamiento libre"}
            </Button>
        </div>
        </div>

        <section aria-labelledby="titulo-diario">
          <h2 id="titulo-diario" className="title-lg mb-3">Diario</h2>

          {isPending ? (
            <Cargando />
          ) : error || !data ? (
            <ErrorDePantalla onReintentar={refetch} />
          ) : data.results.length ? (
            <>
              <div className="card-list">
                {data.results.map((sesion) => {
                  const fecha = comoFecha(sesion.date);
                  const enCurso = sesion.finished_at === null;
                  const destino = enCurso
                    ? `/entrenamientos/${sesion.id}/`
                    : `/entrenamientos/${sesion.id}/cierre/`;
                  const nombre =
                    sesion.routine_name ?? (sesion.routine ? "Rutina" : "Entrenamiento libre");

                  return (
                    <Link className="history-row hover:no-underline" to={destino} key={sesion.id}>
                      <span className="date-block">
                        <span className="metric-md text-ink">{DIA.format(fecha)}</span>
                        <span className="tag text-ink-muted">{MES.format(fecha)}</span>
                      </span>

                      <span className="min-w-0">
                        <span className="title-sm block truncate text-ink">{nombre}</span>
                        <span className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1">
                          {enCurso ? (
                            <Badge tono="warn">En curso</Badge>
                          ) : (
                            <Badge tono="done">Finalizado</Badge>
                          )}
                          <span className="caption text-ink-muted first-letter:uppercase">
                            {DIA_SEMANA.format(fecha)}
                            {sesion.set_count > 0 && (
                              <>
                                {" · "}
                                <span className="num">{sesion.set_count}</span>{" "}
                                {sesion.set_count === 1 ? "serie" : "series"}
                              </>
                            )}
                          </span>
                        </span>
                      </span>

                      <Icono nombre="chevronDerecha" className="size-4 shrink-0 text-ink-subtle" />
                    </Link>
                  );
                })}
              </div>

              <Paginacion
                pagina={pagina}
                hayAnterior={Boolean(data.previous)}
                haySiguiente={Boolean(data.next)}
                onCambio={setPagina}
              />
            </>
          ) : (
            <EmptyState
              titulo="Todavía no has entrenado"
              glifo={<Icono nombre="entrenar" />}
              acciones={
                <EnlaceBoton a="/plan/" variante="primary">
                  Ir a mis rutinas
                </EnlaceBoton>
              }
            >
              Empieza desde una rutina del plan, o registra un entrenamiento libre.
            </EmptyState>
          )}
        </section>
      </div>
    </div>
  );
}
