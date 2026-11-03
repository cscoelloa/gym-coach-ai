import { useState, type FormEvent } from "react";

import { ErrorDeApi } from "@/api/cliente";
import { Aviso } from "@/ds/Aviso";
import { AvisoPasajero } from "@/ds/AvisoPasajero";
import { Button } from "@/ds/Button";
import { Campo } from "@/ds/Campo";
import { Card } from "@/ds/Card";

import { useGuardarPeso, type RegistroDePeso } from "./api";
import { hoyEnIso } from "./fechas";

export function FormularioDePeso({ recientes }: { recientes: RegistroDePeso[] }) {
  const guardar = useGuardarPeso();
  const [formulario, setFormulario] = useState({
    date: hoyEnIso(),
    weight_kg: "",
    body_fat_pct: "",
    notes: "",
  });

  const error = guardar.error instanceof ErrorDeApi ? guardar.error : null;

  const delDia = recientes.find((fila) => fila.date === formulario.date);

  function cambiar(campo: keyof typeof formulario) {
    return (evento: { target: { value: string } }) =>
      setFormulario((previo) => ({ ...previo, [campo]: evento.target.value }));
  }

  function enviar(evento: FormEvent) {
    evento.preventDefault();
    guardar.mutate(
      {
        datos: {
          date: formulario.date,
          weight_kg: formulario.weight_kg,
          ...(formulario.body_fat_pct ? { body_fat_pct: formulario.body_fat_pct } : {}),
          ...(formulario.notes ? { notes: formulario.notes } : {}),
        },
        ...(delDia ? { existente: delDia.id } : {}),
      },
      {
        onSuccess: () =>
          setFormulario((previo) => ({
            ...previo,
            weight_kg: "",
            body_fat_pct: "",
            notes: "",
          })),
      },
    );
  }

  return (
    <Card className="card-accent">
      {!error && (
        <AvisoPasajero marca={guardar.isSuccess && guardar.submittedAt}>Peso registrado.</AvisoPasajero>
      )}
      {error && !Object.keys(error.porCampo).length && (
        <Aviso tono="error" urgente>
          {error.message}
        </Aviso>
      )}

      <form onSubmit={enviar} noValidate>
        <Campo
          etiqueta="Fecha"
          type="date"
          value={formulario.date}
          onChange={cambiar("date")}
          required
          errores={error?.porCampo["date"]}
        />
        <div className="grid grid-cols-2 gap-x-3 sm:gap-x-4">
          <Campo
            etiqueta="Peso (kg)"
            inputMode="decimal"
            value={formulario.weight_kg}
            onChange={cambiar("weight_kg")}
            required
            errores={error?.porCampo["weight_kg"]}
          />
          <Campo
            etiqueta="Grasa (%)"
            inputMode="decimal"
            value={formulario.body_fat_pct}
            onChange={cambiar("body_fat_pct")}
            errores={error?.porCampo["body_fat_pct"]}
          />
        </div>
        <Campo
          etiqueta="Notas"
          multilinea
          filas={2}
          value={formulario.notes}
          onChange={cambiar("notes")}
          errores={error?.porCampo["notes"]}
        />
        <div className="form-actions">
          <Button type="submit" variante="primary" disabled={guardar.isPending}>
            {guardar.isPending ? "Guardando…" : "Guardar"}
          </Button>
        </div>
        <p className="caption mt-3 text-ink-muted">
          {delDia
            ? "Ya tienes un registro de ese día: se actualizará."
            : "Si ya registraste hoy, se actualizará ese registro."}
        </p>
      </form>
    </Card>
  );
}
