import { Link } from "react-router";

import { Aviso } from "@/ds/Aviso";
import { Icono } from "@/ds/Icono";
import { MediaDeEjercicio } from "@/ds/MediaDeEjercicio";
import { Panel } from "@/ds/Panel";
import { useEjercicio } from "@/modulos/ejercicios/api";

export function ComoSeHace({ slug, nombre, onCerrar }: { slug: string; nombre: string; onCerrar: () => void }) {
  const { data: ejercicio, isPending, error } = useEjercicio(slug);

  return (
    <Panel titulo="Cómo se hace" onCerrar={onCerrar}>
      <p className="title-sm mb-4 capitalize">{nombre}</p>
      {isPending ? (
        <div className="min-h-64" aria-busy="true" aria-label="Cargando" />
      ) : error || !ejercicio ? (
        <Aviso tono="error">No se pudo cargar. Inténtalo otra vez.</Aviso>
      ) : (
        <div className="grid grid-cols-1 gap-5 md:grid-cols-[minmax(0,1fr)_minmax(0,1fr)] md:items-start">
          <MediaDeEjercicio
            imagen={ejercicio.image}
            animacion={ejercicio.animation}
            atribucion={ejercicio.attribution}
            tamano="lg"
          />
          <div>
            {ejercicio.steps.length ? (
              <ol className="steps-list">
                {ejercicio.steps.map((paso, indice) => (
                  <li key={indice}>{paso}</li>
                ))}
              </ol>
            ) : (
              <p className="empty-hint">Sin instrucciones.</p>
            )}
            <Link className="mt-4 inline-flex items-center gap-1 font-semibold" to={`/ejercicios/${slug}/`}>
              Ver la ficha completa
              <Icono nombre="chevronDerecha" className="size-4" />
            </Link>
          </div>
        </div>
      )}
    </Panel>
  );
}
