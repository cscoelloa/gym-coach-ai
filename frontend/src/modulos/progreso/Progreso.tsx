import { Badge } from "@/ds/Badge";
import { EnlaceBoton } from "@/ds/Button";
import { PageHeader } from "@/ds/Card";
import { Cargando, ErrorDePantalla } from "@/ds/estados";
import { Pestanas, useVista } from "@/ds/Pestanas";
import { StatTile } from "@/ds/StatTile";

import { useProgreso } from "./api";
import { PanelDeActividad } from "./PanelDeActividad";
import { PanelDelCuerpo } from "./PanelDelCuerpo";
import { PanelDeMetricas } from "./PanelDeMetricas";

const VISTAS = ["actividad", "cuerpo", "metricas"] as const;

export function Progreso() {
  const { data, isPending, error, refetch } = useProgreso();
  const [vista, setVista] = useVista(VISTAS);

  if (isPending) return <Cargando />;
  if (error || !data) return <ErrorDePantalla onReintentar={refetch} />;

  const { cifras } = data;

  return (
    <>
      <PageHeader
        kicker="Panel de rendimiento"
        titulo="Progreso"
        hero="data"
        entradilla="Señales claras para decidir qué ajustar después."
      >
        <EnlaceBoton a="/metricas/" variante="secondary">
          Elegir métricas
        </EnlaceBoton>
        <EnlaceBoton a="/ia/analisis/" variante="primary">
          Análisis con IA
        </EnlaceBoton>
      </PageHeader>

      <div className="stat-row">
        <StatTile etiqueta="Entrenamientos" valor={cifras.total_sesiones} icono="entrenar" />
        <StatTile etiqueta="Este mes" valor={cifras.sesiones_este_mes} icono="plan" tono="data" />
        <StatTile
          etiqueta="Racha"
          valor={cifras.racha_semanas}
          unidad="sem."
          icono="fuego"
          tono="warning"
        />
        <StatTile
          etiqueta="Peso 30 días"
          icono="bascula"
          tono="data"
          valor={
            cifras.peso_30_dias === null
              ? null
              : `${cifras.peso_30_dias > 0 ? "+" : ""}${cifras.peso_30_dias.toFixed(1)}`
          }
          unidad="kg"
          vacio="Hacen falta dos pesajes separados."
        >
          {cifras.peso_30_dias !== null && cifras.peso_30_dias !== 0 && (
            <Badge tono={cifras.peso_30_dias > 0 ? "warn" : "done"}>
              {cifras.peso_30_dias > 0 ? "↑" : "↓"} en 30 días
            </Badge>
          )}
        </StatTile>
      </div>

      <Pestanas
        etiqueta="Secciones de Progreso"
        valor={vista}
        onCambio={setVista}
        opciones={[
          { valor: "actividad", etiqueta: "Actividad" },
          { valor: "cuerpo", etiqueta: "Cuerpo" },
          { valor: "metricas", etiqueta: "Métricas" },
        ]}
      >
        {vista === "actividad" && <PanelDeActividad data={data} />}
        {vista === "cuerpo" && <PanelDelCuerpo data={data} />}
        {vista === "metricas" && <PanelDeMetricas />}
      </Pestanas>
    </>
  );
}
