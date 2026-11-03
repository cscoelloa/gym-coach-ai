import type { CSSProperties, ReactNode } from "react";

export type TonoDeAnillo = "primary" | "data" | "success";

export function Anillo({
  hecho,
  total,
  etiqueta,
  tono = "primary",
  tamano = 96,
  grosor = 10,
  children,
}: {
  hecho: number;
  total: number;
  etiqueta: string;
  tono?: TonoDeAnillo;
  tamano?: number;
  grosor?: number;
  children?: ReactNode;
}) {
  const radio = (tamano - grosor) / 2;
  const circunferencia = 2 * Math.PI * radio;
  const proporcion = total > 0 ? Math.min(1, hecho / total) : 0;
  const cerrado = total > 0 && hecho >= total;

  return (
    <div
      className="goal-ring"
      role="img"
      aria-label={etiqueta}
      style={{ width: tamano, height: tamano }}
    >
      <svg viewBox={`0 0 ${tamano} ${tamano}`} aria-hidden="true">
        <circle
          className="goal-ring-track"
          cx={tamano / 2}
          cy={tamano / 2}
          r={radio}
          strokeWidth={grosor}
        />
        <circle
          className="goal-ring-arc"
          data-tono={cerrado ? "success" : tono}
          cx={tamano / 2}
          cy={tamano / 2}
          r={radio}
          strokeWidth={grosor}
          strokeDasharray={circunferencia}
          style={{ "--resto": circunferencia * (1 - proporcion) } as CSSProperties}
        />
      </svg>
      {children && (
        <span className="goal-ring-center" aria-hidden="true">
          {children}
        </span>
      )}
    </div>
  );
}
