import { EnlaceBoton } from "@/ds/Button";
import { EmptyState } from "@/ds/EmptyState";
import { ErrorDePantalla } from "@/ds/estados";
import { Icono } from "@/ds/Icono";

import { useMisMetricas } from "./api";
import { TarjetaDeMetrica } from "./TarjetaDeMetrica";

export function PanelDeMetricas() {
  const metricas = useMisMetricas();

  if (metricas.isPending) {
    return <div className="min-h-64" aria-busy="true" aria-label="Calculando métricas" />;
  }
  if (metricas.error || !metricas.data) {
    return <ErrorDePantalla onReintentar={metricas.refetch} />;
  }
  if (metricas.data.length === 0) {
    return (
      <EmptyState
        titulo="No tienes ninguna métrica seleccionada"
        glifo={<Icono nombre="progreso" />}
        acciones={
          <EnlaceBoton a="/metricas/" variante="primary">
            Ir al catálogo
          </EnlaceBoton>
        }
      >
        Elige las que quieras seguir y aparecerán aquí.
      </EmptyState>
    );
  }

  return (
    <>
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {metricas.data.map((metrica) => (
          <TarjetaDeMetrica key={metrica.key} metrica={metrica} />
        ))}
      </div>
      <p className="body-sm mt-6 flex items-center gap-2 text-ink-muted">
        <Icono nombre="informacion" className="size-4 shrink-0" />
        Todas las cifras las calcula el servidor a partir de lo que has registrado.
      </p>
    </>
  );
}
