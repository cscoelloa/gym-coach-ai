import { Badge } from "@/ds/Badge";
import { Card, TablaApilada, Celda } from "@/ds/Card";
import { EmptyState } from "@/ds/EmptyState";

import type { Analisis } from "./api";

export function PanelDeEstancamientos({ analisis }: { analisis: Analisis }) {
  if (!(analisis.stalled.length || analisis.patterns.length)) {
    return (
      <EmptyState titulo="Nada estancado">
        La IA no ha visto ningún ejercicio parado ni ningún patrón que señalar.
      </EmptyState>
    );
  }

  return (
    <div className="grid grid-cols-1 items-start gap-4 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]">
      {analisis.stalled.length > 0 && (
        <Card>
          <div className="mb-3 flex items-center justify-between gap-2">
            <h2>Ejercicios estancados</h2>
            <Badge tono="warn">{analisis.stalled.length}</Badge>
          </div>
          <TablaApilada>
            <thead>
              <tr className="text-left tag text-ink-muted">
                <th className="px-3 py-2">Ejercicio</th>
                <th className="px-3 py-2 md:text-right">Semanas</th>
                <th className="px-3 py-2">Causa probable</th>
              </tr>
            </thead>
            <tbody>
              {analisis.stalled.map((item) => (
                <tr className="hairline" key={item.exercise}>
                  <Celda etiqueta="Ejercicio" className="font-medium md:font-normal">
                    {item.exercise}
                  </Celda>
                  <Celda etiqueta="Semanas" className="num md:text-right">
                    {item.weeks_stalled}
                  </Celda>
                  <Celda etiqueta="Causa probable" className="text-ink-muted">
                    {item.likely_cause}
                  </Celda>
                </tr>
              ))}
            </tbody>
          </TablaApilada>
        </Card>
      )}

      {analisis.patterns.length > 0 && (
        <Card>
          <h2 className="mb-2">Patrones detectados</h2>
          <ul className="list-disc space-y-1 pl-5 body-sm">
            {analisis.patterns.map((patron) => (
              <li key={patron}>{patron}</li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  );
}
