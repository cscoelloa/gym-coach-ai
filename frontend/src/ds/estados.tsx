import { onlineManager } from "@tanstack/react-query";
import { useEffect } from "react";

import { ErrorDeApi } from "@/api/cliente";
import { useEnLinea } from "@/lib/conexion";

import { Button } from "./Button";
import { EmptyState } from "./EmptyState";
import { Icono } from "./Icono";

export function Cargando() {
  const enLinea = useEnLinea();

  if (!enLinea) {
    return (
      <EmptyState titulo="Sin conexión" glifo={<Icono nombre="sinConexion" className="size-6" />}>
        Esta pantalla todavía no se había cargado. Se cargará sola en cuanto vuelva la red.
      </EmptyState>
    );
  }

  return (
    <div className="min-h-[60vh] space-y-4" aria-busy="true" aria-label="Cargando">
      <div className="skeleton h-3 w-28" />
      <div className="skeleton h-8 w-48" />
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <div className="skeleton h-24 rounded-xl" />
        <div className="skeleton h-24 rounded-xl" />
        <div className="skeleton hidden h-24 rounded-xl lg:block" />
        <div className="skeleton hidden h-24 rounded-xl lg:block" />
      </div>
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="skeleton h-52 rounded-2xl" />
        <div className="skeleton h-52 rounded-2xl" />
      </div>
    </div>
  );
}

export function ErrorDePantalla({ onReintentar }: { onReintentar: () => void }) {
  return (
    <EmptyState
      titulo="No se han podido cargar los datos"
      acciones={
        <Button variante="primary" tamano="sm" onClick={onReintentar}>
          Reintentar
        </Button>
      }
    >
      Puede ser la conexión. Tus datos están a salvo.
    </EmptyState>
  );
}

export function SinConexion({
  error,
  onReintentar,
}: {
  error?: unknown;
  onReintentar: () => void;
}) {
  const sinRed =
    (error instanceof ErrorDeApi && error.estado === 0) || !onlineManager.isOnline();

  useEffect(
    () => onlineManager.subscribe((enLinea) => enLinea && onReintentar()),
    [onReintentar],
  );

  return (
    <main className="flex min-h-dvh flex-col items-center justify-center gap-5 bg-surface-000 px-6 text-center">
      <span className="flex size-14 items-center justify-center rounded-full bg-surface-200 text-ink-muted">
        <Icono nombre="sinConexion" className="size-7" />
      </span>
      <div className="max-w-sm">
        <h1 className="title-lg">{sinRed ? "Sin conexión" : "No se pudo conectar"}</h1>
        <p className="body mt-2 text-ink-muted">
          {sinRed
            ? "Para ver tus datos y registrar series hace falta red. Tus datos están a salvo."
            : "El servidor no responde ahora mismo. Tus datos están a salvo."}
        </p>
      </div>
      <Button variante="primary" onClick={onReintentar}>
        <Icono nombre="recargar" className="size-5" />
        Reintentar
      </Button>
    </main>
  );
}
