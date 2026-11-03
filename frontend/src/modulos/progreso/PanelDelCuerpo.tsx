import { Badge } from "@/ds/Badge";
import { BodyMap } from "@/ds/BodyMap";
import { EnlaceBoton } from "@/ds/Button";
import { Card } from "@/ds/Card";
import { GraficaDePeso } from "@/ds/GraficaDePeso";
import { HeatCell } from "@/ds/WeekStrip";

import type { Progreso as DatosDeProgreso } from "./api";

export function PanelDelCuerpo({ data }: { data: DatosDeProgreso }) {
  const mapa = data.mapa_corporal;

  return (
    <div className="grid grid-cols-1 items-start gap-4 xl:grid-cols-2">
      <Card>
        <div className="mb-3 flex items-start justify-between gap-2">
          <div>
            <p className="section-kicker">Tendencia</p>
            <h2>Peso corporal</h2>
          </div>
          <EnlaceBoton a="/peso/" variante="secondary" tamano="sm">
            Registrar
          </EnlaceBoton>
        </div>
        {data.peso.serie ? (
          <GraficaDePeso serie={data.peso.serie} />
        ) : (
          <p className="empty-hint">Con dos registros o más verás aquí la tendencia y tu meta.</p>
        )}
      </Card>

      <Card>
        <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="section-kicker">Reparto</p>
            <h2>Qué has entrenado</h2>
            <p className="caption mt-1 text-ink-muted">
              Esta semana, en series efectivas. Cada serie suma entera a su músculo objetivo y
              media a los que ayudan.
            </p>
          </div>
          <Badge>
            <span className="num">{mapa.total_series}</span> series
          </Badge>
        </div>

        <div className="grid grid-cols-1 gap-5 sm:grid-cols-[minmax(0,1fr)_minmax(0,1.1fr)] sm:items-center">
          <BodyMap niveles={mapa.niveles} />

          <div>
            <p className="section-kicker">Intensidad</p>
            <ul className="space-y-1">
              {[
                [0, "sin tocar"],
                [1, "menos de 5 series"],
                [2, "5 a 9"],
                [3, "10 a 14 — la referencia habitual para crecer"],
                [4, "15 o más"],
              ].map(([nivel, texto]) => (
                <li className="body-sm flex items-center gap-2" key={nivel}>
                  <HeatCell nivel={nivel as 0 | 1 | 2 | 3 | 4} />
                  <span className="text-ink-muted">{texto}</span>
                </li>
              ))}
            </ul>

            <p className="empty-hint mt-4">
              Los tonos son cortes fijos y no cuartiles de tu historial: así una semana floja se ve
              floja en vez de reescalarse para parecer normal.
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
}
