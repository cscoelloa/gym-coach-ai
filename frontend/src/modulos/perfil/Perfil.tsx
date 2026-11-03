import { useState } from "react";

import { ErrorDeApi } from "@/api/cliente";
import { Aviso } from "@/ds/Aviso";
import { AvisoPasajero } from "@/ds/AvisoPasajero";
import { Button } from "@/ds/Button";
import { PageHeader } from "@/ds/Card";
import { Cargando, ErrorDePantalla } from "@/ds/estados";
import { Pestanas, useVista } from "@/ds/Pestanas";

import {
  useGuardarPerfil,
  useOpcionesDePerfil,
  usePerfil,
  type Perfil as DatosDePerfil,
} from "./api";
import { SeccionCuenta } from "./SeccionCuenta";
import { SeccionEntrenamiento } from "./SeccionEntrenamiento";
import { SeccionSalud } from "./SeccionSalud";

const VISTAS = ["cuenta", "entrenamiento", "salud"] as const;
type Vista = (typeof VISTAS)[number];

const PESTANA_DEL_CAMPO: Record<string, Vista> = {
  first_name: "cuenta",
  last_name: "cuenta",
  email: "cuenta",
  goal: "entrenamiento",
  experience_level: "entrenamiento",
  target_weight_kg: "entrenamiento",
  weekly_weight_change_target_kg: "entrenamiento",
  available_days_per_week: "entrenamiento",
  available_equipment: "entrenamiento",
  sex: "salud",
  birth_date: "salud",
  height_cm: "salud",
  injuries_notes: "salud",
};

function MarcaDeError() {
  return (
    <span className="size-2 shrink-0 rounded-full bg-danger">
      <span className="sr-only"> (con errores)</span>
    </span>
  );
}

export function Perfil() {
  const { data, isPending, error, refetch } = usePerfil();
  const opciones = useOpcionesDePerfil();
  const guardar = useGuardarPerfil();

  const [cambios, setCambios] = useState<Partial<DatosDePerfil>>({});
  const [vista, setVista] = useVista(VISTAS);

  if (isPending || opciones.isPending) return <Cargando />;
  if (error || !data || opciones.error || !opciones.data) {
    return <ErrorDePantalla onReintentar={refetch} />;
  }

  const actual = { ...data, ...cambios };
  const sinCambios = Object.keys(cambios).length === 0;
  const porCampo = guardar.error instanceof ErrorDeApi ? guardar.error.porCampo : {};
  const conErrores = new Set(Object.keys(porCampo).map((campo) => PESTANA_DEL_CAMPO[campo]));
  const pestana = (valor: Vista, etiqueta: string) => ({
    valor,
    etiqueta,
    ...(conErrores.has(valor) ? { marca: <MarcaDeError /> } : {}),
  });

  function cambiar<C extends keyof DatosDePerfil>(campo: C, valor: DatosDePerfil[C]) {
    setCambios((previo) => ({ ...previo, [campo]: valor }));
  }

  return (
    <>
      <PageHeader
        kicker="Configuración personal"
        titulo="Tu perfil"
        entradilla="Esto es lo que usa la IA para calibrar tus rutinas."
      >
        <Button
          variante="primary"
          disabled={sinCambios || guardar.isPending}
          onClick={() => guardar.mutate(cambios, { onSuccess: () => setCambios({}) })}
        >
          {guardar.isPending ? "Guardando…" : "Guardar cambios"}
        </Button>
      </PageHeader>

      {sinCambios && (
        <AvisoPasajero marca={guardar.isSuccess && guardar.submittedAt}>
          Perfil actualizado.
        </AvisoPasajero>
      )}
      {guardar.error && !Object.keys(porCampo).length && (
        <Aviso tono="error" urgente>
          {guardar.error instanceof Error
            ? guardar.error.message
            : "No se ha podido guardar el perfil."}
        </Aviso>
      )}

      <Pestanas
        etiqueta="Secciones del perfil"
        valor={vista}
        onCambio={setVista}
        opciones={[
          pestana("cuenta", "Cuenta"),
          pestana("entrenamiento", "Entrenamiento"),
          pestana("salud", "Salud"),
        ]}
      >
        {vista === "cuenta" && (
          <SeccionCuenta
            actual={actual}
            cambiar={cambiar}
            porCampo={porCampo}
            usuario={data.username}
          />
        )}
        {vista === "entrenamiento" && (
          <SeccionEntrenamiento
            actual={actual}
            cambiar={cambiar}
            porCampo={porCampo}
            opciones={opciones.data}
          />
        )}
        {vista === "salud" && (
          <SeccionSalud
            actual={actual}
            cambiar={cambiar}
            porCampo={porCampo}
            opciones={opciones.data}
            edad={data.age}
          />
        )}
      </Pestanas>
    </>
  );
}
