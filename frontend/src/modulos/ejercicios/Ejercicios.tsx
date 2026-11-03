import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router";

import { BodyMap } from "@/ds/BodyMap";
import { Button, EnlaceBoton } from "@/ds/Button";
import { EmptyState } from "@/ds/EmptyState";
import { Cargando, ErrorDePantalla } from "@/ds/estados";
import { GrupoDeChips } from "@/ds/GrupoDeChips";
import { Icono } from "@/ds/Icono";
import { Paginacion } from "@/ds/Paginacion";

import { useEjercicios, useFacetas, type FiltrosDeCatalogo } from "./api";
import { TarjetaDeEjercicio } from "./TarjetaDeEjercicio";

function leerFiltros(params: URLSearchParams): FiltrosDeCatalogo {
  return {
    q: params.get("q") ?? "",
    body_part: params.get("body_part") ?? "",
    equipment: params.get("equipment") ?? "",
    muscle: params.get("muscle") ?? "",
  };
}

export function Ejercicios() {
  const [params, setParams] = useSearchParams();
  const filtros = leerFiltros(params);
  const pagina = Number(params.get("page") ?? 1);

  const [texto, setTexto] = useState(filtros.q);
  useEffect(() => setTexto(filtros.q), [filtros.q]);
  useEffect(() => {
    if (texto === filtros.q) return;
    const id = setTimeout(() => cambiar({ q: texto }, { reemplazar: true }), 300);
    return () => clearTimeout(id);
  });

  const listado = useEjercicios(filtros, pagina);
  const facetas = useFacetas(filtros);

  function cambiar(
    cambios: Partial<FiltrosDeCatalogo>,
    { reemplazar = false }: { reemplazar?: boolean } = {},
  ) {
    const siguientes = { ...filtros, ...cambios };
    const nuevos = new URLSearchParams();
    for (const [clave, valor] of Object.entries(siguientes)) {
      if (valor) nuevos.set(clave, valor);
    }
    setParams(nuevos, { replace: reemplazar });
  }

  function irAPagina(numero: number) {
    const nuevos = new URLSearchParams(params);
    nuevos.set("page", String(numero));
    setParams(nuevos);
    window.scrollTo({ top: 0 });
  }

  const hayFiltros = Object.values(filtros).some(Boolean);

  if (listado.isPending && !listado.data) return <Cargando />;
  if (listado.error) return <ErrorDePantalla onReintentar={listado.refetch} />;

  const total = listado.data?.count ?? 0;
  const ejercicios = listado.data?.results ?? [];

  return (
    <>
      <section className="catalog-hero">
        <div className="min-w-0">
          
          <h1>Ejercicios</h1>
          <p className="body mt-2 max-w-lg text-ink-muted">
            <span className="num">{total}</span> movimientos con referencia visual, organizados por
            zona y equipamiento.
          </p>
        </div>

        <div className="w-full max-w-sm">
          <label htmlFor="buscar" className="sr-only">
            Buscar ejercicio
          </label>
          <div className="relative">
            <span className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-ink-subtle">
              <Icono nombre="lupa" />
            </span>
            <input
              id="buscar"
              className="pl-12"
              type="search"
              value={texto}
              onChange={(evento) => setTexto(evento.target.value)}
              placeholder="Buscar un movimiento…"
              autoComplete="off"
            />
          </div>
        </div>
      </section>

      <details className="filter-deck" aria-label="Filtros del catálogo">
        <summary className="cursor-pointer py-2 font-semibold">Filtros · músculo, zona y equipamiento</summary>
        <div className="mb-3 flex items-center justify-between gap-3">
          <div>
            
            <h2>Por músculo</h2>
          </div>
          {hayFiltros && (
            <Button variante="secondary" tamano="sm" onClick={() => setParams(new URLSearchParams())}>
              Limpiar
            </Button>
          )}
        </div>

        <div className="surface-2 mb-4 rounded-md p-3">
          <BodyMap
            niveles={{}}
            activo={filtros.muscle}
            onMusculo={(musculo) =>
              cambiar({ muscle: musculo === filtros.muscle ? "" : musculo })
            }
            compacto
            leyenda="Toca un músculo para filtrar"
          />

          <div className="mt-3">
            <GrupoDeChips
              titulo="Músculo"
              opciones={facetas.data?.muscle ?? []}
              activo={filtros.muscle}
              onElegir={(valor) => cambiar({ muscle: valor })}
            />
          </div>
        </div>

        <div className="mb-4">
          <GrupoDeChips
            titulo="Zona corporal"
            opciones={facetas.data?.body_part ?? []}
            activo={filtros.body_part}
            onElegir={(valor) => cambiar({ body_part: valor })}
          />
        </div>
        <GrupoDeChips
          titulo="Equipamiento"
          opciones={facetas.data?.equipment ?? []}
          activo={filtros.equipment}
          onElegir={(valor) => cambiar({ equipment: valor })}
        />
      </details>

      <div className="mb-3 flex items-end justify-between gap-3">
        <div>
          <p className="section-kicker">Resultados</p>
          <h2>
            <span className="num">{total}</span> movimiento{total === 1 ? "" : "s"}
          </h2>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-4">
        <Link className="exercise-card-create" to="/ejercicios/nuevo/">
          <span className="exercise-card-media">
            <Icono nombre="mas" className="size-9 text-primary" />
          </span>
          <span className="flex min-w-0 flex-1 flex-col p-3">
            <span className="title-sm block">Crea tu ejercicio</span>
            <span className="caption mt-1 block text-ink-muted">
              Uno que no esté en el catálogo.
            </span>
          </span>
        </Link>

        {ejercicios.map((ejercicio) => (
          <TarjetaDeEjercicio key={ejercicio.id} ejercicio={ejercicio} />
        ))}

        {!ejercicios.length && (
          <div className="col-span-2 sm:col-span-3 xl:col-span-4">
            <EmptyState
              titulo="Ningún ejercicio con esos filtros"
              glifo={<Icono nombre="lupa" />}
              acciones={
                <Button
                  variante="secondary"
                  tamano="sm"
                  onClick={() => setParams(new URLSearchParams())}
                >
                  Quitar los filtros
                </Button>
              }
            >
              Prueba con una sola zona del cuerpo o quita el filtro de equipamiento.
            </EmptyState>
          </div>
        )}
      </div>

      <Paginacion
        pagina={pagina}
        hayAnterior={Boolean(listado.data?.previous)}
        haySiguiente={Boolean(listado.data?.next)}
        onCambio={irAPagina}
      />

      <p className="body-sm mt-6 text-center text-ink-muted">
        ¿No encuentras el tuyo?{" "}
        <EnlaceBoton a="/ejercicios/nuevo/" variante="ghost" tamano="sm">
          Créalo
        </EnlaceBoton>
      </p>
    </>
  );
}
