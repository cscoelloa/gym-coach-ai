import { useState } from "react";

import { Aviso } from "@/ds/Aviso";
import { Button } from "@/ds/Button";
import { ConfigDeSeries, type ConfigEnTexto } from "@/ds/ConfigDeSeries";
import { MediaDeEjercicio } from "@/ds/MediaDeEjercicio";

import type { ConfigDeEjercicio } from "./api";
import type { Fila } from "./useEditorDeRutina";

export function Configuracion({
  fila,
  existente,
  onConfirmar,
  onQuitar,
  onAtras,
}: {
  fila: Fila;
  existente: boolean;
  onConfirmar: (fila: Fila) => void;
  onQuitar: () => void;
  onAtras: () => void;
}) {
  const [config, setConfig] = useState<ConfigEnTexto>({
    target_sets: String(fila.target_sets),
    target_reps_min: String(fila.target_reps_min),
    target_reps_max: String(fila.target_reps_max),
    rest_seconds: String(fila.rest_seconds),
  });
  const [error, setError] = useState("");

  function confirmar() {
    const valores = Object.fromEntries(
      Object.entries(config).map(([k, v]) => [k, v.trim() ? Number(v) : NaN]),
    ) as ConfigDeEjercicio;
    if (
      Object.values(valores).some((v) => !Number.isInteger(v)) ||
      valores.target_sets < 1 ||
      valores.target_sets > 20 ||
      valores.target_reps_min < 1 ||
      valores.target_reps_max > 100 ||
      valores.target_reps_min > valores.target_reps_max ||
      valores.rest_seconds < 0 ||
      valores.rest_seconds > 900
    ) {
      setError(
        "Revisa la configuración: 1–20 series, 1–100 repeticiones y 0–900 segundos de descanso. El mínimo no puede superar al máximo.",
      );
      return;
    }
    onConfirmar({ ...fila, ...valores });
  }

  return (
    <div className="space-y-5">
      <MediaDeEjercicio
        imagen={fila.exercise_detail.image}
        animacion={fila.exercise_detail.animation}
        atribucion={fila.exercise_detail.attribution}
        tamano="sm"
      />
      <p className="caption text-center text-ink-muted">
        {fila.exercise_detail.body_part_label} · {fila.exercise_detail.equipment_label}
      </p>
      <ConfigDeSeries valores={config} onCambio={setConfig} />
      {error && (
        <Aviso tono="error" urgente>
          {error}
        </Aviso>
      )}
      <div className="flex flex-col gap-2">
        <Button variante="primary" tamano="lg" bloque onClick={confirmar}>
          {existente ? "Aplicar al borrador" : "Añadir al borrador"}
        </Button>
        {existente ? (
          <Button variante="danger" bloque onClick={onQuitar}>
            Quitar de la rutina
          </Button>
        ) : (
          <Button bloque onClick={onAtras}>
            Volver a buscar
          </Button>
        )}
      </div>
    </div>
  );
}
