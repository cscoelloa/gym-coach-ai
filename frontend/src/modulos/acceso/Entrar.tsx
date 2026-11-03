import { useState, type FormEvent } from "react";
import { Link, useSearchParams } from "react-router";

import { ErrorDeApi } from "@/api/cliente";
import { useEntrar } from "@/api/sesion";
import { Aviso } from "@/ds/Aviso";
import { Campo } from "@/ds/Campo";
import { salirDeLaSpa } from "@/lib/navegar";

import { MarcoDeAcceso } from "./MarcoDeAcceso";

export function Entrar() {
  const [parametros] = useSearchParams();
  const entrar = useEntrar();
  const [usuario, setUsuario] = useState("");
  const [clave, setClave] = useState("");

  const error = entrar.error instanceof ErrorDeApi ? entrar.error : null;

  function enviar(evento: FormEvent) {
    evento.preventDefault();
    entrar.mutate(
      {
        username: usuario,
        password: clave,
        next: parametros.get("next") ?? "",
      },
      { onSuccess: (datos) => salirDeLaSpa(datos.redirect) },
    );
  }

  return (
    <MarcoDeAcceso
      kicker="Bienvenido de vuelta"
      titulo="Entrar"
      entradilla="Continúa donde dejaste tu último entrenamiento."
    >
      {error && (
        <Aviso tono={error.estado === 403 ? "aviso" : "error"} urgente>
          {error.message}
        </Aviso>
      )}

      <form className="mt-6" onSubmit={enviar} noValidate>
        <Campo
          etiqueta="Usuario"
          name="username"
          autoComplete="username"
          required
          autoFocus
          value={usuario}
          onChange={(evento) => setUsuario(evento.target.value)}
          errores={error?.porCampo["username"]}
        />
        <Campo
          etiqueta="Contraseña"
          type="password"
          name="password"
          autoComplete="current-password"
          required
          value={clave}
          onChange={(evento) => setClave(evento.target.value)}
          errores={error?.porCampo["password"]}
        />
        <button className="btn btn-primary btn-lg btn-block" type="submit" disabled={entrar.isPending}>
          {entrar.isPending ? "Entrando…" : "Entrar"}
        </button>
      </form>

      <p className="body mt-5 text-ink-muted">
        ¿No tienes cuenta?{" "}
        <Link className="font-semibold" to="/registro/">
          Crear una
        </Link>
      </p>
    </MarcoDeAcceso>
  );
}
