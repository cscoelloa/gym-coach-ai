import type { ReactNode } from "react";

export function EmptyState({
  titulo,
  glifo,
  children,
  acciones,
}: {
  titulo: string;
  glifo?: ReactNode;
  children?: ReactNode;
  acciones?: ReactNode;
}) {
  return (
    <div className="empty-state">
      {glifo && (
        <span className="empty-glyph" aria-hidden="true">
          {glifo}
        </span>
      )}
      <span className="empty-title">{titulo}</span>
      {children && <p>{children}</p>}
      {acciones && <div className="flex flex-wrap justify-center gap-2">{acciones}</div>}
    </div>
  );
}
