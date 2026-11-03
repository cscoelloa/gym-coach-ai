import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router";

import { ErrorDeApi } from "@/api/cliente";
import { Aviso } from "@/ds/Aviso";
import { Button, EnlaceBoton } from "@/ds/Button";
import { Campo } from "@/ds/Campo";
import { Card } from "@/ds/Card";
import { Cargando } from "@/ds/estados";

import { useCrearEjercicio, useTaxonomia } from "./api";

function Casilla({
  etiqueta,
  ayuda,
  marcada,
  onCambio,
}: {
  etiqueta: string;
  ayuda: string;
  marcada: boolean;
  onCambio: (marcada: boolean) => void;
}) {
  return (
    <div className="field">
      <label className="flex items-center gap-2">
        <input
          type="checkbox"
          checked={marcada}
          onChange={(evento) => onCambio(evento.target.checked)}
        />
        {etiqueta}
      </label>
      <span className="helptext">{ayuda}</span>
    </div>
  );
}

export function EjercicioNuevo() {
  const navegar = useNavigate();
  const taxonomia = useTaxonomia();
  const crear = useCrearEjercicio();

  const [datos, setDatos] = useState({
    name: "",
    body_part: "",
    equipment: "",
    is_bodyweight: false,
    is_unilateral: false,
  });

  const error = crear.error instanceof ErrorDeApi ? crear.error : null;

  if (taxonomia.isPending) return <Cargando />;

  function enviar(evento: FormEvent) {
    evento.preventDefault();
    crear.mutate(datos, {
      onSuccess: (ejercicio) => navegar(`/ejercicios/${ejercicio.slug}/`),
    });
  }

  return (
    <Card className="form-narrow mx-auto">
      <h1>Crea tu propio ejercicio</h1>
      <p className="body-sm mt-1 text-ink-muted">
        Para lo que no está en el catálogo. Solo lo verás tú.
      </p>

      {error && !Object.keys(error.porCampo).length && (
        <Aviso tono="error" urgente>
          {error.message}
        </Aviso>
      )}

      <form className="mt-4" onSubmit={enviar} noValidate>
        <Campo
          etiqueta="Nombre"
          value={datos.name}
          onChange={(evento) => setDatos({ ...datos, name: evento.target.value })}
          required
          autoFocus
          errores={error?.porCampo["name"]}
        />

        <div className="field">
          <label htmlFor="zona">Zona del cuerpo</label>
          <select
            id="zona"
            value={datos.body_part}
            onChange={(evento) => setDatos({ ...datos, body_part: evento.target.value })}
            required
          >
            <option value="">Elige una…</option>
            {taxonomia.data?.body_part.map((opcion) => (
              <option value={opcion.valor} key={opcion.valor}>
                {opcion.etiqueta}
              </option>
            ))}
          </select>
          {error?.porCampo["body_part"] && (
            <p className="errorlist">{error.porCampo["body_part"].join(" ")}</p>
          )}
        </div>

        <div className="field">
          <label htmlFor="material">Equipamiento</label>
          <select
            id="material"
            value={datos.equipment}
            onChange={(evento) => setDatos({ ...datos, equipment: evento.target.value })}
            required
          >
            <option value="">Elige uno…</option>
            {taxonomia.data?.equipment.map((opcion) => (
              <option value={opcion.valor} key={opcion.valor}>
                {opcion.etiqueta}
              </option>
            ))}
          </select>
          {error?.porCampo["equipment"] && (
            <p className="errorlist">{error.porCampo["equipment"].join(" ")}</p>
          )}
        </div>

        <Casilla
          etiqueta="Es de peso corporal"
          ayuda="Márcalo si el peso que mueves es el tuyo (dominadas, fondos). Así el tonelaje se calcula con tu peso corporal y no con cero."
          marcada={datos.is_bodyweight}
          onCambio={(marcada) => setDatos({ ...datos, is_bodyweight: marcada })}
        />
        <Casilla
          etiqueta="Es unilateral"
          ayuda="Márcalo si se hace un lado y luego el otro. Anotarás las series por lado y el tonelaje contará los dos."
          marcada={datos.is_unilateral}
          onCambio={(marcada) => setDatos({ ...datos, is_unilateral: marcada })}
        />

        <p className="caption mb-4 text-ink-muted">
          Sin foto ni animación: el material visual del catálogo es © Gym Visual y no se puede
          reutilizar para un ejercicio nuevo.
        </p>

        <div className="form-actions">
          <Button type="submit" variante="primary" disabled={crear.isPending}>
            {crear.isPending ? "Creando…" : "Crear ejercicio"}
          </Button>
          <EnlaceBoton a="/ejercicios/" variante="secondary">
            Cancelar
          </EnlaceBoton>
        </div>
      </form>
    </Card>
  );
}
