import { Suspense, type ReactNode } from "react";
import { Navigate, Route, Routes, useLocation } from "react-router";

import { useSesion } from "@/api/sesion";
import { AppShell } from "@/ds/AppShell";
import { AvisoDeConexion } from "@/ds/AvisoDeConexion";
import { EnlaceBoton } from "@/ds/Button";
import { EmptyState } from "@/ds/EmptyState";
import { Cargando, SinConexion } from "@/ds/estados";
import { CambiosPendientes } from "@/lib/cambiosPendientes";
import { RUTAS, type RutaDeModulo } from "@/modulos";

function Privada({
  children,
  sinMarco = false,
}: {
  children: ReactNode;
  sinMarco?: boolean;
}) {
  const { data: usuario, isPending, error, refetch } = useSesion();
  const { pathname, search } = useLocation();

  if (isPending) {
    return <div className="min-h-dvh bg-surface-000" aria-busy="true" />;
  }

  if (error) return <SinConexion error={error} onReintentar={() => void refetch()} />;

  if (!usuario) {
    return <Navigate to={`/entrar/?next=${encodeURIComponent(pathname + search)}`} replace />;
  }

  if (sinMarco) return <MarcoDeFoco>{children}</MarcoDeFoco>;

  return <AppShell usuario={usuario}>{children}</AppShell>;
}

function MarcoDeFoco({ children }: { children: ReactNode }) {
  return (
    <>
      <div className="sticky top-0 z-30 pt-[env(safe-area-inset-top)]">
        <AvisoDeConexion />
      </div>
      <main className="flex min-h-dvh flex-col px-[max(1rem,env(safe-area-inset-left))] pt-3 sm:px-6">
        <div className="mx-auto flex w-full max-w-2xl flex-1 flex-col lg:max-w-5xl">{children}</div>
      </main>
    </>
  );
}

function SoloStaff({ children }: { children: ReactNode }) {
  const { data: usuario, isPending, error, refetch } = useSesion();
  const { pathname, search } = useLocation();

  if (isPending) return <div className="min-h-dvh bg-surface-000" aria-busy="true" />;
  if (error) return <SinConexion error={error} onReintentar={() => void refetch()} />;
  if (!usuario) {
    return <Navigate to={`/entrar/?next=${encodeURIComponent(pathname + search)}`} replace />;
  }

  if (!usuario.is_staff) {
    return (
      <AppShell usuario={usuario}>
        <EmptyState
          titulo="Esta sección es del equipo"
          acciones={
            <EnlaceBoton a="/" variante="primary">
              Volver a Inicio
            </EnlaceBoton>
          }
        >
          Si crees que deberías tener acceso, pídelo a quien administre la aplicación.
        </EmptyState>
      </AppShell>
    );
  }

  return (
    <AppShell usuario={usuario} contexto="gestion">
      {children}
    </AppShell>
  );
}

function Pantalla({ ruta }: { ruta: RutaDeModulo }) {
  const { pantalla: Contenido, acceso } = ruta;
  const contenido = (
    <Suspense fallback={<Cargando />}>
      <Contenido />
    </Suspense>
  );

  switch (acceso) {
    case "publica":
      return contenido;
    case "privada":
      return <Privada>{contenido}</Privada>;
    case "foco":
      return <Privada sinMarco>{contenido}</Privada>;
    case "staff":
      return <SoloStaff>{contenido}</SoloStaff>;
  }
}

export function App() {
  return (
    <CambiosPendientes>
      <Routes>
        {RUTAS.map((ruta) => (
          <Route key={ruta.ruta} path={ruta.ruta} element={<Pantalla ruta={ruta} />} />
        ))}
      </Routes>
    </CambiosPendientes>
  );
}
