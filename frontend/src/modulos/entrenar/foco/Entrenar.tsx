import { useEffect, useState } from "react";
import { Link, useParams } from "react-router";

import { Cargando, ErrorDePantalla } from "@/ds/estados";
import { Icono } from "@/ds/Icono";
import { retenerActualizacion } from "@/lib/pwa";

import { AvanceDelEntreno } from "./AvanceDelEntreno";
import { BarraDeRegistrar } from "./BarraDeRegistrar";
import { ChipsDeEjercicios } from "./ChipsDeEjercicios";
import { ComoSeHace } from "./ComoSeHace";
import { CorregirSerie } from "./CorregirSerie";
import { InterruptorDeBloqueo } from "./InterruptorDeBloqueo";
import { InterruptorDePantalla } from "./InterruptorDePantalla";
import { SeriesDelEjercicio } from "./SeriesDelEjercicio";
import { SesionSinRutina } from "./SesionSinRutina";
import { TarjetaDelEjercicio } from "./TarjetaDelEjercicio";
import { useEntrenar } from "./useEntrenar";

export function Entrenar() {
  const { id = "" } = useParams();
  const sesionId = Number(id);
  const e = useEntrenar(sesionId);
  const [mirando, setMirando] = useState(false);

  useEffect(() => retenerActualizacion(), []);

  if (e.foco.isPending) return <Cargando />;
  if (e.foco.error || !e.datos) return <ErrorDePantalla onReintentar={e.foco.refetch} />;

  const datos = e.datos;
  const { actual } = datos;

  return (
    <div className="flex flex-1 flex-col">
      <header className="mb-3 grid grid-cols-[5.75rem_minmax(0,1fr)_5.75rem] items-center gap-2">
        <Link
          className="icon-button justify-self-start bg-surface-200 text-ink-muted"
          to="/entrenamientos/"
        >
          <Icono nombre="cerrar" className="size-5" />
          <span className="sr-only">Salir del entrenamiento</span>
        </Link>
        <p className="truncate text-center text-[15px]/[20px] font-semibold text-ink">
          {datos.sesion.rutina ? datos.sesion.rutina.nombre : "Entrenamiento libre"}
        </p>
        <div className="flex items-center justify-end gap-1">
          <InterruptorDeBloqueo bloqueo={e.bloqueo} />
          <InterruptorDePantalla />
        </div>
      </header>

      {!actual ? (
        <SesionSinRutina datos={datos} onTerminar={e.terminar} />
      ) : (
        <div className="focus-layout">
          <AvanceDelEntreno datos={datos} e={e} />

          {datos.planificados.length > 1 && (
            <ChipsDeEjercicios datos={datos} onElegir={e.irAEjercicio} />
          )}

          <TarjetaDelEjercicio
            datos={datos}
            actual={actual}
            onComoSeHace={() => setMirando(true)}
          />

          <SeriesDelEjercicio
            filas={datos.filas}
            unilateral={actual.unilateral}
            onCorregir={e.setCorrigiendo}
          />

          {e.corrigiendo && (
            <CorregirSerie
              key={e.corrigiendo.serie_id}
              sesionId={sesionId}
              fila={e.corrigiendo}
              onCerrar={() => e.setCorrigiendo(null)}
            />
          )}
          {mirando && (
            <ComoSeHace
              slug={actual.slug}
              nombre={actual.nombre}
              onCerrar={() => setMirando(false)}
            />
          )}

          <BarraDeRegistrar e={e} />
        </div>
      )}
    </div>
  );
}
