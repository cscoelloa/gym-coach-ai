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
      <PageHeader titulo="Entrenar" hero="primary" entradilla="Lo de hoy, y todo lo que llevas hecho." />

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
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                {data.results.map((sesion) => {
                  const fecha = comoFecha(sesion.date);
                  const enCurso = sesion.finished_at === null;
                  const destino = enCurso
                    ? `/entrenamientos/${sesion.id}/`
                    : `/entrenamientos/${sesion.id}/cierre/`;
                  const nombre =
                    sesion.routine_name ?? (sesion.routine ? "Rutina" : "Entrenamiento libre");

                  return (
                    <Link className="diario-card hover:no-underline" to={destino} key={sesion.id}>
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0">
                          <span className="tag block text-ink-subtle first-letter:uppercase">
                            {DIA_SEMANA.format(fecha)} · {DIA.format(fecha)} {MES.format(fecha)}
                          </span>
                          <h3 className="title-sm mt-0.5 truncate text-ink">{nombre}</h3>
                        </div>
                        {enCurso ? (
                          <Badge tono="warn">En curso</Badge>
                        ) : (
                          <Badge tono="done">Finalizado</Badge>
                        )}
                      </div>

                      <div className="mt-3 flex flex-wrap gap-x-6 gap-y-2">
                        {sesion.set_count > 0 && (
                          <span>
                            <span className="metric-sm num block text-ink">{sesion.set_count}</span>
                            <span className="tag text-ink-subtle">
                              {sesion.set_count === 1 ? "serie" : "series"}
                            </span>
                          </span>
                        )}
                        {sesion.duracion_minutos != null && (
                          <span>
                            <span className="metric-sm num block text-ink">
                              {sesion.duracion_minutos}
                            </span>
                            <span className="tag text-ink-subtle">min</span>
                          </span>
                        )}
                        {sesion.tonelaje_kg > 0 && (
                          <span>
                            <span className="metric-sm num block text-ink">
                              {sesion.tonelaje_kg.toLocaleString("es-ES")}
                            </span>
                            <span className="tag text-ink-subtle">kg movidos</span>
                          </span>
                        )}
                      </div>
                    </Link>
                  );
                })}
              </div>

              <Paginacion
                pagina={pagina}
                total={data.total_pages}
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
