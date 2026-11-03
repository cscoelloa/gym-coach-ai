import { useState } from "react";
import { useParams } from "react-router";

import { useUnRato } from "@/ds/AvisoPasajero";
import { Badge } from "@/ds/Badge";
import { Button, EnlaceBoton } from "@/ds/Button";
import { Campo } from "@/ds/Campo";
import { Card, Pill } from "@/ds/Card";
import { Cargando, ErrorDePantalla } from "@/ds/estados";
import { Icono } from "@/ds/Icono";
import { NotaDeStat, StatTile } from "@/ds/StatTile";
import { useTituloDeLaPantalla } from "@/lib/marco";

import { useGuardarNotas, useResumenDeCierre } from "./api";

const FECHA_LARGA = new Intl.DateTimeFormat("es-ES", {
  weekday: "long",
  day: "numeric",
  month: "long",
});

function comoFecha(iso: string): Date {
  const [anio, mes, dia] = iso.split("-").map(Number);
  return new Date(anio!, mes! - 1, dia!);
}

export function CierreDeEntrenamiento() {
  const { id = "" } = useParams();
  const sesionId = Number(id);
  const { data, isPending, error, refetch } = useResumenDeCierre(sesionId);
  const guardar = useGuardarNotas(sesionId);
  const verGuardado = useUnRato(guardar.isSuccess && guardar.submittedAt);
  const [notas, setNotas] = useState<string | null>(null);
  const titulo = data?.sesion.rutina ?? "Entrenamiento libre";
  const observar = useTituloDeLaPantalla(titulo);

  if (isPending) return <Cargando />;
  if (error || !data) return <ErrorDePantalla onReintentar={refetch} />;

  const texto = notas ?? data.sesion.notas;

  return (
    <div className="mx-auto max-w-2xl lg:max-w-5xl">
      <header className="mb-6 flex flex-col items-center text-center">
        <span className="mb-4 flex size-16 items-center justify-center rounded-full bg-success-soft text-success">
          <Icono nombre="comprobado" className="size-9" />
        </span>
        <p className="section-kicker">Entrenamiento terminado</p>
        <h1 ref={observar}>
          {titulo}
        </h1>
        <p className="body-sm mt-1 text-ink-muted first-letter:uppercase">
          {FECHA_LARGA.format(comoFecha(data.sesion.fecha))}
        </p>
      </header>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-[minmax(0,7fr)_minmax(0,5fr)] lg:items-start">
        <div>
          {data.records.length > 0 && (
            <Card className="card-accent mb-4">
              <p className="section-kicker">
                {data.records.length === 1 ? "Récord personal" : "Récords personales"}
              </p>
              <ul className="mt-2 space-y-2">
                {data.records.map((record) => (
                  <li className="flex items-center justify-between gap-3" key={record.ejercicio}>
                    <span className="title-sm">{record.ejercicio}</span>
                    <Badge tono="record">
                      <span className="num">{record.kg}</span> kg
                    </Badge>
                  </li>
                ))}
              </ul>
            </Card>
          )}

          <div className="grid grid-cols-2 gap-3">
            <StatTile
              etiqueta="Duración"
              icono="reloj"
              tono="data"
              valor={data.duracion_minutos}
              unidad="min"
              vacio="Sin hora de inicio."
            />
            <StatTile etiqueta="Series" valor={data.series} icono="entrenar">
              <NotaDeStat>
                en {data.ejercicios} ejercicio{data.ejercicios === 1 ? "" : "s"}
              </NotaDeStat>
            </StatTile>
            <StatTile
              etiqueta="Tonelaje"
              icono="mancuerna"
              tono="data"
              valor={data.tonelaje_kg.toLocaleString("es-ES")}
              unidad="kg"
            >
              {data.series_sin_cobertura > 0 && (
                <NotaDeStat>
                  {data.series_sin_cobertura} serie
                  {data.series_sin_cobertura === 1 ? "" : "s"} sin peso corporal registrado
                </NotaDeStat>
              )}
            </StatTile>
            <StatTile
              etiqueta="Récords"
              icono="trofeo"
              tono="warning"
              valor={data.records.length || null}
              vacio="Ninguno hoy."
            />
          </div>

          {data.musculos.length > 0 && (
            <Card className="mt-4">
              <p className="section-kicker">Lo que has trabajado</p>
              <div className="mt-2 flex flex-wrap gap-2">
                {data.musculos.map((musculo) => (
                  <Pill key={musculo}>{musculo}</Pill>
                ))}
              </div>
            </Card>
          )}
        </div>

        <div>
          <Card className="mt-4 lg:mt-0">
            <h2 className="title-md mb-3">Notas</h2>
            <Campo
              etiqueta="Cómo ha ido"
              multilinea
              value={texto}
              onChange={(evento) => setNotas(evento.target.value)}
              ayuda="Lo que escribas aquí lo lee la IA al analizar tu progreso."
            />
            <div className="form-actions">
              <Button
                variante="secondary"
                disabled={guardar.isPending || texto === data.sesion.notas}
                onClick={() => guardar.mutate(texto)}
              >
                {guardar.isPending ? "Guardando…" : "Guardar notas"}
              </Button>
              {verGuardado && (
                <span role="status" className="aviso-pasajero body-sm text-success">
                  Guardado.
                </span>
              )}
            </div>
          </Card>

          <div className="mt-6 flex flex-col gap-2 sm:flex-row sm:flex-wrap lg:flex-col">
            <EnlaceBoton a="/" variante="primary" tamano="lg">
              Volver a Inicio
            </EnlaceBoton>
            <EnlaceBoton a="/entrenamientos/" variante="secondary" tamano="lg">
              Ver el historial
            </EnlaceBoton>
            <EnlaceBoton a="/progreso/" variante="ghost" tamano="lg">
              Mi progreso
            </EnlaceBoton>
          </div>
        </div>
      </div>
    </div>
  );
}
