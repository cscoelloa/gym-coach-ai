export function ProgressBar({
  etiqueta,
  hecho,
  total,
  unidad,
  marca = false,
}: {
  etiqueta: string;
  hecho: number;
  total: number;
  unidad?: string;
  marca?: boolean;
}) {
  const avance = total > 0 ? Math.min(100, Math.round((hecho / total) * 100)) : 0;

  return (
    <div className={`progress ${marca ? "progress-brand" : ""}`.trim()}>
      <div className="progress-head">
        <span>{etiqueta}</span>
        <span className="progress-value">
          {hecho} / {total}
          {unidad ? ` ${unidad}` : ""}
        </span>
      </div>
      <div
        className="progress-track"
        role="progressbar"
        aria-valuenow={hecho}
        aria-valuemin={0}
        aria-valuemax={total}
        aria-label={etiqueta}
      >
        <div className="progress-fill" style={{ "--avance": `${avance}%` } as React.CSSProperties} />
      </div>
    </div>
  );
}
