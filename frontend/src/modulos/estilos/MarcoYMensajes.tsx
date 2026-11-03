import { useState } from "react";

import { Aviso } from "@/ds/Aviso";
import { Button } from "@/ds/Button";
import { Card } from "@/ds/Card";
import { Icono } from "@/ds/Icono";
import { Placa } from "@/ds/Marca";
import { Panel } from "@/ds/Panel";

import { Seccion } from "./Seccion";

export function MarcoYMensajes() {
  const [hoja, setHoja] = useState(false);

  return (
    <>
      <Seccion
        titulo="El marco y la PWA"
        nota="La barra superior y la de pestañas son de cristal: el contenido pasa por detrás difuminado, y si el teléfono pide menos transparencia se pintan opacas. Las hojas suben desde abajo en el teléfono y se centran en escritorio."
      >
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <Card className="space-y-4">
            <p className="section-kicker">La placa de la marca</p>
            <div className="flex items-end gap-4">
              <Placa className="size-8 rounded-[9px]" />
              <Placa />
              <Placa className="size-16 rounded-[18px]" />
              <Placa className="size-20 rounded-[22px]" />
            </div>
            <p className="body-sm text-ink-muted">
              El mismo dibujo que el icono de la aplicación instalada.
            </p>
            <Button onClick={() => setHoja(true)}>Abrir una hoja</Button>
          </Card>

          <Card className="space-y-3">
            <p className="section-kicker">Avisos de la aplicación</p>
            <p className="flex items-center justify-center gap-2 rounded-lg bg-warning-soft px-4 py-1.5 text-[13px]/[18px] font-medium text-warning">
              <Icono nombre="sinConexion" className="size-4 shrink-0" />
              Sin conexión. Ves lo último que cargaste; para guardar hace falta red.
            </p>
            <div className="flex items-center gap-3 rounded-2xl bg-surface-200 p-3">
              <span className="flex size-9 shrink-0 items-center justify-center rounded-full bg-primary-soft text-primary">
                <Icono nombre="recargar" className="size-5" />
              </span>
              <p className="min-w-0 flex-1 text-[15px]/[20px]">
                <span className="font-semibold">Hay una versión nueva.</span>{" "}
                <span className="text-ink-muted">Se aplica al recargar.</span>
              </p>
              <Button tamano="sm" variante="primary">
                Actualizar
              </Button>
            </div>
          </Card>
        </div>

        {hoja && (
          <Panel titulo="Una hoja" onCerrar={() => setHoja(false)}>
            <p className="body">
              Con la agarradera arriba y el radio de 32 px de las hojas de iOS. Escape, el fondo o
              la ✕ la cierran, y el foco vuelve al botón que la abrió.
            </p>
          </Panel>
        )}
      </Seccion>

      <Seccion
        titulo="Mensajes"
        nota="Teñidos, con el icono en el color del tono y el texto en tinta. Icono además del color: el color a solas no lo ve todo el mundo."
      >
        <div className="space-y-2">
          <Aviso tono="exito">Rutina guardada.</Aviso>
          <Aviso tono="aviso">Llevas dos semanas sin entrenar pierna.</Aviso>
          <Aviso tono="error" urgente>
            No se pudo guardar la serie.
          </Aviso>
          <Aviso tono="informacion">El análisis semanal se ejecuta los lunes a las 8:00.</Aviso>
        </div>
      </Seccion>
    </>
  );
}
