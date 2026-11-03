import { Link } from "react-router";

import { Card, TablaApilada, Celda } from "@/ds/Card";
import { EmptyState } from "@/ds/EmptyState";

import type { Analisis } from "./api";

export function PanelDeCambios({ analisis }: { analisis: Analisis }) {
  if (!(analisis.proposed_changes.length > 0)) {
    return (
      <EmptyState titulo="Sin cambios que proponer">
        Por ahora tu rutina encaja con lo que dicen tus métricas.
      </EmptyState>
    );
  }

  return (
    <Card>
      <h2 className="mb-3">Cambios propuestos a tu rutina</h2>
      <TablaApilada>
        <thead>
          <tr className="text-left tag text-ink-muted">
            <th className="px-3 py-2">Dónde</th>
            <th className="px-3 py-2">Qué cambiar</th>
            <th className="px-3 py-2">Por qué</th>
          </tr>
        </thead>
        <tbody>
          {analisis.proposed_changes.map((cambio) => (
            <tr className="hairline" key={`${cambio.target}-${cambio.change}`}>
              <Celda etiqueta="Dónde" className="font-medium md:font-normal">
                {cambio.target}
              </Celda>
              <Celda etiqueta="Qué cambiar">{cambio.change}</Celda>
              <Celda etiqueta="Por qué" className="text-ink-muted">
                {cambio.reason}
              </Celda>
            </tr>
          ))}
        </tbody>
      </TablaApilada>
      <p className="caption mt-3 text-ink-muted">
        Aplícalos tú desde <Link to="/plan/">tus rutinas</Link>: así decides qué
        aceptar y qué no.
      </p>
    </Card>
  );
}
