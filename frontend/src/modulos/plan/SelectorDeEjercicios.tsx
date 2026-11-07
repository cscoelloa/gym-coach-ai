import type { ConfigDeEjercicio } from "@/ds/ConfigDeSeries";
import { Icono } from "@/ds/Icono";
import { SegmentedControl, type Segmento } from "@/ds/SegmentedControl";
import type { Ejercicio } from "@/modulos/ejercicios/api";

import { useRutinasConEjercicios } from "./api";
import { DelCatalogo } from "./DelCatalogo";
import { DeMisRutinas } from "./DeMisRutinas";
import type { BusquedaDeEjercicios, FuenteDeEjercicios } from "./useBusquedaDeEjercicios";

const FUENTES: ReadonlyArray<Segmento<FuenteDeEjercicios>> = [
  { valor: "catalogo", etiqueta: "Catálogo" },
  { valor: "rutinas", etiqueta: "De mis rutinas" },
];

export function SelectorDeEjercicios({
  busqueda,
  excluir,
  onElegir,
  anadidos,
}: {
  busqueda: BusquedaDeEjercicios;
  excluir?: number;
  onElegir: (ejercicio: Ejercicio, config?: ConfigDeEjercicio) => void;
  anadidos: Map<number, string>;
}) {
  const conRutinas = useRutinasConEjercicios(excluir);
  const hayRutinas = Boolean(conRutinas.data?.length);
  const fuente = hayRutinas ? busqueda.fuente : "catalogo";

  return (
    <div>
      {hayRutinas && (
        <SegmentedControl
          opciones={FUENTES}
          valor={fuente}
          onCambio={busqueda.setFuente}
          etiqueta="Origen de los ejercicios"
          className="mb-3 flex w-full"
        />
      )}
      <label className="sr-only" htmlFor="buscar-en-rutina">
        Buscar ejercicio
      </label>
      <div className="sticky -top-1 z-[1] -mt-1 bg-panel pt-1 pb-3">
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
            value={busqueda.texto}
            onChange={(evento) => busqueda.setTexto(evento.target.value)}
            placeholder="Buscar un movimiento…"
            autoComplete="off"
            enterKeyHint="search"
          />
        </div>
      </div>

      {fuente === "rutinas" ? (
        <DeMisRutinas
          excluir={excluir}
          q={busqueda.filtros.q}
          anadidos={anadidos}
          onElegir={onElegir}
        />
      ) : (
        <DelCatalogo busqueda={busqueda} anadidos={anadidos} onElegir={onElegir} />
      )}
    </div>
  );
}
