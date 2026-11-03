import type { ReactNode } from "react";

export type TonoDeBadge = "record" | "done" | "warn" | "down" | "info" | "neutral";

export function Badge({
  tono = "neutral",
  className = "",
  children,
}: {
  tono?: TonoDeBadge;
  className?: string;
  children: ReactNode;
}) {
  return <span className={`badge badge-${tono} ${className}`.trim()}>{children}</span>;
}
