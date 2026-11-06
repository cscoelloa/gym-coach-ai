import { useState } from "react";

import { Anillo } from "@/ds/Anillo";
import { Badge } from "@/ds/Badge";
import { BodyMap } from "@/ds/BodyMap";
import { Button, EnlaceBoton } from "@/ds/Button";
import { Card } from "@/ds/Card";
import { Cargando, ErrorDePantalla } from "@/ds/estados";
import { GraficaDePeso } from "@/ds/GraficaDePeso";
import { Icono } from "@/ds/Icono";
import { Placa } from "@/ds/Marca";
import { WeekStrip } from "@/ds/WeekStrip";
import { useInstalacion } from "@/lib/instalar";
import { useTituloDeLaPantalla } from "@/lib/marco";

import { useInicio } from "./api";
import { comoFecha, QueTocaHoy } from "./TarjetaDeHoy";

const FECHA_LARGA = new Intl.DateTimeFormat("es-ES", {
  weekday: "long",
  day: "numeric",
  month: "long",
});

const DIA_Y_MES_CORTO = new Intl.DateTimeFormat("es-ES", { day: "numeric", month: "short" });

const CLAVE_INSTALAR = "gym-instalar-descartado";

function leerDescartado(): boolean {
  try {
    return localStorage.getItem(CLAVE_INSTALAR) === "1";
  } catch {
    return false;
  }
}

function TarjetaDeInstalar() {
  const { modo, instalar } = useInstalacion();
  const [descartada, setDescartada] = useState(leerDescartado);
  const [pasos, setPasos] = useState(false);

  if (!modo || descartada) return null;

  function descartar() {
    setDescartada(true);
    try {
      localStorage.setItem(CLAVE_INSTALAR, "1");
    } catch {
    }
  }

  return (
    <Card className="flex items-start gap-3">
      <Placa className="size-12" />
      <div className="min-w-0 flex-1">
        <p className="title-sm">Instala la aplicación</p>
        <p className="body-sm mt-0.5 text-ink-muted">
          Se abre desde la pantalla de inicio, a pantalla completa y también sin conexión.
        </p>
        {modo === "ios" && pasos && (
          <p className="body-sm mt-2 flex flex-wrap items-center gap-1">
            Toca <Icono nombre="compartir" className="size-5 text-primary" /> Compartir y luego
            <span className="font-semibold">«Añadir a pantalla de inicio»</span>.
          </p>
        )}
        <div className="mt-3 flex gap-2">
          <Button
            variante="primary"
            tamano="sm"
            onClick={() => (modo === "prompt" ? void instalar() : setPasos(true))}
          >
            {modo === "prompt" ? "Instalar" : "Cómo se hace"}
          </Button>
          <Button variante="ghost" tamano="sm" onClick={descartar}>
            Ahora no
          </Button>
        </div>
      </div>
    </Card>
  );
}

export function Inicio() {
  const { data, isPending, error, refetch } = useInicio();
  const observar = useTituloDeLaPantalla("Tu semana");

  if (isPending) return <Cargando />;
  if (error || !data) return <ErrorDePantalla onReintentar={refetch} />;

  const hoy = comoFecha(data.hoy);
  const { peso, racha } = data;

  return (
    <>
      <header className="mb-5">
        <span className="hero-kicker">{FECHA_LARGA.format(hoy)}</span>
        <h1 ref={observar}>Tu semana</h1>
      </header>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <section className="hero lg:col-span-2">
          <h2 className="sr-only">Lo de hoy</h2>
          <QueTocaHoy toca={data.hoy_toca} hoy={data.hoy} />

          <div className="mt-5 border-t border-line pt-5">
            <WeekStrip
              dias={data.semana.map((dia) => ({
                inicial: dia.inicial,
                numero: dia.numero,
                hoy: dia.hoy,
                futuro: dia.futuro,
                entrenado: dia.entrenado,
                planificado: dia.planificado,
              }))}
            />
          </div>
        </section>

        <Card className="card-logro flex flex-wrap items-center gap-x-5 gap-y-4 lg:col-span-2">
          <Anillo
            hecho={racha.hechas_esta_semana}
            total={racha.planificadas_esta_semana}
            etiqueta={
              racha.planificadas_esta_semana > 0
                ? `${racha.hechas_esta_semana} de ${racha.planificadas_esta_semana} entrenamientos esta semana`
                : `${racha.hechas_esta_semana} entrenamientos esta semana`
            }
          >
            <span className="metric-md">{racha.hechas_esta_semana}</span>
            {racha.planificadas_esta_semana > 0 && (
              <span className="caption text-ink-muted">
                de <span className="num">{racha.planificadas_esta_semana}</span>
              </span>
            )}
          </Anillo>

          <div className="min-w-0 flex-1">
            <h2 className="title-md">Constancia</h2>
            <p className="mt-1 flex items-baseline gap-1.5">
              <Icono nombre="fuego" className="size-5 self-center text-primary" />
              <span className="metric-xl">{racha.semanas}</span>
              <span className="stat-tile-unit">
                semana{racha.semanas === 1 ? "" : "s"} seguida{racha.semanas === 1 ? "" : "s"}
              </span>
            </p>
            <p className="body-sm text-ink-muted">
              <span className="num">{racha.total_sesiones}</span> entrenamiento
              {racha.total_sesiones === 1 ? "" : "s"} en total
            </p>
          </div>

          <div className="basis-full sm:basis-auto">
            <EnlaceBoton a="/progreso/" variante="secondary" tamano="sm">
              Ver mi progreso
            </EnlaceBoton>
          </div>
        </Card>

        <div className="lg:col-span-2 empty:hidden">
          <TarjetaDeInstalar />
        </div>

        <Card>
          <div className="mb-3 flex items-center justify-between gap-2">
            <h2 className="title-md">Peso corporal</h2>
            <EnlaceBoton a="/peso/" variante="secondary" tamano="sm">
              Registrar
            </EnlaceBoton>
          </div>

          {peso.ultimo ? (
            <>
              <div className="flex flex-wrap items-baseline gap-x-2">
                <span className="metric-xl">{peso.ultimo.kg}</span>
                <span className="stat-tile-unit">kg</span>

                {peso.cambio !== null && peso.cambio !== 0 && (
                  <Badge tono={peso.cambio > 0 ? "warn" : "done"}>
                    {peso.cambio > 0 ? "↑" : "↓"} {Math.abs(peso.cambio).toFixed(1)}
                  </Badge>
                )}

                <span className="metric-sm ml-auto text-ink-muted">
                  {DIA_Y_MES_CORTO.format(comoFecha(peso.ultimo.fecha))}
                </span>
              </div>

              <p className="body-sm mt-1 text-ink-muted">
                {peso.objetivo}
                {peso.meta_kg !== null && ` · meta ${peso.meta_kg} kg`}
              </p>

              {peso.serie ? (
                <div className="mt-3">
                  <GraficaDePeso serie={peso.serie} />
                </div>
              ) : (
                <p className="empty-hint mt-3">Con dos registros o más verás aquí la tendencia.</p>
              )}
            </>
          ) : (
            <div className="empty-state">
              <span className="empty-glyph" aria-hidden="true">
                <Icono nombre="bascula" />
              </span>
              <span className="empty-title">Sin registros de peso</span>
              <p>Anota tu peso de hoy y en dos días ya verás la tendencia.</p>
              <EnlaceBoton a="/peso/" variante="primary" tamano="sm">
                Registrar el primero
              </EnlaceBoton>
            </div>
          )}
        </Card>

        <Card>
          <div className="mb-3 flex items-center justify-between gap-2">
            <h2 className="title-md">Esta semana</h2>
            <EnlaceBoton a="/progreso/" variante="secondary" tamano="sm">
              Detalle
            </EnlaceBoton>
          </div>
          <BodyMap
            niveles={data.mapa_corporal}
            compacto
            leyenda="Cuanto más encendido, más series efectivas llevas"
          />
        </Card>

      </div>
    </>
  );
}
