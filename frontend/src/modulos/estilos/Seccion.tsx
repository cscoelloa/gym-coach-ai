import type { ReactNode } from "react";

export function Seccion({
  titulo,
  nota,
  children,
}: {
  titulo: string;
  nota?: ReactNode;
  children: ReactNode;
}) {
  return (
    <section className="mb-10">
      <h2 className="mb-1">{titulo}</h2>
      {nota && <p className="body-sm mb-4 text-ink-muted">{nota}</p>}
      {children}
    </section>
  );
}
