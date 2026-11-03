import { Aviso } from "@/ds/Aviso";
import { Badge } from "@/ds/Badge";
import { Button, EnlaceBoton } from "@/ds/Button";
import { Card, PageHeader } from "@/ds/Card";
import { EmptyState } from "@/ds/EmptyState";
import { Cargando, ErrorDePantalla } from "@/ds/estados";
import { Pestanas, useVista } from "@/ds/Pestanas";
import { ProgressBar } from "@/ds/ProgressBar";

import { codigoDe, useAnalisis, usePedirAnalisis } from "./api";
import { PanelDeCambios } from "./PanelDeCambios";
import { PanelDeEstancamientos } from "./PanelDeEstancamientos";
import { PanelDeLectura } from "./PanelDeLectura";

const VISTAS = ["lectura", "estancamientos", "cambios"] as const;

function Cuantos({ n }: { n: number }) {
  return <span className="num text-ink-subtle">{n}</span>;
}

const FECHA = new Intl.DateTimeFormat("es-ES", {
  day: "numeric",
  month: "short",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
});

export function AnalisisDeProgreso() {
  const { data, isPending, error, refetch } = useAnalisis();
  const pedir = usePedirAnalisis();
  const [vista, setVista] = useVista(VISTAS);

  if (isPending) return <Cargando />;
  if (error || !data) return <ErrorDePantalla onReintentar={refetch} />;

  const { analisis, generacion } = data;
  const faltanSesiones = data.sesiones < data.sesiones_necesarias;
  const sinCupo = data.restantes <= 0;

  return (
    <>
      <PageHeader
        kicker="Con ayuda de la IA"
        titulo="Análisis de progreso"
        entradilla="Lee tus métricas y te dice qué cambiar."
      >
        <Badge tono={sinCupo ? "down" : "record"}>
          <span className="num">{data.restantes}</span> restante
          {data.restantes === 1 ? "" : "s"} esta hora
        </Badge>
        <Button
          variante="primary"
          disabled={sinCupo || faltanSesiones || pedir.isPending}
          onClick={() => pedir.mutate()}
        >
          {pedir.isPending
            ? "Analizando…"
            : analisis
              ? "Analizar de nuevo"
              : "Analizar ahora"}
        </Button>
      </PageHeader>

      {pedir.error && (
        <div className="mb-4">
          <Aviso
            tono={codigoDe(pedir.error) === "sin_datos" ? "informacion" : "error"}
            urgente={codigoDe(pedir.error) !== "sin_datos"}
          >
            {pedir.error instanceof Error
              ? pedir.error.message
              : "No se ha podido completar el análisis."}
          </Aviso>
        </div>
      )}

      {faltanSesiones && (
        <Card className="mb-4">
          <p className="section-kicker">Todavía no</p>
          <h2 className="mb-3">Hacen falta más entrenamientos</h2>
          <ProgressBar
            etiqueta="Entrenamientos registrados"
            hecho={data.sesiones}
            total={data.sesiones_necesarias}
            unidad="sesiones"
          />
          <p className="body-sm mt-3 text-ink-muted">
            Con menos, el análisis solo podría decirte que entrenes más — y eso ya lo sabes. El
            análisis también se ejecuta solo, una vez por semana, en cuanto haya con qué.
          </p>
          <div className="mt-4">
            <EnlaceBoton a="/plan/" variante="secondary" tamano="sm">
              Ir a entrenar
            </EnlaceBoton>
          </div>
        </Card>
      )}

      {!analisis ? (
        !faltanSesiones && (
          <EmptyState titulo="Todavía no has pedido ningún análisis">
            Pulsa «Analizar ahora» y la IA leerá tus métricas de las últimas semanas.
          </EmptyState>
        )
      ) : (
        <>
          <Pestanas
            etiqueta="Secciones del análisis"
            valor={vista}
            onCambio={setVista}
            opciones={[
              { valor: "lectura", etiqueta: "Lectura" },
              {
                valor: "estancamientos",
                etiqueta: "Estancamientos",
                marca: <Cuantos n={analisis.stalled.length} />,
              },
              {
                valor: "cambios",
                etiqueta: "Cambios",
                marca: <Cuantos n={analisis.proposed_changes.length} />,
              },
            ]}
          >
            {vista === "lectura" && <PanelDeLectura analisis={analisis} />}
            {vista === "estancamientos" && <PanelDeEstancamientos analisis={analisis} />}
            {vista === "cambios" && <PanelDeCambios analisis={analisis} />}
          </Pestanas>

          {generacion && (
            <p className="caption mt-4 text-ink-muted">
              Generado el {FECHA.format(new Date(generacion.fecha))} con {generacion.modelo} ·{" "}
              <span className="num">
                {generacion.tokens_entrada}+{generacion.tokens_salida}
              </span>{" "}
              tokens.
            </p>
          )}
        </>
      )}
    </>
  );
}
