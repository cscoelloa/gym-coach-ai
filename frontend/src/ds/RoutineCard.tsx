import type { ReactNode } from "react";

export type EjercicioDeRutina = {
  nombre: string;
  series?: string;
};

export function RoutineCard({
  nombre,
  dias,
  insignia,
  ejercicios,
  maximo = 3,
  children,
}: {
  nombre: string;
  dias?: string;
  insignia?: ReactNode;
  ejercicios: readonly EjercicioDeRutina[];
  maximo?: number;
  children?: ReactNode;
}) {
  const visibles = ejercicios.slice(0, maximo);
  const ocultos = ejercicios.length - visibles.length;

  return (
    <article className="routine-panel">
      <div className="routine-top">
        <div className="min-w-0">
          <span className="routine-name">{nombre}</span>
          {dias && <span className="routine-days block">{dias}</span>}
        </div>
        {insignia}
      </div>

      <div className="routine-list">
        {visibles.map((ejercicio) => (
          <div className="routine-item" key={ejercicio.nombre}>
            <b>{ejercicio.nombre}</b>
            <span>{ejercicio.series ?? ""}</span>
          </div>
        ))}
        {ocultos > 0 && (
          <div className="routine-item">
            <b>
              +{ocultos} ejercicio{ocultos === 1 ? "" : "s"}
            </b>
            <span />
          </div>
        )}
        {ejercicios.length === 0 && (
          <div className="routine-item">
            <b className="text-ink-muted">Sin ejercicios todavía</b>
            <span />
          </div>
        )}
      </div>

      {children && <div className="routine-foot">{children}</div>}
    </article>
  );
}
