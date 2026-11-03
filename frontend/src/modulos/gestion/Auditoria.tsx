import { useState } from "react";

import { Badge } from "@/ds/Badge";
import { Button } from "@/ds/Button";
import { Campo } from "@/ds/Campo";
import { Card, Celda, PageHeader, TablaApilada } from "@/ds/Card";
import { EmptyState } from "@/ds/EmptyState";
import { Cargando, ErrorDePantalla } from "@/ds/estados";
import { Paginacion } from "@/ds/Paginacion";
import { Panel } from "@/ds/Panel";
import { SegmentedControl } from "@/ds/SegmentedControl";
import { NotaDeStat, StatTile } from "@/ds/StatTile";

import {
  useGeneracion,
  useGeneraciones,
  useResumenDeGeneraciones,
} from "./api";

const FECHA = new Intl.DateTimeFormat("es-ES", {
  day: "2-digit",
  month: "short",
  hour: "2-digit",
  minute: "2-digit",
});

export function Auditoria() {
  const [tipo, setTipo] = useState("");
  const [estado, setEstado] = useState("");
  const [usuario, setUsuario] = useState("");
  const [abierta, setAbierta] = useState<number | null>(null);
  const [pagina, setPagina] = useState(1);

  const resumen = useResumenDeGeneraciones();
  const { data, isPending, error, refetch } = useGeneraciones({
    tipo,
    estado,
    usuario,
    page: pagina > 1 ? String(pagina) : "",
  });

  function filtrar<T>(cambiar: (valor: T) => void) {
    return (valor: T) => {
      cambiar(valor);
      setPagina(1);
    };
  }

  return (
    <>
      <PageHeader
        kicker="Auditoría"
        titulo="Generaciones"
        entradilla="Qué se le ha pedido al modelo, qué costó y qué falló."
      />

      {resumen.data && (
        <div className="mb-5 grid grid-cols-2 gap-3 lg:grid-cols-4">
          <StatTile etiqueta={`Llamadas (${resumen.data.dias} d)`} valor={resumen.data.total} />
          <StatTile
            etiqueta="Con error"
            valor={resumen.data.errores || null}
            vacio="Ninguna."
          />
          <StatTile etiqueta="Tokens" valor={resumen.data.tokens.toLocaleString("es-ES")} />
          <StatTile etiqueta="Tipos" valor={resumen.data.por_tipo.length}>
            <NotaDeStat>
              {resumen.data.por_tipo.map((fila) => `${fila.etiqueta}: ${fila.total}`).join(" · ")}
            </NotaDeStat>
          </StatTile>
        </div>
      )}

      <Card className="mb-4">
        <div className="grid grid-cols-1 gap-3 lg:grid-cols-3 lg:items-end">
          <div>
            <span className="config-label">Tipo</span>
          <SegmentedControl
            etiqueta="Tipo"
            opciones={[
              { valor: "", etiqueta: "Todas" },
              { valor: "routine", etiqueta: "Rutinas" },
              { valor: "progress", etiqueta: "Progreso" },
              { valor: "test", etiqueta: "Pruebas" },
            ]}
            valor={tipo}
            onCambio={filtrar(setTipo)}
          />
          </div>
          <div>
            <span className="config-label">Estado</span>
          <SegmentedControl
            etiqueta="Estado"
            opciones={[
              { valor: "", etiqueta: "Todos" },
              { valor: "ok", etiqueta: "Correctas" },
              { valor: "error", etiqueta: "Con error" },
            ]}
            valor={estado}
            onCambio={filtrar(setEstado)}
          />
          </div>
          <Campo
            etiqueta="Usuario"
            value={usuario}
            onChange={(evento) => filtrar(setUsuario)(evento.target.value)}
            placeholder="Parte del nombre"
          />
        </div>
      </Card>

      {isPending ? (
        <Cargando />
      ) : error || !data ? (
        <ErrorDePantalla onReintentar={refetch} />
      ) : data.results.length === 0 ? (
        <EmptyState titulo="No hay generaciones con esos filtros">
          Prueba a quitar alguno.
        </EmptyState>
      ) : (
        <Card>
          <TablaApilada>
            <thead>
              <tr className="text-left tag text-ink-muted">
                <th className="px-3 py-2">Cuándo</th>
                <th className="px-3 py-2">Usuario</th>
                <th className="px-3 py-2">Tipo</th>
                <th className="px-3 py-2">Modelo</th>
                <th className="px-3 py-2 md:text-right">Tokens</th>
                <th className="px-3 py-2">Estado</th>
                <th className="px-3 py-2" />
              </tr>
            </thead>
            <tbody>
              {data.results.map((fila) => (
                <tr className="hairline" key={fila.id}>
                  <Celda etiqueta="Cuándo" className="num">
                    {FECHA.format(new Date(fila.created_at))}
                  </Celda>
                  <Celda etiqueta="Usuario">{fila.usuario ?? "—"}</Celda>
                  <Celda etiqueta="Tipo">{fila.kind_label}</Celda>
                  <Celda etiqueta="Modelo" className="num">
                    {fila.model}
                  </Celda>
                  <Celda etiqueta="Tokens" className="num md:text-right">
                    {fila.input_tokens + fila.output_tokens}
                  </Celda>
                  <Celda etiqueta="Estado">
                    <Badge tono={fila.status === "ok" ? "done" : "down"}>
                      {fila.status_label}
                    </Badge>
                  </Celda>
                  <Celda etiqueta="">
                    <Button variante="ghost" tamano="sm" onClick={() => setAbierta(fila.id)}>
                      Ver
                      <span className="sr-only"> la generación #{fila.id}</span>
                    </Button>
                  </Celda>
                </tr>
              ))}
            </tbody>
          </TablaApilada>
          <Paginacion
            pagina={pagina}
            hayAnterior={Boolean(data.previous)}
            haySiguiente={Boolean(data.next)}
            onCambio={setPagina}
          />
        </Card>
      )}

      {abierta !== null && <Detalle id={abierta} onCerrar={() => setAbierta(null)} />}
    </>
  );
}

function Detalle({ id, onCerrar }: { id: number; onCerrar: () => void }) {
  const { data, isPending, error } = useGeneracion(id);

  return (
    <Panel titulo={`Generación #${id}`} onCerrar={onCerrar}>
      {isPending ? (
        <div className="min-h-32" aria-busy="true" />
      ) : error || !data ? (
        <p className="empty-hint">No se ha podido cargar el detalle.</p>
      ) : (
        <DetalleCargado data={data} />
      )}
    </Panel>
  );
}

function DetalleCargado({ data }: { data: NonNullable<ReturnType<typeof useGeneracion>["data"]> }) {
  return (
    <>
      <p className="caption num mb-3 text-ink-muted">
        {data.provider} · {data.model} · {data.latency_ms} ms · {data.input_tokens}+
        {data.output_tokens} tokens
      </p>

      {data.error && (
        <p className="mb-3 rounded-md border border-danger px-3 py-2 caption text-danger">
          {data.error}
        </p>
      )}

      <p className="section-kicker">Prompt enviado</p>
      <p className="caption mb-1 text-ink-muted">
        Puede contener las notas y las lesiones de esta persona. No salgas de esta pantalla con
        ella abierta.
      </p>
      <pre className="surface-2 mb-4 max-h-64 overflow-auto whitespace-pre-wrap rounded-md p-3 caption">
        {data.prompt_rendered || "(vacío)"}
      </pre>

      <p className="section-kicker">Respuesta cruda</p>
      <pre className="surface-2 max-h-64 overflow-auto whitespace-pre-wrap rounded-md p-3 caption">
        {data.raw_response || "(vacía)"}
      </pre>
    </>
  );
}
