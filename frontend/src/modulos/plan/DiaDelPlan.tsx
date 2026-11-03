import { useState } from "react";
import { useNavigate, useParams } from "react-router";

import { Button, EnlaceBoton } from "@/ds/Button";
import { EmptyState } from "@/ds/EmptyState";
import { Cargando, ErrorDePantalla } from "@/ds/estados";

import { useAsignarRutina, usePlan } from "./api";

export function DiaDelPlan({ diaElegido, onListo }: { diaElegido?: number; onListo?: () => void } = {}) {
  const params = useParams();
  const weekday = diaElegido === undefined ? params.weekday ?? "" : String(diaElegido);
  const navegar = useNavigate();
  const { data, isPending, error, refetch } = usePlan();
  const asignar = useAsignarRutina();

  const [elegida, setElegida] = useState<number | null>(null);
  const [tocado, setTocado] = useState(false);

  if (isPending) return <Cargando />;
  if (error || !data) return <ErrorDePantalla onReintentar={refetch} />;

  const dia = data.semana.find((d) => String(d.weekday) === weekday);

  if (!dia || !data.programa) {
    return (
      <EmptyState
        titulo="Ese día no está en tu plan"
        acciones={
          <EnlaceBoton a="/plan/" variante="primary" tamano="sm">
            Volver al plan
          </EnlaceBoton>
        }
      >
        Puede que el enlace sea viejo o que todavía no tengas un programa.
      </EmptyState>
    );
  }

  const seleccion = tocado ? elegida : (dia.rutina?.id ?? null);

  function guardar(evento: React.FormEvent) {
    evento.preventDefault();
    if (dia?.entrada_id == null) return;
    asignar.mutate(
      { entrada: dia.entrada_id, rutina: seleccion },
      { onSuccess: () => (onListo ? onListo() : navegar("/plan/", { replace: true })) },
    );
  }

  function elegir(id: number | null) {
    setTocado(true);
    setElegida(id);
  }

  const enHoja = Boolean(onListo);

  if (!data.rutinas.length) {
    return (
      <>
        {!enHoja && <h1 className="mb-5">{dia.etiqueta}</h1>}
        <EmptyState
          titulo="No tienes ninguna rutina todavía"
          acciones={
            <EnlaceBoton a="/rutinas/nueva/" variante="primary">
              Crear una rutina
            </EnlaceBoton>
          }
        >
          Sin rutinas no hay nada que asignar a un día.
        </EmptyState>
      </>
    );
  }

  return (
    <>
      {enHoja ? (
        <p className="body-sm mb-4 text-ink-muted">
          {data.programa.nombre} · Elige qué rutina toca este día.
        </p>
      ) : (
        <div className="mb-5">
          <p className="section-kicker">{data.programa.nombre}</p>
          <h1>{dia.etiqueta}</h1>
          <p className="body-sm mt-1 text-ink-muted">Elige qué rutina toca este día.</p>
        </div>
      )}

      <form onSubmit={guardar}>
        {asignar.error && (
          <p role="alert" className="body-sm mb-3 text-danger">
            No se pudo guardar el día. Inténtalo de nuevo.
          </p>
        )}
        <div className="compact-list">
          <label className="compact-row cursor-pointer has-[:checked]:bg-primary-soft">
            <input
              className="shrink-0"
              type="radio"
              name="rutina"
              checked={seleccion === null}
              onChange={() => elegir(null)}
            />
            <span className="min-w-0">
              <span className="block font-medium">Descanso</span>
              <span className="caption block text-ink-muted">Sin rutina asignada</span>
            </span>
          </label>

          {data.rutinas.map((rutina) => (
            <label
              key={rutina.id}
              className="compact-row cursor-pointer has-[:checked]:bg-primary-soft"
            >
              <input
                className="shrink-0"
                type="radio"
                name="rutina"
                checked={seleccion === rutina.id}
                onChange={() => elegir(rutina.id)}
              />
              <span className="min-w-0">
                <span className="block truncate font-medium">{rutina.nombre}</span>
                <span className="caption block text-ink-muted">
                  {rutina.n_ejercicios} ejercicio{rutina.n_ejercicios === 1 ? "" : "s"}
                </span>
              </span>
            </label>
          ))}
        </div>

        <div className="form-actions">
          <Button type="submit" variante="primary" disabled={asignar.isPending}>
            {asignar.isPending ? "Guardando…" : "Guardar"}
          </Button>
          <Button onClick={() => (onListo ? onListo() : navegar("/plan/"))}>Cancelar</Button>
        </div>
      </form>

      <p className="caption mt-4 text-ink-muted">
        La misma rutina puede ir en varios días. Si la editas, cambian todos: es la misma.
      </p>
    </>
  );
}
