import { Badge } from "@/ds/Badge";
import { PageHeader } from "@/ds/Card";
import { Cargando, ErrorDePantalla } from "@/ds/estados";
import { Pestanas, useVista } from "@/ds/Pestanas";

import { useRegistrosDePeso, useResumenDePeso } from "./api";
import { FormularioDePeso } from "./FormularioDePeso";
import { HistorialDePeso } from "./HistorialDePeso";
import { TendenciaDePeso } from "./TendenciaDePeso";

const VISTAS = ["registrar", "historial"] as const;

export function Peso() {
  const [vista, setVista] = useVista(VISTAS);
  const resumen = useResumenDePeso();
  const registros = useRegistrosDePeso();

  if (resumen.isPending || registros.isPending) return <Cargando />;
  if (resumen.error || registros.error) {
    return (
      <ErrorDePantalla
        onReintentar={() => {
          resumen.refetch();
          registros.refetch();
        }}
      />
    );
  }

  const ultimo = resumen.data.ultimo;

  return (
    <>
      <PageHeader
        kicker="Composición y tendencia"
        titulo="Peso corporal"
        hero="data"
        entradilla="Un dato breve; una señal útil cuando se mira en el tiempo."
      >
        {ultimo && (
          <div className="text-right">
            <span className="tag block text-ink-subtle">Último registro</span>
            <strong className="metric-xl">{ultimo.weight_kg}</strong>
            <span className="stat-tile-unit"> kg</span>
            {resumen.data.cambio != null && resumen.data.cambio !== 0 && (
              <div className="mt-1">
                <Badge tono={resumen.data.cambio > 0 ? "warn" : "info"}>
                  {resumen.data.cambio > 0 ? "▲" : "▼"}{" "}
                  {Math.abs(resumen.data.cambio).toFixed(1)} kg
                </Badge>
              </div>
            )}
          </div>
        )}
      </PageHeader>

      <Pestanas
        etiqueta="Secciones de Peso"
        valor={vista}
        onCambio={setVista}
        opciones={[
          { valor: "registrar", etiqueta: "Registrar" },
          {
            valor: "historial",
            etiqueta: "Historial",
            marca: registros.data.count ? (
              <span className="num text-ink-subtle">{registros.data.count}</span>
            ) : undefined,
          },
        ]}
      >
        {vista === "registrar" && (
          <div className="grid grid-cols-1 items-start gap-4 lg:grid-cols-2">
            <FormularioDePeso recientes={registros.data.results} />
            <TendenciaDePeso serie={resumen.data.serie} ultimo={ultimo} />
          </div>
        )}
        {vista === "historial" && <HistorialDePeso />}
      </Pestanas>
    </>
  );
}
