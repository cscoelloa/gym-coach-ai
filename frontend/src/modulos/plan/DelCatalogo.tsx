import { Aviso } from "@/ds/Aviso";
import { BodyMap } from "@/ds/BodyMap";
import { Button } from "@/ds/Button";
import { GrupoDeChips } from "@/ds/GrupoDeChips";
import { Paginacion } from "@/ds/Paginacion";
import { useFacetas, type Ejercicio } from "@/modulos/ejercicios/api";

import { useBuscadorDeEjercicios } from "./api";
import { FilaDeEjercicio } from "./FilaDeEjercicio";
import type { BusquedaDeEjercicios } from "./useBusquedaDeEjercicios";

export function DelCatalogo({
  busqueda,
  anadidos,
  onElegir,
}: {
  busqueda: BusquedaDeEjercicios;
  anadidos: Map<number, string>;
  onElegir: (ejercicio: Ejercicio) => void;
}) {
  const { filtros, pagina, setPagina, cambiar } = busqueda;
  const listado = useBuscadorDeEjercicios(filtros, pagina);
  const facetas = useFacetas(filtros);

  return (
    <>
      <details
        className="mb-3 rounded-xl bg-surface-100 px-3 py-1"
        open={busqueda.abierta}
        onToggle={(evento) => busqueda.setAbierta(evento.currentTarget.open)}
      >
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
          <Button tamano="sm" onClick={busqueda.limpiar}>
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
              <FilaDeEjercicio
                key={ejercicio.id}
                ejercicio={ejercicio}
                detalle={
                  ejercicio.target_muscle ? (
                    <span className="tag-musculo">{ejercicio.target_muscle.name}</span>
                  ) : (
                    <span className="caption text-ink-muted">{ejercicio.body_part_label}</span>
                  )
                }
                esquema={anadidos.get(ejercicio.id)}
                deshabilitada={listado.isPlaceholderData}
                onElegir={() => onElegir(ejercicio)}
              />
            ))}
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
    </>
  );
}
