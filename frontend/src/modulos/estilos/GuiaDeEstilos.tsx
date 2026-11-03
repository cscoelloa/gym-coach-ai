import { PageHeader } from "@/ds/Card";
import { ThemeToggle } from "@/ds/ThemeToggle";

import { Controles } from "./Controles";
import { DatosYVacios } from "./DatosYVacios";
import { Fundamentos } from "./Fundamentos";
import { MarcoYMensajes } from "./MarcoYMensajes";
import { PiezasDeEntrenar } from "./PiezasDeEntrenar";

export function GuiaDeEstilos() {
  return (
    <>
      <PageHeader
        kicker="Aire · sistema de diseño"
        titulo="Guía de estilos"
        entradilla={
          <>
            Construida con los componentes de <code>frontend/src/ds/</code>. Los tokens salen de{" "}
            <code>assets/app.css</code>, y el tema sigue al del sistema salvo que se fuerce uno.
          </>
        }
      >
        <div className="w-full max-w-xs">
          <ThemeToggle />
        </div>
      </PageHeader>

      <Fundamentos />
      <Controles />
      <PiezasDeEntrenar />
      <DatosYVacios />
      <MarcoYMensajes />
    </>
  );
}
