import { Campo } from "@/ds/Campo";
import { Card } from "@/ds/Card";

import { Desplegable } from "./Desplegable";
import type { OpcionesDePerfil, PropsDeSeccion } from "./formulario";

export function SeccionSalud({
  actual,
  cambiar,
  porCampo,
  opciones,
  edad,
}: PropsDeSeccion & { opciones: OpcionesDePerfil; edad: number | null }) {
  return (
    <Card>
      <p className="section-kicker">03 / Datos de salud</p>
      <h2 className="mb-1">Para calibrar las cargas</h2>
      <p className="body-sm mb-3 text-ink-muted">
        Sirven para estimar tu 1RM, interpretar el tonelaje y evitar ejercicios que te hagan
        daño. A la IA se le manda tu <strong>edad calculada</strong>, nunca tu fecha de
        nacimiento.
      </p>

      <div className="form-grid">
        <Desplegable
          etiqueta="Sexo"
          valor={actual.sex}
          opciones={opciones.sex}
          onCambio={(valor) => cambiar("sex", valor)}
        />
        <Campo
          etiqueta="Fecha de nacimiento"
          type="date"
          value={actual.birth_date ?? ""}
          errores={porCampo["birth_date"]}
          onChange={(evento) => cambiar("birth_date", evento.target.value || null)}
          ayuda={edad !== null ? `Ahora mismo: ${edad} años.` : undefined}
        />
        <Campo
          etiqueta="Altura (cm)"
          type="number"
          inputMode="numeric"
          value={actual.height_cm === null ? "" : String(actual.height_cm)}
          errores={porCampo["height_cm"]}
          onChange={(evento) =>
            cambiar("height_cm", evento.target.value ? Number(evento.target.value) : null)
          }
        />
      </div>

      <Campo
        etiqueta="Lesiones y limitaciones"
        multilinea
        filas={4}
        maxLength={500}
        value={actual.injuries_notes}
        errores={porCampo["injuries_notes"]}
        onChange={(evento) => cambiar("injuries_notes", evento.target.value)}
        ayuda="Se le pasa a la IA como dato sobre tu situación, nunca como instrucción."
      />
    </Card>
  );
}
