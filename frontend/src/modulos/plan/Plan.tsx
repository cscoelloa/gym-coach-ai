import { useState } from "react";
import { Link } from "react-router";

import { Aviso } from "@/ds/Aviso";
import { Badge } from "@/ds/Badge";
import { Button, EnlaceBoton } from "@/ds/Button";
import { Cabecera } from "@/ds/Cabecera";
import { Cargando, ErrorDePantalla } from "@/ds/estados";
import { Icono } from "@/ds/Icono";
import { Panel } from "@/ds/Panel";

import { useActivarPrograma, useBorrarPrograma, usePlan } from "./api";
import { DiaDelPlan } from "./DiaDelPlan";

function HojaDeProgramas({ onCerrar }: { onCerrar: () => void }) {
  const { data } = usePlan();
  const activar = useActivarPrograma();
  const borrar = useBorrarPrograma();
  const [confirmarBorrado, setConfirmarBorrado] = useState(false);

  if (!data) return null;
  const { programa, programas } = data;

  return (
    <Panel titulo="Tus programas" onCerrar={onCerrar}>
      <p className="body-sm mb-4 text-ink-muted">
        Elige la semana que estás siguiendo. Tus rutinas se conservan al cambiar de programa.
      </p>
      {(activar.error || borrar.error) && (
        <div className="mb-3">
          <Aviso tono="error">No se pudo actualizar el programa. Inténtalo de nuevo.</Aviso>
        </div>
      )}

      <div className="compact-list">
        {programas.map((p) => (
          <button
            className="compact-row"
            key={p.id}
            disabled={activar.isPending || p.activo}
            onClick={() => activar.mutate(p.id)}
          >
            <span className="flex-1">{p.nombre}</span>
            {p.activo ? (
              <Badge tono="record">Activo</Badge>
            ) : (
              <span className="text-primary">Activar</span>
            )}
          </button>
        ))}
      </div>

      <div className="mt-3">
        <EnlaceBoton a="/programas/nuevo/" variante="ghost">
          <Icono nombre="mas" className="size-5" />
          Crear otro programa
        </EnlaceBoton>
      </div>

      {programa && (
        <div className="mt-6 border-t border-line pt-4">
          {confirmarBorrado ? (
            <>
              <p className="body-sm">
                ¿Eliminar «{programa.nombre}»? Las rutinas y los entrenamientos se conservan.
              </p>
              <div className="form-actions">
                <Button
                  variante="danger"
                  disabled={borrar.isPending}
                  onClick={() =>
                    borrar.mutate(programa.id, { onSuccess: () => setConfirmarBorrado(false) })
                  }
                >
                  Sí, eliminar programa
                </Button>
                <Button onClick={() => setConfirmarBorrado(false)}>Cancelar</Button>
              </div>
            </>
          ) : (
            <Button variante="danger" onClick={() => setConfirmarBorrado(true)}>
              Eliminar programa
            </Button>
          )}
        </div>
      )}
    </Panel>
  );
}

export function Plan() {
  const consulta = usePlan();
  const [dia, setDia] = useState<number | null>(null);
  const [programas, setProgramas] = useState(false);

  if (consulta.isPending) return <Cargando />;
  if (consulta.error || !consulta.data) {
    return <ErrorDePantalla onReintentar={consulta.refetch} />;
  }
  const { programa, semana, rutinas, hoy_weekday } = consulta.data;

  return (
    <>
      <Cabecera
        titulo="Plan"
        descripcion={programa?.nombre ?? "Tu semana de entrenamiento"}
        acciones={
          <>
            <EnlaceBoton a="/ia/generar/" tamano="sm">
              Crear con IA
            </EnlaceBoton>
            <Button tamano="sm" onClick={() => setProgramas(true)}>
              Programas
            </Button>
          </>
        }
      />

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-2 lg:items-start">
        <section aria-label="Tu semana">
          <h2 className="title-lg mb-3">Tu semana</h2>
          {programa ? (
            <div className="compact-list">
              {semana.map((d) => (
                <button key={d.weekday} className="compact-row" onClick={() => setDia(d.weekday)}>
                  <span
                    className="day-tile"
                    data-rutina={d.rutina ? "true" : "false"}
                    data-hoy={d.weekday === hoy_weekday ? "true" : "false"}
                    aria-hidden="true"
                  >
                    {d.etiqueta.slice(0, 2)}
                  </span>
                  <span className="w-24 shrink-0 font-semibold">{d.etiqueta}</span>
                  <span
                    className={`min-w-0 flex-1 truncate text-right ${
                      d.rutina ? "text-ink" : "text-ink-subtle"
                    }`}
                  >
                    {d.rutina ? d.rutina.nombre : "Descanso"}
                  </span>
                  {d.weekday === hoy_weekday && <Badge tono="record">Hoy</Badge>}
                  <Icono nombre="chevronDerecha" className="size-4" />
                </button>
              ))}
            </div>
          ) : (
            <div className="card card-accent space-y-3">
              <h3 className="title-md">Organiza tu primera semana</h3>
              <p className="body-sm text-ink-muted">
                Crea un programa para repartir tus rutinas de lunes a domingo.
              </p>
              <EnlaceBoton a="/programas/nuevo/" variante="primary">
                Crear programa
              </EnlaceBoton>
            </div>
          )}
        </section>

        <section aria-label="Tus rutinas">
          <div className="mb-3 flex items-center justify-between gap-3">
            <h2 className="title-lg">Tus rutinas</h2>
            <EnlaceBoton a="/rutinas/nueva/" tamano="sm" variante="primary">
              <Icono nombre="mas" className="size-4" />
              Nueva
            </EnlaceBoton>
          </div>
          {rutinas.length ? (
            <div className="compact-list">
              {rutinas.map((r) => (
                <Link key={r.id} className="compact-row hover:no-underline" to={`/rutinas/${r.id}/`}>
                  <span className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-primary-soft text-primary">
                    <Icono nombre="entrenar" />
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="block truncate font-semibold text-ink">{r.nombre}</span>
                    <span className="caption text-ink-muted">
                      {r.n_ejercicios} ejercicio{r.n_ejercicios !== 1 ? "s" : ""} ·{" "}
                      {r.dias.length ? r.dias.join(", ") : "sin asignar"}
                    </span>
                  </span>
                  <Icono nombre="chevronDerecha" className="size-4" />
                </Link>
              ))}
            </div>
          ) : (
            <div className="empty-state">
              <span className="empty-glyph" aria-hidden="true">
                <Icono nombre="entrenar" />
              </span>
              <p className="empty-title">Todavía no tienes rutinas</p>
              <p>Añade tus ejercicios y después asígnalos a tu semana.</p>
              <EnlaceBoton a="/rutinas/nueva/" variante="primary" tamano="sm">
                Crear la primera
              </EnlaceBoton>
            </div>
          )}
        </section>
      </div>

      {dia !== null && (
        <Panel
          titulo={`Organizar el ${(semana.find((d) => d.weekday === dia)?.etiqueta ?? "día").toLowerCase()}`}
          onCerrar={() => setDia(null)}
        >
          <DiaDelPlan diaElegido={dia} onListo={() => setDia(null)} />
        </Panel>
      )}
      {programas && <HojaDeProgramas onCerrar={() => setProgramas(false)} />}
    </>
  );
}
