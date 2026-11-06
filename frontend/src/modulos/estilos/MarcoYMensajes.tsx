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
        nota="El cristal es solo para lo que controla: la barra de pestañas flota como una cápsula, arriba los botones son cápsulas y el contenido se funde en el borde de scroll en vez de chocar con una línea. Sobre cristal el texto es tinta o lima, nunca gris. Si el teléfono pide más contraste, el cristal se vuelve opaco. Las tarjetas y las hojas son sólidas: son contenido."
      >
        <Card className="mb-4 space-y-3">
          <p className="section-kicker">El cristal</p>
          <div className="relative h-44 overflow-hidden rounded-2xl bg-linear-to-br from-primary-soft via-data-soft to-surface-200 p-4">
            <p className="metric-2xl text-ink">92,5</p>
            <div className="mt-2 flex flex-wrap gap-2">
              <span className="chip chip-on">Pecho</span>
              <span className="chip">Espalda</span>
              <span className="chip">Pierna</span>
            </div>
            <div className="glass absolute inset-x-3 bottom-3 grid grid-cols-3 rounded-full p-1">
              <span className="tab-link tab-link-on">
                <Icono nombre="inicio" className="size-6" />
                Inicio
              </span>
              <span className="tab-link">
                <Icono nombre="plan" className="size-6" />
                Plan
              </span>
              <span className="tab-link">
                <Icono nombre="entrenar" className="size-6" />
                Entrenar
              </span>
            </div>
          </div>
        </Card>

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
              Con la agarradera arriba y el radio de 36 px de las hojas de iOS. Escape, el fondo o
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
