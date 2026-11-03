import { Link } from "react-router";

import { MarcoDeAcceso } from "./MarcoDeAcceso";

export function SesionCerrada() {
  return (
    <MarcoDeAcceso
      kicker="Hasta la próxima"
      titulo="Sesión cerrada"
      entradilla="Tus datos siguen aquí. Vuelve cuando toque entrenar."
    >
      <div className="mt-6 flex flex-wrap gap-3">
        <Link className="btn btn-primary btn-lg" to="/entrar/">
          Volver a entrar
        </Link>
      </div>
    </MarcoDeAcceso>
  );
}
