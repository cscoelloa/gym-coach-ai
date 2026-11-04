import { useNavigate, useParams } from "react-router";

import { ErrorDeApi } from "@/api/cliente";
import { Aviso } from "@/ds/Aviso";
import { Badge } from "@/ds/Badge";
import { BarraDeAcciones } from "@/ds/BarraDeAcciones";
import { Button, EnlaceBoton } from "@/ds/Button";
import { Card, PageHeader, Pill } from "@/ds/Card";
import { EmptyState } from "@/ds/EmptyState";
import { Cargando, ErrorDePantalla } from "@/ds/estados";

import { codigoDe, useAceptar, useDescartar, usePropuesta } from "./api";

export function PropuestaDeRutina() {
  const { id = "" } = useParams();
  const generacionId = Number(id);
  const { data, isPending, error, refetch } = usePropuesta(generacionId);
  const aceptar = useAceptar(generacionId);
  const descartar = useDescartar(generacionId);
  const navegar = useNavigate();

  if (isPending) return <Cargando />;

  if (error instanceof ErrorDeApi && error.estado === 404) {
    return (
      <EmptyState
        titulo="Esta propuesta no existe"
        acciones={
          <EnlaceBoton a="/ia/generar/" variante="primary">
            Generar una
          </EnlaceBoton>
        }
      >
        Puede que el enlace sea viejo, o que fuera de otra cuenta.
      </EmptyState>
    );
  }

  if (error || !data) return <ErrorDePantalla onReintentar={refetch} />;

  const total = data.rutinas.reduce((suma, rutina) => suma + rutina.ejercicios.length, 0);
  const faltantes = data.rutinas.flatMap((r) => r.ejercicios).filter((e) => !e.en_catalogo).length;

  return (
    <>
      <PageHeader
        kicker="Propuesta — todavía no guardada"
        titulo={data.nombre}
        entradilla={data.descripcion}
      >
        {data.ya_aplicada && (
          <>
            <Badge tono="done">Ya aplicada</Badge>
            <EnlaceBoton a="/plan/" variante="secondary">
              Ver mi plan
            </EnlaceBoton>
          </>
        )}
      </PageHeader>

      {aceptar.error && (
        <div className="mb-4">
          <Aviso tono={codigoDe(aceptar.error) === "no_aplicable" ? "informacion" : "error"} urgente>
            {aceptar.error instanceof Error
              ? aceptar.error.message
              : "No se ha podido guardar la propuesta."}
          </Aviso>
        </div>
      )}

      {faltantes > 0 && (
        <div className="mb-4">
          <Aviso tono="aviso">
            {faltantes} ejercicio{faltantes === 1 ? "" : "s"} de esta propuesta ya no está
            {faltantes === 1 ? "" : "n"} en el catálogo. Se guardará
            {faltantes === 1 ? "" : "n"} igual, pero conviene revisarlo
            {faltantes === 1 ? "" : "s"} después.
          </Aviso>
        </div>
      )}

      {data.motivo && (
        <section className="insight-card mb-6">
          <h2 className="title-md mb-2">Por qué este plan</h2>
          <p className="body">{data.motivo}</p>
        </section>
      )}

      <section className="mb-6" aria-labelledby="titulo-semana">
        <h2 className="section-kicker px-4" id="titulo-semana">
          Tu semana
        </h2>
        <div className="compact-list">
          {data.semana.map((dia) => (
            <div className="compact-row" key={dia.weekday}>
              <span className="w-24 shrink-0 font-semibold">{dia.etiqueta}</span>
              <span className="min-w-0 flex-1 text-right">
                {dia.rutina ? <Pill activa>{dia.rutina}</Pill> : <Pill>Descanso</Pill>}
              </span>
            </div>
          ))}
        </div>
      </section>

      <section aria-labelledby="titulo-rutinas">
        <h2 className="mb-2 body-sm font-medium text-ink-muted" id="titulo-rutinas">
          {data.rutinas.length} rutina{data.rutinas.length === 1 ? "" : "s"} ·{" "}
          {total} ejercicio{total === 1 ? "" : "s"}
        </h2>

        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          {data.rutinas.map((rutina) => (
            <Card key={rutina.nombre}>
              <div className="mb-3 flex items-center justify-between gap-2">
                <h3>{rutina.nombre}</h3>
                <Badge>{rutina.ejercicios.length} ejercicios</Badge>
              </div>

              <ul className="space-y-2 body-sm">
                {rutina.ejercicios.map((ejercicio) => (
                  <li className="flex items-start gap-3" key={ejercicio.external_id}>
                    {ejercicio.imagen && (
                      <img
                        className="size-12 shrink-0 rounded-lg bg-white object-contain"
                        src={ejercicio.imagen}
                        alt=""
                        loading="lazy"
                      />
                    )}
                    <span className="min-w-0 flex-1">
                      <span className="ex-name block text-[15px]/[20px]">
                        {ejercicio.nombre}
                        {!ejercicio.en_catalogo && (
                          <span className="ml-2">
                            <Badge tono="warn">ya no está</Badge>
                          </span>
                        )}
                      </span>
                      <span className="caption num block text-ink-muted">
                        {ejercicio.series}×{ejercicio.reps_min}-{ejercicio.reps_max} ·{" "}
                        {ejercicio.descanso}s
                      </span>
                    </span>
                  </li>
                ))}
              </ul>
            </Card>
          ))}
        </div>
      </section>

      <Card className="mt-4">
        <p className="caption text-ink-muted">
          Generada con {data.generacion.proveedor} ({data.generacion.modelo}) en{" "}
          <span className="num">{data.generacion.latencia_ms}</span> ms ·{" "}
          <span className="num">
            {data.generacion.tokens_entrada}+{data.generacion.tokens_salida}
          </span>{" "}
          tokens. Al guardarla se creará el programa con sus rutinas y se desactivarán tus otros
          programas. Podrás editarlo todo después.
        </p>
      </Card>

      {!data.ya_aplicada && (
        <BarraDeAcciones>
          <span className="caption text-ink-muted" role="status">
            Nada se guarda hasta que lo aceptes.
          </span>
          <Button
            variante="primary"
            disabled={aceptar.isPending}
            onClick={() =>
              aceptar.mutate(undefined, { onSuccess: () => navegar("/plan/", { replace: true }) })
            }
          >
            {aceptar.isPending ? "Guardando…" : "Guardar y activar"}
          </Button>
          <Button
            variante="secondary"
            disabled={descartar.isPending}
            onClick={() =>
              descartar.mutate(undefined, {
                onSuccess: () => navegar("/ia/generar/", { replace: true }),
              })
            }
          >
            Descartar
          </Button>
        </BarraDeAcciones>
      )}
    </>
  );
}
