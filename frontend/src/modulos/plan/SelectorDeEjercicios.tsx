import { useEffect, useState } from "react";

import { Aviso } from "@/ds/Aviso";
import { BodyMap } from "@/ds/BodyMap";
import { Button } from "@/ds/Button";
import { GrupoDeChips } from "@/ds/GrupoDeChips";
import { Icono } from "@/ds/Icono";
import { Paginacion } from "@/ds/Paginacion";
import {
  SIN_FILTROS,
  useFacetas,
  type Ejercicio,
  type FiltrosDeCatalogo,
} from "@/modulos/ejercicios/api";

import { useBuscadorDeEjercicios } from "./api";

export function SelectorDeEjercicios({
  onElegir,
  anadidos,
  onListo,
}: {
  onElegir: (ejercicio: Ejercicio) => void;
  anadidos: Map<number, string>;
  onListo: () => void;
}) {
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

      <details className="mb-3 rounded-xl bg-surface-100 px-3 py-1">
        <summary className="body-sm cursor-pointer py-2.5 font-medium text-primary">
          Filtros · músculo y equipamiento
        </summary>
        <div className="mt-1 space-y-4 pb-3">
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
            {listado.data?.results.map((ejercicio) => {
              const esquema = anadidos.get(ejercicio.id);
              return (
                <button
                  key={ejercicio.id}
                  className="compact-row"
                  data-anadido={esquema ? "true" : "false"}
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
                    {ejercicio.target_muscle ? (
                      <span className="tag-musculo">{ejercicio.target_muscle.name}</span>
                    ) : (
                      <span className="caption text-ink-muted">{ejercicio.body_part_label}</span>
                    )}
                  </span>
                  {esquema ? (
                    <span className="flex shrink-0 items-center gap-1.5 text-primary">
                      <span className="tag num">{esquema}</span>
                      <Icono nombre="comprobado" className="size-5" />
                    </span>
                  ) : (
                    <Icono nombre="mas" className="size-5 text-primary" />
                  )}
                </button>
              );
            })}
          </div>
          {!listado.data?.count && (
            <p className="body-sm py-6 text-center text-ink-muted">
              Ningún ejercicio con esos filtros. Prueba otra búsqueda o quita los filtros.
            </p>
          )}
          <Paginacion
            pagina={pagina}
            total={listado.data?.total_pages}
            hayAnterior={pagina > 1}
            haySiguiente={Boolean(listado.data?.next)}
            ocupado={listado.isFetching}
            onCambio={setPagina}
          />
        </>
      )}

      <div className="selector-pie">
        <Button variante="primary" bloque onClick={onListo}>
          {anadidos.size ? `Listo · ${anadidos.size}` : "Listo"}
        </Button>
      </div>
    </div>
  );
}
