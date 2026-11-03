import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router";

import { ErrorDeApi } from "@/api/cliente";
import { Aviso } from "@/ds/Aviso";
import { Button, EnlaceBoton } from "@/ds/Button";
import { Cabecera } from "@/ds/Cabecera";
import { Campo } from "@/ds/Campo";
import { Card } from "@/ds/Card";

import { useCrearPrograma } from "./api";
import { EditorDeRutina } from "./EditorDeRutina";

type Props = {
  titulo: string;
  entradilla: string;
  etiquetaNombre: string;
  ayudaNombre: string;
  boton: string;
  onCrear: (datos: { name: string; description: string }) => void;
  guardando: boolean;
  error: ErrorDeApi | null;
};

function FormularioDeAlta({
  titulo,
  entradilla,
  etiquetaNombre,
  ayudaNombre,
  boton,
  onCrear,
  guardando,
  error,
}: Props) {
  const [datos, setDatos] = useState({ name: "", description: "" });

  function enviar(evento: FormEvent) {
    evento.preventDefault();
    onCrear(datos);
  }

  return (
    <div className="form-narrow mx-auto">
      <Cabecera titulo={titulo} descripcion={entradilla} />

      <Card>
        {error && !Object.keys(error.porCampo).length && (
          <div className="mb-4">
            <Aviso tono="error" urgente>
              {error.message}
            </Aviso>
          </div>
        )}

        <form onSubmit={enviar} noValidate>
          <Campo
            etiqueta={etiquetaNombre}
            ayuda={ayudaNombre}
            value={datos.name}
            onChange={(evento) => setDatos({ ...datos, name: evento.target.value })}
            required
            autoFocus
            errores={error?.porCampo["name"]}
          />
          <Campo
            etiqueta="Descripción"
            multilinea
            value={datos.description}
            onChange={(evento) => setDatos({ ...datos, description: evento.target.value })}
            errores={error?.porCampo["description"]}
          />

          <div className="form-actions">
            <Button type="submit" variante="primary" disabled={guardando}>
              {guardando ? "Creando…" : boton}
            </Button>
            <EnlaceBoton a="/plan/" variante="secondary">
              Cancelar
            </EnlaceBoton>
          </div>
        </form>
      </Card>
    </div>
  );
}

export function RutinaNueva() {
  return <EditorDeRutina nueva />;
}

export function ProgramaNuevo() {
  const navegar = useNavigate();
  const crear = useCrearPrograma();

  return (
    <FormularioDeAlta
      titulo="Nuevo programa"
      entradilla="Un programa conecta tus rutinas con cada día de la semana."
      etiquetaNombre="Nombre"
      ayudaNombre="«Volumen», «Definición», «Vuelta tras la lesión»…"
      boton="Crear programa"
      guardando={crear.isPending}
      error={crear.error instanceof ErrorDeApi ? crear.error : null}
      onCrear={(datos) =>
        crear.mutate(datos, { onSuccess: () => navegar("/plan/", { replace: true }) })
      }
    />
  );
}
