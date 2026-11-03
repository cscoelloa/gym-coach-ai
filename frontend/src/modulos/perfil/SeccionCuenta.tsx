import { EnlaceBoton } from "@/ds/Button";
import { Campo } from "@/ds/Campo";
import { Card } from "@/ds/Card";
import { Hint } from "@/ds/Hint";

import type { PropsDeSeccion } from "./formulario";

export function SeccionCuenta({
  actual,
  cambiar,
  porCampo,
  usuario,
}: PropsDeSeccion & { usuario: string }) {
  return (
    <div className="grid grid-cols-1 items-start gap-4 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]">
      <Card className="card-accent">
        <p className="section-kicker">01 / Identidad</p>
        <h2 className="mb-3">Datos de la cuenta</h2>
        <div className="form-grid">
          <Campo
            etiqueta="Nombre"
            value={actual.first_name}
            errores={porCampo["first_name"]}
            onChange={(evento) => cambiar("first_name", evento.target.value)}
          />
          <Campo
            etiqueta="Apellidos"
            value={actual.last_name}
            errores={porCampo["last_name"]}
            onChange={(evento) => cambiar("last_name", evento.target.value)}
          />
          <Campo
            etiqueta="Correo"
            type="email"
            value={actual.email}
            errores={porCampo["email"]}
            onChange={(evento) => cambiar("email", evento.target.value)}
          />
        </div>
        <p className="caption mt-2 text-ink-muted">
          El nombre de usuario (<span className="num">{usuario}</span>) no se cambia: es lo
          que identifica tu cuenta.
        </p>
      </Card>

      <Card>
        <h2 className="mb-2">Tus datos</h2>
        <Hint>
          Puedes descargar todo lo que la aplicación sabe de ti en cualquier momento, y borrarlo
          entero. Son tus datos.
        </Hint>
        <div className="form-actions">
          <a className="btn btn-secondary" href="/api/cuenta/" download>
            Descargar mis datos
          </a>
          <EnlaceBoton a="/perfil/eliminar/" variante="danger">
            Eliminar mi cuenta
          </EnlaceBoton>
        </div>
      </Card>
    </div>
  );
}
