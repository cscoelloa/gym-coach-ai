import { useState, type ReactNode } from "react";
import { useNavigate } from "react-router";

import { useSalir, type UsuarioDeSesion } from "@/api/sesion";
import { useAvisos } from "@/lib/avisos";
import { useConfirmarSalida } from "@/lib/cambiosPendientes";
import { useInstalacion } from "@/lib/instalar";

import { Aviso } from "./Aviso";
import { Button } from "./Button";
import { Icono, type NombreDeIcono } from "./Icono";
import { Panel } from "./Panel";
import { ThemeToggle } from "./ThemeToggle";

function inicial(usuario: UsuarioDeSesion): string {
  return (usuario.first_name || usuario.username).trim().charAt(0) || "·";
}

function Fila({
  icono,
  children,
  onClick,
}: {
  icono: NombreDeIcono;
  children: ReactNode;
  onClick: () => void;
}) {
  return (
    <button type="button" className="compact-row" onClick={onClick}>
      <span className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-primary-soft text-primary">
        <Icono nombre={icono} className="size-[18px]" />
      </span>
      <span className="flex-1">{children}</span>
      <Icono nombre="chevronDerecha" className="size-4" />
    </button>
  );
}

function FilaDeAvisos() {
  const avisos = useAvisos();
  if (avisos.estado === "no" || avisos.estado === "cargando") return null;

  const activo = avisos.estado === "activo";
  const bloqueado = avisos.estado === "bloqueado" || avisos.estado === "instalar";

  return (
    <>
      <div className="compact-list mt-4">
        <button
          type="button"
          role="switch"
          aria-checked={activo}
          className="compact-row disabled:opacity-60"
          disabled={avisos.ocupado || bloqueado}
          onClick={() => void (activo ? avisos.desactivar() : avisos.activar())}
        >
          <span className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-data-soft text-data">
            <Icono nombre="campana" className="size-[18px]" />
          </span>
          <span className="flex-1">Avisarme al acabar el descanso</span>
          <span className="switch" data-on={activo ? "true" : "false"} aria-hidden="true" />
        </button>
      </div>
      {avisos.estado === "bloqueado" && (
        <p className="body-sm mt-2 px-4 text-ink-muted">
          Los avisos están bloqueados en los ajustes del navegador. Permítelos ahí para activarlos.
        </p>
      )}
      {avisos.estado === "instalar" && (
        <p className="body-sm mt-2 px-4 text-ink-muted">
          En iPhone y iPad los avisos llegan solo con la aplicación instalada.
        </p>
      )}
      {avisos.resultado === "actualizar" && (
        <p className="body-sm mt-2 px-4 text-ink-muted">
          Actualiza la aplicación para poder activarlos.
        </p>
      )}
      {avisos.resultado === "error" && (
        <p className="body-sm mt-2 px-4 text-danger">
          No se pudieron activar. Inténtalo más tarde.
        </p>
      )}
    </>
  );
}

export function Cuenta({
  usuario,
  variante = "boton",
}: {
  usuario: UsuarioDeSesion;
  variante?: "boton" | "avatar";
}) {
  const [abierto, setAbierto] = useState(false);
  const [pasos, setPasos] = useState(false);
  const { modo, instalar } = useInstalacion();
  const salir = useSalir();
  const navegar = useNavigate();
  const guardia = useConfirmarSalida();

  function ir(url: string) {
    setAbierto(false);
    navegar(url);
  }

  async function cerrarSesion() {
    if (!(await guardia.confirmar())) return;
    salir.mutate(undefined, {
      onSuccess: () => {
        guardia.limpiar();
        navegar("/sesion-cerrada/", { replace: true });
      },
    });
  }

  return (
    <>
      {variante === "avatar" ? (
        <button
          type="button"
          className="icon-button account-trigger"
          onClick={() => setAbierto(true)}
          aria-haspopup="dialog"
          aria-label="Cuenta"
        >
          <span className="avatar" aria-hidden="true">
            {inicial(usuario)}
          </span>
        </button>
      ) : (
        <button
          type="button"
          className="side-link account-trigger"
          onClick={() => setAbierto(true)}
          aria-haspopup="dialog"
        >
          <span className="avatar size-6 text-[12px]/[16px]" aria-hidden="true">
            {inicial(usuario)}
          </span>
          Cuenta
        </button>
      )}

      {abierto && (
        <Panel titulo="Tu cuenta" onCerrar={() => setAbierto(false)}>
          <div className="mb-6 flex items-center gap-3">
            <span className="avatar size-14 text-[24px]/[28px]" aria-hidden="true">
              {inicial(usuario)}
            </span>
            <div className="min-w-0">
              <p className="title-md truncate">{usuario.first_name || usuario.username}</p>
              <p className="body-sm truncate text-ink-muted">@{usuario.username}</p>
            </div>
          </div>

          <div className="compact-list">
            <Fila icono="persona" onClick={() => ir("/perfil/")}>
              Perfil
            </Fila>
            <Fila icono="campana" onClick={() => ir("/notificaciones/")}>
              Notificaciones
            </Fila>
            {usuario.is_staff && (
              <Fila icono="escudo" onClick={() => ir("/gestion/")}>
                Gestión
              </Fila>
            )}
          </div>

          {modo && (
            <>
              <div className="compact-list mt-4">
                <Fila
                  icono="instalar"
                  onClick={() => (modo === "prompt" ? void instalar() : setPasos(!pasos))}
                >
                  Instalar la aplicación
                </Fila>
              </div>
              {modo === "ios" && pasos && (
                <ol className="mt-3 space-y-2 rounded-xl bg-surface-100 p-4 text-[15px]/[20px]">
                  <li className="flex items-center gap-2">
                    <span className="num font-semibold text-ink-subtle">1</span>
                    Toca <Icono nombre="compartir" className="size-5 text-primary" />
                    <span className="font-semibold">Compartir</span> en la barra de Safari.
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="num font-semibold text-ink-subtle">2</span>
                    Elige <span className="font-semibold">Añadir a pantalla de inicio</span>.
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="num font-semibold text-ink-subtle">3</span>
                    Pulsa <span className="font-semibold">Añadir</span>.
                  </li>
                </ol>
              )}
            </>
          )}

          <FilaDeAvisos />

          <p className="section-kicker mt-6 px-4">Apariencia</p>
          <ThemeToggle />

          <div className="mt-8">
            {salir.error && (
              <Aviso tono="error" urgente>
                No se pudo cerrar sesión. Inténtalo de nuevo.
              </Aviso>
            )}
            <Button variante="danger" bloque disabled={salir.isPending} onClick={cerrarSesion}>
              {salir.isPending ? "Cerrando sesión…" : "Cerrar sesión"}
            </Button>
          </div>
        </Panel>
      )}
    </>
  );
}
