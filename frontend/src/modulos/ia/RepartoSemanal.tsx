import { useState } from "react";

import { Button } from "@/ds/Button";
import { Campo } from "@/ds/Campo";
import { Chip, FilaDeChips } from "@/ds/Chip";
import { Icono } from "@/ds/Icono";
import { Panel } from "@/ds/Panel";

import type { DiaDelReparto, MusculoElegible } from "./api";

export const DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"];

export function repartoInicial(
  sugeridos: number[],
  ejerciciosPorDefecto: number,
): DiaDelReparto[] {
  return DIAS.map((_etiqueta, weekday) => ({
    weekday,
    muscles: [],
    emphasis: null,
    exercises: sugeridos.includes(weekday) ? ejerciciosPorDefecto : 0,
  }));
}

function resumen(dia: DiaDelReparto, musculos: MusculoElegible[]): string {
  if (!dia.muscles.length) return "Descanso";
  const etiqueta = (valor: string) =>
    musculos.find((m) => m.valor === valor)?.etiqueta ?? valor;
  const lista = dia.muscles.map(etiqueta).join(", ");
  return `${lista} · ${dia.exercises} ejercicios`;
}

export function RepartoSemanal({
  reparto,
  musculos,
  limites,
  onCambio,
}: {
  reparto: DiaDelReparto[];
  musculos: MusculoElegible[];
  limites: { min: number; max: number; por_defecto: number };
  onCambio: (reparto: DiaDelReparto[]) => void;
}) {
  const [editando, setEditando] = useState<number | null>(null);
  const abierto = editando === null ? null : reparto[editando];

  function guardar(nuevo: DiaDelReparto) {
    onCambio(reparto.map((d) => (d.weekday === nuevo.weekday ? nuevo : d)));
    setEditando(null);
  }

  return (
    <>
      <p className="section-kicker">Tu semana</p>
      <div className="compact-list">
        {reparto.map((dia) => (
          <button
            key={dia.weekday}
            type="button"
            className="compact-row"
            onClick={() => setEditando(dia.weekday)}
          >
            <span className="ex-name w-24 shrink-0 text-left">{DIAS[dia.weekday]}</span>
            <span
              className={`body-sm flex-1 text-left ${dia.muscles.length ? "" : "text-ink-muted"}`}
            >
              {resumen(dia, musculos)}
            </span>
            <Icono nombre="chevronDerecha" />
          </button>
        ))}
      </div>

      {abierto && (
        <Panel titulo={DIAS[abierto.weekday] ?? ""} onCerrar={() => setEditando(null)}>
          <EditorDeDia
            key={abierto.weekday}
            dia={abierto}
            musculos={musculos}
            limites={limites}
            onGuardar={guardar}
            onDescanso={() =>
              guardar({ ...abierto, muscles: [], emphasis: null, exercises: limites.por_defecto })
            }
          />
        </Panel>
      )}
    </>
  );
}

function EditorDeDia({
  dia,
  musculos,
  limites,
  onGuardar,
  onDescanso,
}: {
  dia: DiaDelReparto;
  musculos: MusculoElegible[];
  limites: { min: number; max: number; por_defecto: number };
  onGuardar: (dia: DiaDelReparto) => void;
  onDescanso: () => void;
}) {
  const [elegidos, setElegidos] = useState<string[]>(dia.muscles);
  const [enfasis, setEnfasis] = useState<string | null>(dia.emphasis);
  const [ejercicios, setEjercicios] = useState(String(dia.exercises || limites.por_defecto));

  function alternar(valor: string) {
    const nuevos = elegidos.includes(valor)
      ? elegidos.filter((m) => m !== valor)
      : [...elegidos, valor];
    setElegidos(nuevos);
    if (enfasis && !nuevos.includes(enfasis)) setEnfasis(null);
  }

  return (
    <div className="space-y-5">
      <div>
        <p className="section-kicker">Qué se entrena</p>
        <FilaDeChips>
          {musculos.map((musculo) => (
            <Chip
              key={musculo.valor}
              activo={elegidos.includes(musculo.valor)}
              recuento={musculo.n}
              onClick={() => alternar(musculo.valor)}
            >
              {musculo.etiqueta}
            </Chip>
          ))}
        </FilaDeChips>
      </div>

      {elegidos.length > 1 && (
        <div>
          <p className="section-kicker">Énfasis (opcional)</p>
          <p className="caption mb-2 text-ink-muted">
            El que lleve énfasis se lleva más ejercicios que los demás ese día.
          </p>
          <FilaDeChips>
            {elegidos.map((valor) => (
              <Chip
                key={valor}
                activo={enfasis === valor}
                onClick={() => setEnfasis(enfasis === valor ? null : valor)}
              >
                {musculos.find((m) => m.valor === valor)?.etiqueta ?? valor}
              </Chip>
            ))}
          </FilaDeChips>
        </div>
      )}

      <Campo
        etiqueta="Ejercicios ese día"
        type="number"
        min={limites.min}
        max={limites.max}
        inputMode="numeric"
        value={ejercicios}
        onChange={(evento) => setEjercicios(evento.target.value)}
      />

      <Button
        variante="primary"
        bloque
        disabled={!elegidos.length}
        onClick={() =>
          onGuardar({
            ...dia,
            muscles: elegidos,
            emphasis: enfasis,
            exercises: Number(ejercicios) || limites.por_defecto,
          })
        }
      >
        Guardar el día
      </Button>
      <Button bloque onClick={onDescanso}>
        Marcar como descanso
      </Button>
    </div>
  );
}
