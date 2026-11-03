import { useState, type FormEvent } from "react";
import { Link } from "react-router";

import { ErrorDeApi } from "@/api/cliente";
import { useRegistrarse } from "@/api/sesion";
import { Aviso } from "@/ds/Aviso";
import { Campo } from "@/ds/Campo";
import { salirDeLaSpa } from "@/lib/navegar";

import { MarcoDeAcceso } from "./MarcoDeAcceso";

export function Registro() {
  const registrarse = useRegistrarse();
  const [datos, setDatos] = useState({
    username: "",
    email: "",
    password: "",
    password2: "",
  });

  const error = registrarse.error instanceof ErrorDeApi ? registrarse.error : null;

  function cambiar(campo: keyof typeof datos) {
    return (evento: { target: { value: string } }) =>
      setDatos((previos) => ({ ...previos, [campo]: evento.target.value }));
  }

  function enviar(evento: FormEvent) {
    evento.preventDefault();
    registrarse.mutate(datos, {
      onSuccess: (respuesta) => salirDeLaSpa(respuesta.redirect),
    });
  }

  return (
    <MarcoDeAcceso
      kicker="Empieza aquí"
      titulo="Crear cuenta"
      entradilla="Un minuto para montar tu primera semana."
    >
      {error && !Object.keys(error.porCampo).length && (
        <Aviso tono="error" urgente>
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
          value={datos.username}
          onChange={cambiar("username")}
          errores={error?.porCampo["username"]}
        />
        <Campo
          etiqueta="Correo"
          type="email"
          name="email"
          autoComplete="email"
          required
          value={datos.email}
          onChange={cambiar("email")}
          errores={error?.porCampo["email"]}
        />
        <Campo
          etiqueta="Contraseña"
          type="password"
          name="password"
          autoComplete="new-password"
          required
          value={datos.password}
          onChange={cambiar("password")}
          errores={error?.porCampo["password"]}
        />
        <Campo
          etiqueta="Repite la contraseña"
          type="password"
          name="password2"
          autoComplete="new-password"
          required
          value={datos.password2}
          onChange={cambiar("password2")}
          errores={error?.porCampo["password2"]}
        />
        <button
          className="btn btn-primary btn-lg btn-block"
          type="submit"
          disabled={registrarse.isPending}
        >
          {registrarse.isPending ? "Creando…" : "Crear cuenta"}
        </button>
      </form>

      <p className="body mt-5 text-ink-muted">
        ¿Ya tienes cuenta?{" "}
        <Link className="font-semibold" to="/entrar/">
          Entrar
        </Link>
      </p>
    </MarcoDeAcceso>
  );
}
