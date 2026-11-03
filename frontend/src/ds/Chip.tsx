import type { ReactNode } from "react";
import { Link } from "react-router";

type Comun = {
  activo?: boolean;
  recuento?: number;
  children: ReactNode;
};

function contenido(children: ReactNode, recuento?: number) {
  return (
    <>
      {children}
      {recuento !== undefined && <span className="chip-count">{recuento}</span>}
    </>
  );
}

export function ChipEnlace({ a, activo, recuento, children }: Comun & { a: string }) {
  return (
    <Link
      to={a}
      className={`chip ${activo ? "chip-on" : ""}`.trim()}
      aria-current={activo ? "true" : undefined}
    >
      {contenido(children, recuento)}
    </Link>
  );
}

export function Chip({ activo, recuento, onClick, children }: Comun & { onClick?: () => void }) {
  return (
    <button
      type="button"
      className={`chip ${activo ? "chip-on" : ""}`.trim()}
      aria-pressed={activo}
      onClick={onClick}
    >
      {contenido(children, recuento)}
    </button>
  );
}

export function FilaDeChips({ children }: { children: ReactNode }) {
  return <div className="chip-row">{children}</div>;
}
