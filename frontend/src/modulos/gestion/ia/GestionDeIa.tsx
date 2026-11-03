import { PageHeader } from "@/ds/Card";
import { Pestanas, useVista } from "@/ds/Pestanas";

import { Documentos } from "./Documentos";
import { Programacion } from "./Programacion";
import { Prompts } from "./Prompts";
import { Proveedores } from "./Proveedores";

const ZONAS = ["proveedores", "prompts", "rag", "programacion"] as const;

export function GestionDeIa() {
  const [zona, setZona] = useVista(ZONAS, "zona");

  return (
    <>
      <PageHeader
        kicker="Inteligencia artificial"
        titulo="Configuración"
        entradilla="Qué modelo responde, con qué instrucciones y con qué contexto."
      />

      <Pestanas
        etiqueta="Zona"
        opciones={[
          { valor: "proveedores", etiqueta: "Proveedores" },
          { valor: "prompts", etiqueta: "Prompts" },
          { valor: "rag", etiqueta: "Documentos" },
          { valor: "programacion", etiqueta: "Programación" },
        ]}
        valor={zona}
        onCambio={setZona}
      >
        {zona === "proveedores" && <Proveedores />}
        {zona === "prompts" && <Prompts />}
        {zona === "rag" && <Documentos />}
        {zona === "programacion" && <Programacion />}
      </Pestanas>
    </>
  );
}
