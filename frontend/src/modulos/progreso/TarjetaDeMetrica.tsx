import type { ReactNode } from "react";

import { Badge } from "@/ds/Badge";
import { TablaDesplazable } from "@/ds/Card";
import { GraficaDeMetrica } from "@/ds/GraficaDeMetrica";
import { Icono } from "@/ds/Icono";

import type { MetricaCalculada } from "./api";

const FILAS_VISIBLES = 10;

function CoberturaBaja({ children }: { children: ReactNode }) {
  return (
    <p className="mb-3 flex items-start gap-2 rounded-lg border border-warning bg-warning-soft px-3 py-2 caption text-warning">
      <Icono nombre="aviso" className="mt-px size-4 shrink-0" />
      <span>{children}</span>
    </p>
  );
}

export function TarjetaDeMetrica({ metrica }: { metrica: MetricaCalculada }) {
  return (
    <div className="insight-card">
      <div className="mb-3 flex items-start justify-between gap-2">
        <h3>{metrica.label}</h3>
        {metrica.value !== null && !metrica.has_no_data && (
          <Badge tono="record">
            <span className="num">{metrica.value}</span>
            {metrica.unit && ` ${metrica.unit}`}
          </Badge>
        )}
      </div>

      {metrica.has_no_data ? (
        <p className="empty-hint">{metrica.empty_hint}</p>
      ) : (
        <>
          {!metrica.is_reliable && (
            <CoberturaBaja>
              Solo el <span className="num">{metrica.coverage_pct}</span>% de los datos necesarios
              está registrado.
              {metrica.needs.length > 0 && ` Para afinarlo, registra ${metrica.needs.join(" y ")}.`}
            </CoberturaBaja>
          )}

          {metrica.notes.map((nota) => (
            <p className="caption text-ink-muted" key={nota}>
              {nota}
            </p>
          ))}
        </>
      )}

      {metrica.series.length > 0 ? (
        <div className="mt-3">
          <GraficaDeMetrica
            serie={metrica.series}
            tipo={metrica.chart === "bar" ? "bar" : "line"}
            unidad={metrica.unit}
          />
        </div>
      ) : metrica.rows.length > 0 ? (
        <div className="mt-3">
          <TablaDesplazable>
            <table className="w-full body-sm">
              <thead>
                <tr className="text-left tag text-ink-muted">
                  {metrica.columns.map((columna, indice) => (
                    <th
                      className={`whitespace-nowrap px-3 py-2 ${indice ? "text-right" : ""}`}
                      key={columna}
                    >
                      {columna}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {metrica.rows.slice(0, FILAS_VISIBLES).map((fila, indice) => (
                  <tr className="hairline border-b" key={indice}>
                    {fila.map((celda, columna) => (
                      <td
                        className={`whitespace-nowrap px-3 py-2 ${columna ? "text-right num" : ""}`}
                        key={columna}
                      >
                        {celda}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </TablaDesplazable>
          {metrica.rows.length > FILAS_VISIBLES && (
            <p className="caption mt-2 text-ink-muted">
              Se muestran {FILAS_VISIBLES} de {metrica.rows.length}.
            </p>
          )}
        </div>
      ) : null}

      <p className="caption mt-3 text-ink-muted">{metrica.description}</p>
    </div>
  );
}
