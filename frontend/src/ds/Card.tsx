import { Cabecera } from "./Cabecera";
import type { ReactNode } from "react";

export function Card({
  className = "",
  children,
  ...resto
}: { className?: string; children: ReactNode } & React.HTMLAttributes<HTMLElement>) {
  return (
    <section className={`card ${className}`.trim()} {...resto}>
      {children}
    </section>
  );
}

export function PageHeader({
  kicker,
  titulo,
  entradilla,
  children,
}: {
  kicker?: string;
  titulo: string;
  entradilla?: ReactNode;
  children?: ReactNode;
}) {
  return <Cabecera titulo={titulo} kicker={kicker} descripcion={entradilla} acciones={children} />;
}

export function SectionKicker({ children }: { children: ReactNode }) {
  return <p className="section-kicker">{children}</p>;
}

export function Pill({ activa = false, children }: { activa?: boolean; children: ReactNode }) {
  return <span className={`pill ${activa ? "pill-active" : ""}`.trim()}>{children}</span>;
}

export function TablaDesplazable({ children }: { children: ReactNode }) {
  return (
    <div className="table-scroll">
      <table className="data-table">{children}</table>
    </div>
  );
}

export function TablaApilada({ children }: { children: ReactNode }) {
  return (
    <div className="table-scroll">
      <table className="table-stack w-full">{children}</table>
    </div>
  );
}

export function Celda({
  etiqueta,
  className = "",
  children,
}: {
  etiqueta: string;
  className?: string;
  children: ReactNode;
}) {
  return (
    <td data-label={etiqueta} className={className}>
      {children}
    </td>
  );
}
