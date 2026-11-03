import type { CSSProperties, ReactNode } from "react";

const CIRCUNFERENCIA = 226.19;

export function formatearCuenta(segundos: number): string {
  const positivos = Math.max(0, segundos);
  const minutos = Math.floor(positivos / 60);
  const resto = positivos % 60;
  return `${minutos}:${String(resto).padStart(2, "0")}`;
}

export function RestTimer({
  restante,
  total,
  siguiente,
  compacto = false,
  children,
}: {
  restante: number;
  total: number;
  siguiente?: string;
  compacto?: boolean;
  children?: ReactNode;
}) {
  const consumido = total > 0 ? Math.min(1, Math.max(0, 1 - restante / total)) : 1;
  const resto = CIRCUNFERENCIA * consumido;

  return (
    <div className={compacto ? "rest-timer-compact" : "rest-timer"}>
      <div className="rest-ring">
        <svg width="88" height="88" viewBox="0 0 88 88" aria-hidden="true">
          <circle className="rest-ring-track" cx="44" cy="44" r="36" />
          <circle
            className="rest-ring-arc"
            cx="44"
            cy="44"
            r="36"
            strokeDasharray={CIRCUNFERENCIA}
            style={{ "--resto": resto } as CSSProperties}
          />
        </svg>
        <span className="rest-count" role="timer" aria-live="off">
          {formatearCuenta(restante)}
        </span>
      </div>

      {compacto ? (
        <>
          <div className="flex min-w-0 flex-1 flex-col">
            <span className="caption text-data">Descanso</span>
            {siguiente && <span className="rest-next truncate">{siguiente}</span>}
          </div>
          {children && <div className="flex shrink-0 gap-1.5">{children}</div>}
        </>
      ) : (
        <div className="flex min-w-0 flex-col gap-2">
          <span className="rest-label">Descanso</span>
          {siguiente && <span className="rest-next">{siguiente}</span>}
          {children && <div className="mt-1 flex gap-2">{children}</div>}
        </div>
      )}
    </div>
  );
}
