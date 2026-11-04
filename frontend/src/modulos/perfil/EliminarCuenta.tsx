import { useState } from "react";
import { useNavigate } from "react-router";

import { ErrorDeApi } from "@/api/cliente";
import { useSesion } from "@/api/sesion";
import { Aviso } from "@/ds/Aviso";
import { Button, EnlaceBoton } from "@/ds/Button";
import { Campo } from "@/ds/Campo";
import { Card } from "@/ds/Card";
import { Cargando } from "@/ds/estados";
import { olvidarEsteDispositivo } from "@/lib/avisos";
import { salirDeLaSpa } from "@/lib/navegar";
import { borrarCachesDeLaApp } from "@/lib/pwa";

import { useBorrarCuenta } from "./api";

export function EliminarCuenta() {
  const { data: usuario, isPending } = useSesion();
  const borrar = useBorrarCuenta();
  const navegar = useNavigate();
  const [confirmacion, setConfirmacion] = useState("");

  if (isPending) return <Cargando />;
  if (!usuario) return null;

  const coincide = confirmacion === usuario.username;
  const porCampo = borrar.error instanceof ErrorDeApi ? borrar.error.porCampo : {};

  return (
    <div className="form-narrow mx-auto">
      <Card>
        <h1>Eliminar tu cuenta</h1>

        <p className="mt-3">Se borrarán de forma permanente:</p>
        <ul className="mt-2 list-disc space-y-1 pl-5 body-sm">
          <li>Tu perfil, incluidos altura, peso objetivo y lesiones.</li>
          <li>Todas tus rutinas y tus programas.</li>
          <li>Todo tu historial de entrenamientos y series.</li>
          <li>Todos tus registros de peso corporal.</li>
          <li>Tus notificaciones y tus preferencias de métricas.</li>
        </ul>

        <p className="body-sm mt-3 text-ink-muted">
          De las llamadas a la IA se conserva únicamente el consumo (proveedor, modelo, tokens y
          fecha) para contabilidad.{" "}
          <strong>El contenido de los prompts, que incluye tus datos, se elimina.</strong>
        </p>

        <div className="mt-4">
          <Aviso tono="aviso" urgente>
            Esto no se puede deshacer. Si quieres conservar tu historial,{" "}
            <a href="/api/cuenta/" download>
              descárgalo antes
            </a>
            .
          </Aviso>
        </div>

        {borrar.error && !Object.keys(porCampo).length && (
          <Aviso tono="error" urgente>
            {borrar.error instanceof Error
              ? borrar.error.message
              : "No se ha podido eliminar la cuenta."}
          </Aviso>
        )}

        <div className="mt-4">
          <Campo
            etiqueta={`Escribe «${usuario.username}» para confirmar`}
            autoComplete="off"
            value={confirmacion}
            errores={porCampo["confirmacion"]}
            onChange={(evento) => setConfirmacion(evento.target.value)}
          />
        </div>

        <div className="form-actions">
          <Button
            variante="danger"
            disabled={!coincide || borrar.isPending}
            onClick={() =>
              borrar.mutate(confirmacion, {
                onSuccess: async () => {
                  await olvidarEsteDispositivo({ avisarAlServidor: false });
                  await borrarCachesDeLaApp().catch(() => {});
                  salirDeLaSpa("/entrar/");
                },
              })
            }
          >
            {borrar.isPending ? "Eliminando…" : "Sí, eliminar mi cuenta"}
          </Button>
          <Button variante="secondary" onClick={() => navegar("/perfil/")}>
            Cancelar
          </Button>
        </div>

        <div className="mt-4">
          <EnlaceBoton a="/perfil/" variante="ghost" tamano="sm">
            Volver al perfil
          </EnlaceBoton>
        </div>
      </Card>
    </div>
  );
}
