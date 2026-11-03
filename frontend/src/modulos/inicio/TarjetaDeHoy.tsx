import type { ReactNode } from "react";
import { useNavigate } from "react-router";

import { Button, EnlaceBoton } from "@/ds/Button";
import { Icono } from "@/ds/Icono";
import { useEmpezar } from "@/modulos/entrenar/api";

import type { HoyToca } from "./api";

const DIA_Y_MES = new Intl.DateTimeFormat("es-ES", { day: "numeric", month: "long" });

export function comoFecha(iso: string): Date {
  const [anio, mes, dia] = iso.split("-").map(Number);
  return new Date(anio!, mes! - 1, dia!);
}

export function BotonDeEmpezar({
  etiqueta,
  variante,
  rutina,
  bloque = false,
}: {
  etiqueta: string;
  variante: "primary" | "secondary";
  rutina?: number;
  bloque?: boolean;
}) {
  const navegar = useNavigate();
  const empezar = useEmpezar();

  return (
    <Button
      variante={variante}
      tamano="lg"
      bloque={bloque}
      disabled={empezar.isPending}
      onClick={() =>
        empezar.mutate(rutina, {
          onSuccess: (sesion) => navegar(`/entrenamientos/${sesion.id}/`),
        })
      }
    >
      {variante === "primary" && <Icono nombre="entrenar" className="size-5" />}
      {empezar.isPending ? "Empezando…" : etiqueta}
    </Button>
  );
}

function Marco({
  kicker,
  titulo,
  detalle,
  accion,
}: {
  kicker: string;
  titulo: string;
  detalle?: ReactNode;
  accion: ReactNode;
}) {
  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div className="min-w-0">
        <p className="section-kicker">{kicker}</p>
        <p className="title-lg">{titulo}</p>
        {detalle && <p className="body-sm mt-1 line-clamp-2 text-ink-muted">{detalle}</p>}
      </div>
      <div className="shrink-0 [&>*]:w-full sm:[&>*]:w-auto">{accion}</div>
    </div>
  );
}

export function QueTocaHoy({ toca, hoy }: { toca: HoyToca; hoy: string }) {
  if (toca.estado === "sesion_abierta" && toca.sesion) {
    return (
      <Marco
        kicker="Sin terminar"
        titulo={`Entrenamiento del ${DIA_Y_MES.format(comoFecha(toca.sesion.fecha))}`}
        detalle="Lo dejaste a medias: sigue donde lo dejaste."
        accion={
          <EnlaceBoton a={`/entrenamientos/${toca.sesion.id}/`} variante="primary" tamano="lg">
            Continuar
          </EnlaceBoton>
        }
      />
    );
  }

  if (toca.estado === "sin_programa") {
    return (
      <Marco
        kicker="Para empezar"
        titulo="Todavía no tienes un plan"
        detalle="Elige qué rutina va cada día y la aplicación te dirá qué toca."
        accion={
          <EnlaceBoton a="/plan/" variante="primary" tamano="lg">
            Montar mi semana
          </EnlaceBoton>
        }
      />
    );
  }

  if (toca.estado === "descanso") {
    return (
      <Marco
        kicker="Hoy"
        titulo="Descanso"
        detalle="El músculo crece mientras descansa."
        accion={<BotonDeEmpezar etiqueta="Entrenar igualmente" variante="secondary" />}
      />
    );
  }

  const rutina = toca.rutina!;
  return (
    <Marco
      kicker={`Hoy · ${DIA_Y_MES.format(comoFecha(hoy))}`}
      titulo={rutina.nombre}
      detalle={
        rutina.ejercicios.length ? rutina.ejercicios.join(" · ") : "Sin ejercicios todavía"
      }
      accion={
        rutina.ejercicios.length ? (
          <BotonDeEmpezar etiqueta="Empezar" variante="primary" rutina={rutina.id} />
        ) : (
          <EnlaceBoton a={`/rutinas/${rutina.id}/`} variante="secondary" tamano="lg">
            Añadir ejercicios
          </EnlaceBoton>
        )
      }
    />
  );
}
