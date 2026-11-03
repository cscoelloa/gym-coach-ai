import { Card } from "@/ds/Card";

import type { Analisis } from "./api";

export function PanelDeLectura({ analisis }: { analisis: Analisis }) {
  return (
    <div className="grid grid-cols-1 items-start gap-4 lg:grid-cols-2">
      <div className="space-y-4">
        <Card className="insight-card">
          <h2 className="mb-2">Resumen</h2>
          <p>{analisis.summary}</p>
        </Card>

        {analisis.data_caveats.length > 0 && (
          <Card>
            <h2 className="mb-1">Lo que no se puede afirmar todavía</h2>
            <p className="caption mb-2 text-ink-muted">
              Faltan datos para sostener estas conclusiones. Registrar lo que se indica
              las desbloquea.
            </p>
            <ul className="list-disc space-y-1 pl-5 body-sm">
              {analisis.data_caveats.map((aviso) => (
                <li key={aviso}>{aviso}</li>
              ))}
            </ul>
          </Card>
        )}
      </div>

      {analisis.recommendations.length > 0 && (
        <Card className="card-accent">
          <h2 className="mb-3">Recomendaciones</h2>
          <ol className="steps-list">
            {analisis.recommendations.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ol>
        </Card>
      )}
    </div>
  );
}
