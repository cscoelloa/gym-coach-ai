import { useState } from "react";

import { Button } from "@/ds/Button";
import { Card, Celda, TablaApilada } from "@/ds/Card";
import { Confirmacion } from "@/ds/Confirmacion";
import { EmptyState } from "@/ds/EmptyState";
import { ErrorDePantalla } from "@/ds/estados";
import { Icono } from "@/ds/Icono";
import { Paginacion } from "@/ds/Paginacion";

import { useBorrarPeso, useRegistrosDePeso } from "./api";
import { comoFecha, FECHA_CORTA } from "./fechas";

export function HistorialDePeso() {
  const [pagina, setPagina] = useState(1);
  const registros = useRegistrosDePeso(pagina);
  const borrar = useBorrarPeso();
  const [porBorrar, setPorBorrar] = useState<{ id: number; fecha: string } | null>(null);

  if (registros.isPending) return <div className="min-h-64" aria-busy="true" aria-label="Cargando" />;
  if (registros.error) return <ErrorDePantalla onReintentar={registros.refetch} />;

  const filas = registros.data.results;

  return (
    <Card>
      {filas.length ? (
        <TablaApilada>
          <thead>
            <tr className="tag text-left text-ink-subtle">
              <th className="px-3 py-2">Fecha</th>
              <th className="px-3 py-2 text-right">Peso</th>
              <th className="px-3 py-2 text-right">Grasa</th>
              <th className="px-3 py-2">Notas</th>
              <th className="px-3 py-2">
                <span className="sr-only">Acciones</span>
              </th>
            </tr>
          </thead>
          <tbody className="body-sm">
            {filas.map((fila) => (
              <tr className="border-b border-line" key={fila.id}>
                <Celda etiqueta="Fecha" className="font-medium md:font-normal">
                  {FECHA_CORTA.format(comoFecha(fila.date))}
                </Celda>
                <Celda etiqueta="Peso" className="num md:text-right">
                  {fila.weight_kg} kg
                </Celda>
                <Celda etiqueta="Grasa" className="num md:text-right">
                  {fila.body_fat_pct ? `${fila.body_fat_pct} %` : "—"}
                </Celda>
                <Celda etiqueta="Notas" className="text-ink-muted">
                  {fila.notes || "—"}
                </Celda>
                <Celda etiqueta="" className="md:text-right">
                  <Button
                    variante="danger"
                    tamano="sm"
                    disabled={borrar.isPending}
                    onClick={() =>
                      setPorBorrar({ id: fila.id, fecha: FECHA_CORTA.format(comoFecha(fila.date)) })
                    }
                  >
                    <span aria-hidden="true">×</span>
                    <span className="sr-only">
                      Borrar el registro del {FECHA_CORTA.format(comoFecha(fila.date))}
                    </span>
                    <span className="md:hidden">Borrar</span>
                  </Button>
                </Celda>
              </tr>
            ))}
          </tbody>
        </TablaApilada>
      ) : (
        <EmptyState titulo="Sin registros" glifo={<Icono nombre="bascula" />}>
          Anota tu peso de hoy: con dos ya hay tendencia que mirar.
        </EmptyState>
      )}

      <Paginacion
        pagina={pagina}
        total={registros.data.total_pages}
        hayAnterior={Boolean(registros.data.previous)}
        haySiguiente={Boolean(registros.data.next)}
        onCambio={setPagina}
      />

      {porBorrar && (
        <Confirmacion
          titulo="Borrar el registro"
          mensaje={`Se borrará el peso del ${porBorrar.fecha}. No se puede deshacer.`}
          confirmar="Sí, borrar"
          onConfirmar={() => {
            borrar.mutate(porBorrar.id);
            setPorBorrar(null);
          }}
          onCancelar={() => setPorBorrar(null)}
        />
      )}
    </Card>
  );
}
