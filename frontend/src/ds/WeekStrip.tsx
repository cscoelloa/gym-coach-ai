export type DiaDeLaSemana = {
  inicial: string;
  numero: number;
  hoy?: boolean;
  entrenado?: boolean;
  planificado?: boolean;
  futuro?: boolean;
};

export function WeekStrip({ dias }: { dias: readonly DiaDeLaSemana[] }) {
  return (
    <div className="week-strip">
      {dias.map((dia, indice) => (
        <div
          key={`${dia.inicial}-${dia.numero}-${indice}`}
          className={`week-day ${dia.hoy ? "week-day-today" : ""}`.trim()}
        >
          <span className={`tag ${dia.hoy ? "" : "text-ink-subtle"}`.trim()}>{dia.inicial}</span>
          <span className={`metric-sm ${dia.futuro && !dia.hoy ? "opacity-40" : ""}`.trim()}>
            {dia.numero}
          </span>

          {dia.entrenado ? (
            <>
              <span
                className={`size-1.5 rounded-full ${dia.hoy ? "bg-on-primary" : "bg-primary"}`}
              />
              <span className="sr-only">entrenado</span>
            </>
          ) : dia.planificado ? (
            <>
              <span
                className={`size-1.5 rounded-full border ${
                  dia.hoy ? "border-on-primary" : "border-line-strong"
                }`}
              />
              <span className="sr-only">planificado</span>
            </>
          ) : (
            <span className="size-1.5" />
          )}
        </div>
      ))}
    </div>
  );
}

export function HeatCell({ nivel, titulo }: { nivel: 0 | 1 | 2 | 3 | 4; titulo?: string }) {
  return <span className={`heat-cell heat-${nivel}`} title={titulo} />;
}
