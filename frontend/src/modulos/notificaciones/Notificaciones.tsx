import { useState } from "react";
import { Link } from "react-router";

import {
  useMarcarLeida,
  useMarcarTodasLeidas,
  useNotificaciones,
  useSinLeer,
  type Notificacion,
} from "@/api/notificaciones";
import { Badge } from "@/ds/Badge";
import { Button, EnlaceBoton } from "@/ds/Button";
import { PageHeader } from "@/ds/Card";
import { EmptyState } from "@/ds/EmptyState";
import { ErrorDePantalla } from "@/ds/estados";
import { Icono } from "@/ds/Icono";
import { Paginacion } from "@/ds/Paginacion";
import { Pestanas, useVista } from "@/ds/Pestanas";

const VISTAS = ["todas", "sin-leer"] as const;

const FECHA_Y_HORA = new Intl.DateTimeFormat("es-ES", {
  day: "numeric",
  month: "short",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
});

const CON_ANALISIS = new Set(["stall_detected", "progress_ready"]);

const ICONO_POR_TIPO = {
  stall_detected: "diana",
  weight_off_track: "bascula",
  progress_ready: "trofeo",
  routine_ready: "plan",
} as const;

function Tarjeta({ aviso }: { aviso: Notificacion }) {
  const marcar = useMarcarLeida();

  return (
    <div className={`notification-card ${aviso.is_read ? "" : "border border-primary"}`.trim()}>
      <span className="notification-mark" data-tipo={aviso.kind} aria-hidden="true">
        <Icono nombre={ICONO_POR_TIPO[aviso.kind]} />
      </span>

      <div className="min-w-0">
        <div className="mb-2 flex flex-wrap items-start justify-between gap-2">
          <h2 className="flex items-center gap-2">
            {!aviso.is_read && (
              <>
                <span className="size-2 shrink-0 rounded-full bg-primary" aria-hidden="true" />
                <span className="sr-only">Sin leer:</span>
              </>
            )}
            {aviso.title}
          </h2>

          <div className="flex items-center gap-2">
            <Badge tono={aviso.severity === "warning" ? "warn" : "info"}>{aviso.kind_label}</Badge>
            {!aviso.is_read && (
              <Button
                variante="secondary"
                tamano="sm"
                disabled={marcar.isPending}
                onClick={() => marcar.mutate(aviso.id)}
              >
                Marcar leída
              </Button>
            )}
          </div>
        </div>

        <div className="body-sm whitespace-pre-line">{aviso.body}</div>

        <p className="caption mt-3 text-ink-muted">
          {FECHA_Y_HORA.format(new Date(aviso.created_at))}
          {aviso.emailed_at && " · enviada por correo"}
          {CON_ANALISIS.has(aviso.kind) && (
            <>
              {" · "}
              <Link to="/ia/analisis/">Ver el análisis completo</Link>
            </>
          )}
        </p>
      </div>
    </div>
  );
}

function ListaDeAvisos({ soloSinLeer }: { soloSinLeer: boolean }) {
  const [pagina, setPagina] = useState(1);
  const { data, isPending, error, refetch } = useNotificaciones(pagina, soloSinLeer);

  if (isPending) return <div className="min-h-64" aria-busy="true" aria-label="Cargando" />;
  if (error || !data) return <ErrorDePantalla onReintentar={refetch} />;

  if (!data.results.length) {
    return soloSinLeer ? (
      <EmptyState titulo="Estás al día" glifo={<Icono nombre="comprobado" className="size-6" />}>
        No tienes avisos sin leer.
      </EmptyState>
    ) : (
      <EmptyState
        titulo="No tienes notificaciones"
        glifo={<Icono nombre="campana" />}
        acciones={
          <EnlaceBoton a="/progreso/" variante="secondary" tamano="sm">
            Ver mi progreso
          </EnlaceBoton>
        }
      >
        Aquí aparecerán los avisos de estancamiento y las desviaciones de tu peso.
      </EmptyState>
    );
  }

  return (
    <>
      <div className="card-list">
        {data.results.map((aviso) => (
          <Tarjeta aviso={aviso} key={aviso.id} />
        ))}
      </div>
      <Paginacion
        pagina={pagina}
        total={data.total_pages}
        hayAnterior={Boolean(data.previous)}
        haySiguiente={Boolean(data.next)}
        onCambio={setPagina}
      />
    </>
  );
}

export function Notificaciones() {
  const [vista, setVista] = useVista(VISTAS);
  const { data: sinLeer = 0 } = useSinLeer();
  const todas = useMarcarTodasLeidas();

  return (
    <>
      <PageHeader
        kicker="Centro de señales"
        titulo="Notificaciones"
        hero="primary"
        entradilla="Cambios importantes, sin mezclar con el resto."
      >
        {sinLeer > 0 && (
          <Button
            variante="secondary"
            tamano="sm"
            disabled={todas.isPending}
            onClick={() => todas.mutate()}
          >
            Marcar todas como leídas
          </Button>
        )}
      </PageHeader>

      <Pestanas
        etiqueta="Qué avisos ver"
        valor={vista}
        onCambio={setVista}
        opciones={[
          { valor: "todas", etiqueta: "Todas" },
          {
            valor: "sin-leer",
            etiqueta: "Sin leer",
            marca: sinLeer > 0 ? <span className="num text-primary">{sinLeer}</span> : undefined,
          },
        ]}
      >
        <ListaDeAvisos soloSinLeer={vista === "sin-leer"} />
      </Pestanas>
    </>
  );
}
