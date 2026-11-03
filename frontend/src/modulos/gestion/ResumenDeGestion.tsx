import { Link } from "react-router";

import { Aviso } from "@/ds/Aviso";
import { EnlaceBoton } from "@/ds/Button";
import { Card, PageHeader } from "@/ds/Card";
import { Cargando, ErrorDePantalla } from "@/ds/estados";
import { NotaDeStat, StatTile } from "@/ds/StatTile";

import { useResumenDelPanel } from "./api";

export function ResumenDeGestion() {
  const { data, isPending, error, refetch } = useResumenDelPanel();

  if (isPending) return <Cargando />;
  if (error || !data) return <ErrorDePantalla onReintentar={refetch} />;

  const sinProveedor = data.proveedor === null;
  const claveRota = data.proveedor !== null && !data.proveedor.clave_usable;

  return (
    <>
      <PageHeader
        kicker={`Últimos ${data.dias} días`}
        titulo="Resumen"
        entradilla="El estado de lo que hace falta para que la aplicación funcione entera."
      />

      {sinProveedor && (
        <div className="mb-4">
          <Aviso tono="error" urgente>
            No hay ningún proveedor de IA activo. Generar rutinas y analizar el progreso fallan
            para todo el mundo. <Link to="/gestion/ia/">Configurar uno</Link>
          </Aviso>
        </div>
      )}
      {claveRota && (
        <div className="mb-4">
          <Aviso tono="error" urgente>
            La clave del proveedor activo no se puede descifrar: vuelve a pegarla. Hasta entonces
            la configuración parece correcta y todas las llamadas fallan.{" "}
            <Link to="/gestion/ia/">Ir a proveedores</Link>
          </Aviso>
        </div>
      )}
      {data.documentos.fallidos > 0 && (
        <div className="mb-4">
          <Aviso tono="aviso">
            {data.documentos.fallidos} documento{data.documentos.fallidos === 1 ? "" : "s"} del RAG
            sin indexar. La IA está respondiendo sin ese contexto.{" "}
            <Link to="/gestion/ia/?zona=rag">Revisar</Link>
          </Aviso>
        </div>
      )}

      <div className="mb-5 grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatTile
          etiqueta="Generaciones"
          valor={data.generaciones.total}
          icono="rayo"
        >
          {data.generaciones.errores > 0 && (
            <NotaDeStat>
              {data.generaciones.errores} con error
            </NotaDeStat>
          )}
        </StatTile>
        <StatTile etiqueta="Usuarios" valor={data.usuarios.total} icono="persona" tono="data">
          <NotaDeStat>
            {data.usuarios.nuevos} nuevo{data.usuarios.nuevos === 1 ? "" : "s"}
          </NotaDeStat>
        </StatTile>
        <StatTile
          etiqueta="Bloqueados"
          valor={data.usuarios.bloqueados || null}
          vacio="Ninguno."
          icono="escudo"
          tono="warning"
        />
        <StatTile
          etiqueta="Métricas activas"
          valor={data.metricas.activas}
          icono="progreso"
          tono="success"
        >
          <NotaDeStat>de {data.metricas.total} en el catálogo</NotaDeStat>
        </StatTile>
      </div>

      <div className="grid grid-cols-1 items-start gap-4 lg:grid-cols-2">
        <Card>
          <p className="section-kicker">Proveedor activo</p>
          {data.proveedor ? (
            <>
              <h2 className="mb-1">{data.proveedor.nombre}</h2>
              <p className="body-sm num text-ink-muted">{data.proveedor.modelo}</p>
            </>
          ) : (
            <p className="empty-hint">Sin configurar.</p>
          )}
          <div className="mt-4">
            <EnlaceBoton a="/gestion/ia/" variante="secondary" tamano="sm">
              Configurar la IA
            </EnlaceBoton>
          </div>
        </Card>

        <Card>
          <p className="section-kicker">Documentos del RAG</p>
          <h2 className="mb-1">
            <span className="num">{data.documentos.total}</span> en total
          </h2>
          <p className="body-sm text-ink-muted">
            <span className="num">{data.documentos.pendientes}</span> por indexar ·{" "}
            <span className="num">{data.documentos.fallidos}</span> con error
          </p>
          <div className="mt-4">
            <EnlaceBoton a="/gestion/ia/?zona=rag" variante="secondary" tamano="sm">
              Ver documentos
            </EnlaceBoton>
          </div>
        </Card>
      </div>
    </>
  );
}
