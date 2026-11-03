import type { FilaDeSerie } from "../api";

export function textoDeLaSiguiente(fila: FilaDeSerie): string {
  if (!fila.peso) return `Serie ${fila.numero} · ${fila.reps ?? "—"} reps`;
  return `Serie ${fila.numero} · ${fila.peso} kg × ${fila.reps ?? "—"}`;
}

export function textoDeSerie(kg: string, reps: number | null): string {
  return kg ? `${kg}×${reps ?? "—"}` : `${reps ?? "—"} reps`;
}
