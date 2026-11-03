import { useEffect, useState } from "react";

import { Aviso } from "@/ds/Aviso";
import { BodyMap } from "@/ds/BodyMap";
import { Button } from "@/ds/Button";
import { GrupoDeChips } from "@/ds/GrupoDeChips";
import { Icono } from "@/ds/Icono";
import {
  SIN_FILTROS,
  useFacetas,
  type Ejercicio,
  type FiltrosDeCatalogo,
} from "@/modulos/ejercicios/api";

import { useBuscadorDeEjercicios } from "./api";

export function SelectorDeEjercicios({ onElegir }: { onElegir: (ejercicio: Ejercicio) => void }) {
  const [filtros, setFiltros] = useState<FiltrosDeCatalogo>(SIN_FILTROS);
  const [texto, setTexto] = useState("");
  const [pagina, setPagina] = useState(1);

  useEffect(() => {
    const espera = setTimeout(() => {
      setFiltros((previos) => ({ ...previos, q: texto }));
      setPagina(1);
    }, 300);
    return () => clearTimeout(espera);
  }, [texto]);

  const listado = useBuscadorDeEjercicios(filtros, pagina);
  const facetas = useFacetas(filtros);

  function cambiar(cambios: Partial<FiltrosDeCatalogo>) {
    setFiltros((previos) => ({ ...previos, ...cambios }));
    setPagina(1);
  }

  return (
    <div>
      <label className="sr-only" htmlFor="buscar-en-rutina">
        Buscar ejercicio
      </label>
      <div className="sticky -top-1 z-[1] -mt-1 bg-surface-000 pt-1 pb-3">
        <div className="relative">
          <Icono
            nombre="lupa"
            className="pointer-events-none absolute top-1/2 left-3.5 size-5 -translate-y-1/2 text-ink-subtle"
          />
          <input
            id="buscar-en-rutina"
            className="pl-11"
            type="search"
            data-autofocus
            value={texto}
            onChange={(evento) => setTexto(evento.target.value)}
            placeholder="Buscar un movimiento…"
            autoComplete="off"
            enterKeyHint="search"
          />
        </div>
      </div>

      <details className="mb-3 rounded-xl bg-surface-100 p-3">
        <summary className="body-sm cursor-pointer py-1 font-medium text-primary">
          Filtros · músculo y equipamiento
        </summary>
        <div className="mt-3 space-y-4">
          <BodyMap
            niveles={{}}
            activo={filtros.muscle}
            onMusculo={(muscle) => cambiar({ muscle: filtros.muscle === muscle ? "" : muscle })}
            compacto
            leyenda="Toca un músculo para filtrar"
          />
          <GrupoDeChips
            titulo="Músculo"
            opciones={facetas.data?.muscle ?? []}
            activo={filtros.muscle}
            onElegir={(muscle) => cambiar({ muscle })}
          />
          <GrupoDeChips
            titulo="Zona corporal"
            opciones={facetas.data?.body_part ?? []}
            activo={filtros.body_part}
            onElegir={(body_part) => cambiar({ body_part })}
          />
          <GrupoDeChips
            titulo="Equipamiento"
            opciones={facetas.data?.equipment ?? []}
            activo={filtros.equipment}
            onElegir={(equipment) => cambiar({ equipment })}
          />
          <Button
            tamano="sm"
            onClick={() => {
              setTexto("");
              setFiltros(SIN_FILTROS);
              setPagina(1);
            }}
          >
            Quitar filtros
          </Button>
        </div>
      </details>

      <p className="caption mb-3 text-ink-muted">
        Según el material de tu perfil. Puedes elegir otro en Filtros.
      </p>

      {listado.isPending ? (
        <p role="status" className="body-sm py-6 text-center text-ink-muted">
          Buscando ejercicios…
        </p>
      ) : listado.error ? (
        <Aviso tono="error">
          No se pudieron cargar los ejercicios.{" "}
          <Button tamano="sm" onClick={() => void listado.refetch()}>
            Reintentar
          </Button>
        </Aviso>
      ) : (
        <>
          <p className="tag mb-2 px-1 text-ink-subtle">{listado.data?.count ?? 0} ejercicios</p>
          <div className="compact-list" aria-busy={listado.isFetching}>
            {listado.data?.results.map((ejercicio) => (
              <button
                key={ejercicio.id}
                className="compact-row"
                disabled={listado.isPlaceholderData}
                onClick={() => onElegir(ejercicio)}
              >
                {ejercicio.image ? (
                  <img src={ejercicio.image} className="ex-media" alt="" loading="lazy" />
                ) : (
                  <span className="ex-glyph">
                    <Icono nombre="entrenar" />
                  </span>
                )}
                <span className="min-w-0 flex-1">
                  <span className="ex-name block truncate">{ejercicio.name}</span>
                  <span className="caption text-ink-muted">
                    {ejercicio.body_part_label} · {ejercicio.equipment_label}
                  </span>
                </span>
                <Icono nombre="mas" className="size-5 text-primary" />
              </button>
            ))}
          </div>
          {!listado.data?.count && (
            <p className="body-sm py-6 text-center text-ink-muted">
              Ningún ejercicio con esos filtros. Prueba otra búsqueda o quita los filtros.
            </p>
          )}
          <div className="mt-4 flex items-center justify-between gap-2">
            <Button
              tamano="sm"
              disabled={pagina === 1 || listado.isFetching}
              onClick={() => setPagina((p) => p - 1)}
            >
              Anterior
            </Button>
            <span className="caption num text-ink-muted">Página {pagina}</span>
            <Button
              tamano="sm"
              disabled={!listado.data?.next || listado.isFetching}
              onClick={() => setPagina((p) => p + 1)}
            >
              Siguiente
            </Button>
          </div>
        </>
      )}
    </div>
  );
}
