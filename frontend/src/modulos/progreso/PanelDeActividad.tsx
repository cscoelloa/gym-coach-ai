import { CalendarioDeActividad } from "@/ds/CalendarioDeActividad";
import { Card } from "@/ds/Card";

import type { Progreso as DatosDeProgreso } from "./api";

export function PanelDeActividad({ data }: { data: DatosDeProgreso }) {
  const masSesiones = Math.max(...data.por_dia_de_semana.map((d) => d.sesiones), 1);

  return (
    <div className="grid grid-cols-1 items-start gap-4 xl:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)]">
      <section className="insight-card" aria-labelledby="titulo-calendario">
        <div className="mb-4">
          <p className="section-kicker">Consistencia</p>
          <h2 id="titulo-calendario">Mapa de actividad</h2>
          <p className="caption mt-1 text-ink-muted">
            Últimos 12 meses, medidos por tiempo entrenado.
          </p>
        </div>
        <CalendarioDeActividad semanas={data.calendario.semanas} niveles={data.calendario.niveles} />
      </section>

      <Card>
        <div className="mb-4">
          <p className="section-kicker">Costumbre</p>
          <h2>Cuándo entrenas</h2>
          <p className="caption mt-1 text-ink-muted">
            Sesiones por día de la semana en las últimas {data.semanas_por_dia} semanas.
          </p>
        </div>

        <ul className="flex items-end justify-between gap-2" aria-label="Sesiones por día">
          {data.por_dia_de_semana.map((dia) => (
            <li className="flex min-w-0 flex-1 flex-col items-center gap-1" key={dia.weekday}>
              <span className="metric-sm text-ink-muted">{dia.sesiones}</span>
              <span
                className={`w-full rounded-t-sm ${dia.sesiones ? "bg-data" : "bg-track"}`}
                style={{ height: `${Math.max(4, (dia.sesiones / masSesiones) * 96)}px` }}
              />
              <span className="tag text-ink-subtle">{dia.inicial}</span>
            </li>
          ))}
        </ul>
      </Card>
    </div>
  );
}
