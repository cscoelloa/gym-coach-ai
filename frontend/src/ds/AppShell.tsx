import type { ReactNode } from "react";
import { useLocation } from "react-router";

import { useSinLeer } from "@/api/notificaciones";
import { type UsuarioDeSesion } from "@/api/sesion";
import { useDescanso } from "@/lib/descanso";
import { ProveedorDeMarco, useMarco } from "@/lib/marco";

import { AvisoDeActualizacion } from "./AvisoDeActualizacion";
import { AvisoDeConexion } from "./AvisoDeConexion";
import { Cuenta } from "./Cuenta";
import { DescansoEnCurso } from "./DescansoEnCurso";
import { EnlaceDeDestino } from "./EnlaceDeDestino";
import { GestoDeVolver } from "./GestoDeVolver";
import { Icono } from "./Icono";
import { Marca } from "./Marca";
import { DESTINOS, esDestino, type Destino } from "./navegacion";
import { useVolver } from "./useVolver";

type Contexto = "app" | "gestion";

function estaActivo(destino: Destino, camino: string): boolean {
  if (destino.url === "/") return camino === "/";
  return camino.startsWith(destino.url);
}

function Campana({ className = "" }: { className?: string }) {
  const { data: sinLeer = 0 } = useSinLeer();

  return (
    <EnlaceDeDestino a="/notificaciones/" className={`icon-button ${className}`.trim()}>
      <Icono nombre="campana" className="size-[22px]" />
      <span className="sr-only">Avisos</span>
      {sinLeer > 0 && (
        <span className="icon-badge">
          {sinLeer > 99 ? "99+" : sinLeer}
          <span className="sr-only"> sin leer</span>
        </span>
      )}
    </EnlaceDeDestino>
  );
}

function Atras() {
  const { etiqueta, volver } = useVolver();

  return (
    <button type="button" className="btn-back" onClick={volver}>
      <Icono nombre="chevronIzquierda" className="size-6 shrink-0" />
      <span className="truncate">{etiqueta}</span>
    </button>
  );
}

function BarraSuperior({ usuario }: { usuario: UsuarioDeSesion }) {
  const { pathname } = useLocation();
  const { titulo, compacta } = useMarco();
  const conAtras = !esDestino(pathname);
  const descanso = useDescanso();
  const conFila = conAtras || (descanso !== null && descanso.sesionId !== null);

  return (
    <header className="app-bar" data-compacta={compacta && titulo ? "true" : "false"}>
      <div className={`app-bar-row ${conFila ? "" : "lg:hidden"}`.trim()}>
        <div className="flex min-w-0 items-center">{conAtras && <Atras />}</div>

        <div className="min-w-0">
          {compacta && titulo && (
            <p className="app-bar-title" aria-hidden="true">
              {titulo}
            </p>
          )}
        </div>

        <div className="flex items-center justify-end gap-0.5">
          <DescansoEnCurso />
          <div className="flex items-center gap-0.5 lg:hidden">
            <Campana />
            <Cuenta usuario={usuario} variante="avatar" />
          </div>
        </div>
      </div>
      <AvisoDeConexion />
    </header>
  );
}

function BarraLateral({ usuario }: { usuario: UsuarioDeSesion }) {
  const { pathname } = useLocation();
  const { data: sinLeer = 0 } = useSinLeer();

  return (
    <aside className="app-sidebar side-rail fixed inset-y-0 left-0 z-30 hidden w-20 flex-col px-2 py-5 lg:flex xl:w-64 xl:px-3">
      <EnlaceDeDestino
        a="/"
        className="mb-8 flex items-center justify-center gap-3 hover:no-underline xl:justify-start xl:px-3"
      >
        <Marca />
      </EnlaceDeDestino>

      <p className="nav-group-label">Tu entrenamiento</p>
      <nav className="flex flex-col gap-0.5" aria-label="Principal">
        {DESTINOS.map((destino) => {
          const activo = estaActivo(destino, pathname);
          return (
            <EnlaceDeDestino
              key={destino.clave}
              a={destino.url}
              className={`side-link ${activo ? "side-link-on" : ""}`}
              {...(activo ? { "aria-current": "page" as const } : {})}
            >
              <Icono nombre={destino.icono} className="size-5 shrink-0" />
              {destino.etiqueta}
            </EnlaceDeDestino>
          );
        })}
      </nav>

      <div className="mt-auto flex flex-col gap-0.5 border-t border-line pt-4">
        <EnlaceDeDestino a="/notificaciones/" className="side-link">
          <Icono nombre="campana" className="size-5 shrink-0" />
          Avisos
          {sinLeer > 0 && (
            <span className="badge badge-warn ml-auto">
              {sinLeer}
              <span className="sr-only"> sin leer</span>
            </span>
          )}
        </EnlaceDeDestino>

        <EnlaceDeDestino a="/perfil/" className="side-link">
          <Icono nombre="persona" className="size-5 shrink-0" />
          <span className="truncate">{usuario.username}</span>
        </EnlaceDeDestino>

        {usuario.is_staff && (
          <>
            <EnlaceDeDestino a="/gestion/" className="side-link">
              <Icono nombre="escudo" className="size-5 shrink-0" />
              Gestión
            </EnlaceDeDestino>
            <EnlaceDeDestino a="/admin/" className="side-link">
              <Icono nombre="escudo" className="size-5 shrink-0" />
              Admin de Django
            </EnlaceDeDestino>
          </>
        )}

        <Cuenta usuario={usuario} />
      </div>
    </aside>
  );
}

function BarraDePestanas() {
  const { pathname } = useLocation();

  return (
    <nav className="tab-bar" aria-label="Principal">
      <div className="mx-auto grid max-w-lg grid-cols-5">
        {DESTINOS.map((destino) => {
          const activo = estaActivo(destino, pathname);
          return (
            <EnlaceDeDestino
              key={destino.clave}
              a={destino.url}
              className={`tab-link ${activo ? "tab-link-on" : ""}`}
              {...(activo ? { "aria-current": "page" as const } : {})}
            >
              <Icono nombre={destino.icono} className="size-6 shrink-0" />
              {destino.etiqueta}
            </EnlaceDeDestino>
          );
        })}
      </div>
    </nav>
  );
}

export function AppShell({
  usuario,
  children,
  contexto = "app",
}: {
  usuario: UsuarioDeSesion;
  children: ReactNode;
  contexto?: Contexto;
}) {
  const { pathname } = useLocation();

  return (
    <ProveedorDeMarco>
      <BarraLateral usuario={usuario} />

      <div className="lg:pl-20 xl:pl-64">
        <BarraSuperior usuario={usuario} />

        <main className="app-main pt-2 lg:pt-10">
          <div className="mx-auto max-w-6xl">{children}</div>
        </main>
      </div>

      {contexto === "app" && <BarraDePestanas />}
      {!esDestino(pathname) && <GestoDeVolver />}
      <AvisoDeActualizacion />
    </ProveedorDeMarco>
  );
}
