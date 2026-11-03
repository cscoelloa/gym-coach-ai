import { Badge } from "@/ds/Badge";
import { Card, PageHeader } from "@/ds/Card";
import { Cargando, ErrorDePantalla } from "@/ds/estados";
import { Pestanas, useVista } from "@/ds/Pestanas";
import { NotaDeStat, StatTile } from "@/ds/StatTile";

import { useCambiarMetrica, useCatalogoDeGestion, useMetricasDeGestion } from "./api";

const VISTAS = ["ejercicios", "metricas"] as const;

export function CatalogoYMetricas() {
  const [vista, setVista] = useVista(VISTAS);
  const catalogo = useCatalogoDeGestion();
  const metricas = useMetricasDeGestion();
  const cambiar = useCambiarMetrica();

  if (catalogo.isPending || metricas.isPending) return <Cargando />;
  if (catalogo.error || !catalogo.data || metricas.error || !metricas.data) {
    return <ErrorDePantalla onReintentar={() => void catalogo.refetch()} />;
  }

  const mayor = Math.max(...catalogo.data.por_zona.map((z) => z.n), 1);

  return (
    <>
      <PageHeader
        kicker="Contenido"
        titulo="Catálogo y métricas"
        entradilla="Qué ejercicios hay importados y qué se calcula para quién."
      />

      <Pestanas
        etiqueta="Qué catálogo"
        valor={vista}
        onCambio={setVista}
        opciones={[
          { valor: "ejercicios", etiqueta: "De ejercicios" },
          { valor: "metricas", etiqueta: "De métricas" },
        ]}
      >
        {vista === "ejercicios" && (
          <>
          <div className="mb-5 grid grid-cols-2 gap-3 lg:grid-cols-4">
            <StatTile etiqueta="Ejercicios" valor={catalogo.data.total}>
              <NotaDeStat>del catálogo global</NotaDeStat>
            </StatTile>
            <StatTile etiqueta="Con imagen" valor={catalogo.data.con_imagen}>
              {catalogo.data.total > 0 && (
                <NotaDeStat>
                  {Math.round((catalogo.data.con_imagen / catalogo.data.total) * 100)}%
                </NotaDeStat>
              )}
            </StatTile>
            <StatTile etiqueta="Propios" valor={catalogo.data.propios || null} vacio="Ninguno.">
              <NotaDeStat>creados por usuarios</NotaDeStat>
            </StatTile>
            <StatTile etiqueta="Grupos musculares" valor={catalogo.data.musculos} />
          </div>

          <Card className="mb-4">
            <h2 className="mb-1">Reparto por zona</h2>
            <p className="caption mb-3 text-ink-muted">
              Una zona con muy pocos ejercicios limita lo que la IA puede proponer para ella.
            </p>
            <ul className="space-y-2">
              {catalogo.data.por_zona.map((zona) => (
                <li className="flex items-center gap-3" key={zona.valor}>
                  <span className="w-28 shrink-0 body-sm">{zona.etiqueta}</span>
                  <span
                    className="h-2 rounded-full bg-data"
                    style={{ width: `${Math.max(2, (zona.n / mayor) * 100)}%` }}
                  />
                  <span className="num shrink-0 caption text-ink-muted">{zona.n}</span>
                </li>
              ))}
            </ul>
            <p className="empty-hint mt-4">
              Se importan con <code className="surface-2 rounded px-1.5 py-0.5">import_catalog</code> y
              no se editan aquí: un cambio a mano se perdería en la siguiente importación.
            </p>
          </Card>
          </>
        )}

        {vista === "metricas" && (
          <Card>
            <h2 className="mb-1">Métricas</h2>
            <p className="caption mb-3 text-ink-muted">
              Las filas las crea <code className="surface-2 rounded px-1.5 py-0.5">sync_metrics</code>{" "}
              desde el código. Lo editable son los tres interruptores.
            </p>

            <div className="space-y-2">
              {metricas.data.map((metrica) => (
                <div className="surface-2 rounded-md p-3" key={metrica.id}>
                  <div className="mb-2 flex flex-wrap items-start justify-between gap-2">
                    <div className="min-w-0">
                      <span className="title-sm block">{metrica.label}</span>
                      <span className="caption text-ink-muted">
                        {metrica.category_label}
                        {metrica.unit && ` · ${metrica.unit}`}
                      </span>
                    </div>
                    <Badge tono={metrica.en_paneles ? "info" : "neutral"}>
                      en <span className="num">{metrica.en_paneles}</span> panel
                      {metrica.en_paneles === 1 ? "" : "es"}
                    </Badge>
                  </div>

                  <div className="flex flex-wrap gap-4">
                    {(
                      [
                        ["is_active", "Se calcula"],
                        ["send_to_ai", "Va al análisis"],
                        ["default_visible", "Activa por defecto"],
                      ] as const
                    ).map(([campo, etiqueta]) => (
                      <label className="flex cursor-pointer items-center gap-2 body-sm" key={campo}>
                        <input
                          type="checkbox"
                          checked={metrica[campo]}
                          disabled={cambiar.isPending}
                          onChange={(evento) =>
                            cambiar.mutate({ id: metrica.id, [campo]: evento.target.checked })
                          }
                        />
                        {etiqueta}
                      </label>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </Card>
        )}
      </Pestanas>
    </>
  );
}
