import { useState } from "react";

import { Badge } from "@/ds/Badge";
import { Button } from "@/ds/Button";
import { Campo } from "@/ds/Campo";
import { Card, Celda, PageHeader, TablaApilada } from "@/ds/Card";
import { EmptyState } from "@/ds/EmptyState";
import { Cargando, ErrorDePantalla } from "@/ds/estados";
import { Hint } from "@/ds/Hint";
import { SegmentedControl } from "@/ds/SegmentedControl";

import {
  useCambiarUsuario,
  useDesbloquear,
  useUsuariosDeGestion,
  type UsuarioDeGestion,
} from "./api";

const FECHA = new Intl.DateTimeFormat("es-ES", { day: "numeric", month: "short", year: "numeric" });

type Estado = "" | "activas" | "bloqueadas" | "desactivadas";

function estadoDe(usuario: UsuarioDeGestion): Exclude<Estado, ""> {
  if (!usuario.is_active) return "desactivadas";
  return usuario.bloqueado ? "bloqueadas" : "activas";
}

export function Usuarios() {
  const [buscar, setBuscar] = useState("");
  const [estado, setEstado] = useState<Estado>("");
  const { data, isPending, error, refetch } = useUsuariosDeGestion(buscar);
  const visibles = data?.filter((usuario) => !estado || estadoDe(usuario) === estado);
  const cuantas = (filtro: Exclude<Estado, "">) =>
    data ? data.filter((usuario) => estadoDe(usuario) === filtro).length : 0;
  const cambiar = useCambiarUsuario();
  const desbloquear = useDesbloquear();

  return (
    <>
      <PageHeader
        kicker="Cuentas"
        titulo="Usuarios"
        entradilla="Quién se ha registrado, qué lleva hecho y quién está bloqueado."
      />

      <Card className="mb-4">
        <Campo
          etiqueta="Buscar"
          value={buscar}
          onChange={(evento) => setBuscar(evento.target.value)}
          placeholder="Nombre de usuario o correo"
        />
        <div className="mb-4">
          <span className="config-label">Estado</span>
          <SegmentedControl
            etiqueta="Estado de la cuenta"
            opciones={[
              { valor: "", etiqueta: "Todas" },
              { valor: "activas", etiqueta: `Activas · ${cuantas("activas")}` },
              { valor: "bloqueadas", etiqueta: `Bloqueadas · ${cuantas("bloqueadas")}` },
              { valor: "desactivadas", etiqueta: `Desactivadas · ${cuantas("desactivadas")}` },
            ]}
            valor={estado}
            onCambio={setEstado}
          />
        </div>
        <Hint>
          Aquí no hay peso, altura, lesiones ni fecha de nacimiento: son datos de salud y no hacen
          falta para administrar. Si hay que mirarlos por soporte, se pide permiso a la persona.
        </Hint>
      </Card>

      {isPending ? (
        <Cargando />
      ) : error || !data || !visibles ? (
        <ErrorDePantalla onReintentar={refetch} />
      ) : data.length === 0 ? (
        <EmptyState titulo="Ninguna cuenta con ese nombre">
          Prueba con otra parte del nombre o del correo.
        </EmptyState>
      ) : visibles.length === 0 ? (
        <EmptyState titulo="Ninguna cuenta en ese estado">
          Con esta búsqueda no hay ninguna. Elige «Todas» para verlas.
        </EmptyState>
      ) : (
        <Card>
          <TablaApilada>
            <thead>
              <tr className="text-left tag text-ink-muted">
                <th className="px-3 py-2">Usuario</th>
                <th className="px-3 py-2">Alta</th>
                <th className="px-3 py-2 md:text-right">Entrenos</th>
                <th className="px-3 py-2 md:text-right">Rutinas</th>
                <th className="px-3 py-2 md:text-right">IA</th>
                <th className="px-3 py-2">Estado</th>
                <th className="px-3 py-2" />
              </tr>
            </thead>
            <tbody>
              {visibles.map((usuario) => (
                <tr className="hairline" key={usuario.id}>
                  <Celda etiqueta="Usuario" className="font-medium md:font-normal">
                    {usuario.username}
                    {usuario.is_staff && (
                      <span className="ml-2">
                        <Badge tono="info">staff</Badge>
                      </span>
                    )}
                  </Celda>
                  <Celda etiqueta="Alta" className="num">
                    {FECHA.format(new Date(usuario.date_joined))}
                  </Celda>
                  <Celda etiqueta="Entrenos" className="num md:text-right">
                    {usuario.entrenamientos}
                  </Celda>
                  <Celda etiqueta="Rutinas" className="num md:text-right">
                    {usuario.rutinas}
                  </Celda>
                  <Celda etiqueta="IA" className="num md:text-right">
                    {usuario.generaciones}
                  </Celda>
                  <Celda etiqueta="Estado">
                    {!usuario.is_active ? (
                      <Badge tono="down">Desactivada</Badge>
                    ) : usuario.bloqueado ? (
                      <Badge tono="warn">Bloqueada</Badge>
                    ) : (
                      <Badge tono="done">Activa</Badge>
                    )}
                  </Celda>
                  <Celda etiqueta="">
                    <span className="flex flex-wrap gap-2">
                      {usuario.bloqueado && (
                        <Button
                          variante="secondary"
                          tamano="sm"
                          disabled={desbloquear.isPending}
                          onClick={() => desbloquear.mutate(usuario.id)}
                        >
                          Desbloquear
                        </Button>
                      )}
                      <Button
                        variante="ghost"
                        tamano="sm"
                        disabled={cambiar.isPending}
                        onClick={() =>
                          cambiar.mutate({ id: usuario.id, is_active: !usuario.is_active })
                        }
                      >
                        {usuario.is_active ? "Desactivar" : "Reactivar"}
                      </Button>
                    </span>
                  </Celda>
                </tr>
              ))}
            </tbody>
          </TablaApilada>
        </Card>
      )}

      <p className="body-sm mt-4 text-ink-muted">
        Borrar una cuenta no se hace desde aquí: cada persona la borra desde su perfil, que además
        exporta sus datos antes.
      </p>
    </>
  );
}
