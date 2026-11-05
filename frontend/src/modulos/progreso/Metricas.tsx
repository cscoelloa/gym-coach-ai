import { useState } from "react";
import { useNavigate } from "react-router";

import { Badge } from "@/ds/Badge";
import { BarraDeAcciones } from "@/ds/BarraDeAcciones";
import { Button, EnlaceBoton } from "@/ds/Button";
import { Card, PageHeader } from "@/ds/Card";
import { EmptyState } from "@/ds/EmptyState";
import { Cargando, ErrorDePantalla } from "@/ds/estados";

import { useCatalogoDeMetricas, useGuardarMetricas } from "./api";

export function Metricas() {
  const { data, isPending, error, refetch } = useCatalogoDeMetricas();
  const guardar = useGuardarMetricas();
  const navegar = useNavigate();
  const [elegidas, setElegidas] = useState<Set<string> | null>(null);

  if (isPending) return <Cargando />;
  if (error || !data) return <ErrorDePantalla onReintentar={refetch} />;

  const marcadas = elegidas ?? new Set(data.filter((m) => m.visible).map((m) => m.key));

  function alternar(key: string) {
    const siguiente = new Set(marcadas);
    if (siguiente.has(key)) siguiente.delete(key);
    else siguiente.add(key);
    setElegidas(siguiente);
  }

  const categorias: { clave: string; etiqueta: string; metricas: typeof data }[] = [];
  for (const metrica of data) {
    let grupo = categorias.find((c) => c.clave === metrica.category);
    if (!grupo) {
      grupo = { clave: metrica.category, etiqueta: metrica.category_label, metricas: [] };
      categorias.push(grupo);
    }
    grupo.metricas.push(metrica);
  }

  return (
    <>
      <PageHeader
        kicker="Tu panel"
        titulo="Catálogo de métricas"
        hero="data"
        entradilla="Elige cuáles quieres ver en tu panel de progreso."
      >
        <EnlaceBoton a="/progreso/?vista=metricas" variante="secondary">
          Ver mi panel
        </EnlaceBoton>
      </PageHeader>

      {categorias.length === 0 ? (
        <EmptyState titulo="No hay métricas en el catálogo">
          Ejecuta <code className="surface-2 rounded px-1.5 py-0.5">python manage.py sync_metrics</code>.
        </EmptyState>
      ) : (
        <>
          <div className="space-y-4">
            {categorias.map((categoria) => (
              <Card key={categoria.clave}>
                <div className="mb-3 flex items-center justify-between gap-2">
                  <h2>{categoria.etiqueta}</h2>
                  <Badge>{categoria.metricas.length}</Badge>
                </div>

                <div className="@container">
                <div className="grid grid-cols-1 gap-2 @lg:grid-cols-2">
                  {categoria.metricas.map((metrica) => (
                    <label
                      className="hairline flex cursor-pointer items-start gap-3 rounded-lg border p-3 transition-colors hover:surface-2 has-[:checked]:border-primary has-[:checked]:bg-primary-soft"
                      key={metrica.key}
                    >
                      <input
                        className="mt-0.5 shrink-0"
                        type="checkbox"
                        checked={marcadas.has(metrica.key)}
                        onChange={() => alternar(metrica.key)}
                      />
                      <span className="min-w-0">
                        <span className="flex flex-wrap items-center gap-2">
                          <span className="title-sm text-ink">{metrica.label}</span>
                          {metrica.unit && <Badge>{metrica.unit}</Badge>}
                        </span>
                        <span className="caption mt-1 block text-ink-muted">
                          {metrica.description}
                        </span>
                      </span>
                    </label>
                  ))}
                </div>
                </div>
              </Card>
            ))}
          </div>

          <BarraDeAcciones>
            <Button
              variante="primary"
              disabled={guardar.isPending}
              onClick={() =>
                guardar.mutate([...marcadas], {
                  onSuccess: () => navegar("/progreso/?vista=metricas"),
                })
              }
            >
              {guardar.isPending ? "Guardando…" : "Guardar mi panel"}
            </Button>
            <span className="caption text-ink-muted" role="status">
              <span className="num">{marcadas.size}</span> de{" "}
              <span className="num">{data.length}</span> seleccionadas
            </span>
          </BarraDeAcciones>
        </>
      )}
    </>
  );
}
