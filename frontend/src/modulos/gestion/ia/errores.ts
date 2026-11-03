import { ErrorDeApi } from "@/api/cliente";

export function erroresDe(error: unknown, campo: string): string[] | undefined {
  return error instanceof ErrorDeApi ? error.porCampo[campo] : undefined;
}

export function mensajeDe(error: unknown): string {
  return error instanceof Error ? error.message : "No se ha podido completar la operación.";
}
