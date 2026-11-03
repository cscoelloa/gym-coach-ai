import { Campo } from "@/ds/Campo";
import { Card } from "@/ds/Card";
import { Icono } from "@/ds/Icono";

import { Desplegable } from "./Desplegable";
import type { OpcionesDePerfil, PropsDeSeccion } from "./formulario";

export function SeccionEntrenamiento({
  actual,
  cambiar,
  porCampo,
  opciones,
}: PropsDeSeccion & { opciones: OpcionesDePerfil }) {
  function alternarMaterial(material: string) {
    const puestos = new Set(actual.available_equipment);
    if (puestos.has(material)) puestos.delete(material);
    else puestos.add(material);
    cambiar("available_equipment", [...puestos]);
  }

  return (
    <Card>
      <p className="section-kicker">02 / Objetivo</p>
      <h2 className="mb-3">Entrenamiento</h2>
      <div className="form-grid">
        <Desplegable
          etiqueta="Objetivo"
          valor={actual.goal}
          opciones={opciones.goal}
          onCambio={(valor) => cambiar("goal", valor)}
        />
        <Desplegable
          etiqueta="Nivel"
          valor={actual.experience_level}
          opciones={opciones.experience_level}
          onCambio={(valor) => cambiar("experience_level", valor)}
        />
        <Campo
          etiqueta="Peso objetivo (kg)"
          type="number"
          step="0.1"
          inputMode="decimal"
          value={actual.target_weight_kg ?? ""}
          errores={porCampo["target_weight_kg"]}
          onChange={(evento) => cambiar("target_weight_kg", evento.target.value || null)}
        />
        <Campo
          etiqueta="Cambio semanal objetivo (kg)"
          type="number"
          step="0.05"
          inputMode="decimal"
          value={actual.weekly_weight_change_target_kg ?? ""}
          errores={porCampo["weekly_weight_change_target_kg"]}
          onChange={(evento) =>
            cambiar("weekly_weight_change_target_kg", evento.target.value || null)
          }
          ayuda="En negativo si quieres bajar."
        />
        <Campo
          etiqueta="Días por semana"
          type="number"
          min={1}
          max={7}
          inputMode="numeric"
          value={String(actual.available_days_per_week)}
          errores={porCampo["available_days_per_week"]}
          onChange={(evento) =>
            cambiar("available_days_per_week", Number(evento.target.value))
          }
        />
      </div>

      <div className="field">
        <span className="config-label">Equipamiento disponible</span>
        <div className="flex flex-wrap gap-2">
          {opciones.available_equipment.map((material) => {
            const marcado = actual.available_equipment.includes(material.valor);
            return (
              <label
                className={`chip has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-offset-2 has-[:focus-visible]:outline-focus ${
                  marcado ? "chip-on" : ""
                }`}
                key={material.valor}
              >
                <input
                  className="sr-only"
                  type="checkbox"
                  checked={marcado}
                  onChange={() => alternarMaterial(material.valor)}
                />
                {marcado && <Icono nombre="comprobado" className="-ml-1 size-4" />}
                {material.etiqueta}
              </label>
            );
          })}
        </div>
        <span className="helptext">Sin marcar nada = sin restricción.</span>
      </div>
    </Card>
  );
}
