import { useState } from "react";

import { Aviso } from "@/ds/Aviso";
import { AvisoPasajero } from "@/ds/AvisoPasajero";
import { Badge } from "@/ds/Badge";
import { Button } from "@/ds/Button";
import { Campo } from "@/ds/Campo";
import { Card } from "@/ds/Card";
import { Confirmacion } from "@/ds/Confirmacion";
import { Cargando, ErrorDePantalla } from "@/ds/estados";

import { useAlmacenes, useBorrarDocumento, useCrearAlmacen, useCrearEnOpenAI, useDocumentos, useLimitesDeSubida, useReindexar, useSubirDocumento, type Almacen, type Documento } from "../api";
import { erroresDe, mensajeDe } from "./errores";

export function Documentos() {
  const almacenes = useAlmacenes();
  const documentos = useDocumentos();
  const reindexar = useReindexar();
  const borrar = useBorrarDocumento();
  const [aBorrar, setABorrar] = useState<Documento | null>(null);

  if (almacenes.isPending || documentos.isPending) return <Cargando />;
  if (almacenes.error || !almacenes.data || documentos.error || !documentos.data) {
    return <ErrorDePantalla onReintentar={() => void almacenes.refetch()} />;
  }

  return (
    <div className="space-y-4">
      {almacenes.data.length === 0 ? (
        <>
          <Aviso tono="informacion">
            No hay ningún almacén vectorial. El RAG solo lo soporta OpenAI: con Anthropic
            o Google las rutinas se generan igual, pero sin el contexto de los libros.
          </Aviso>
          <CrearAlmacen />
        </>
      ) : (
        almacenes.data.map((almacen) => <TarjetaDeAlmacen almacen={almacen} key={almacen.id} />)
      )}

      {documentos.data.length > 0 && (
        <Card>
          <h2 className="mb-3">Documentos</h2>
          <div className="space-y-2">
            {documentos.data.map((documento) => (
              <div
                className="surface-2 flex flex-wrap items-center justify-between gap-2 rounded-md p-3"
                key={documento.id}
              >
                <div className="min-w-0">
                  <span className="title-sm block truncate">{documento.title}</span>
                  <span className="caption text-ink-muted">
                    {documento.almacen}
                    {documento.subido_por && ` · ${documento.subido_por}`}
                  </span>
                  {documento.error && (
                    <span className="caption block text-danger">{documento.error}</span>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <Badge
                    tono={
                      documento.status === "indexed"
                        ? "done"
                        : documento.status === "failed"
                          ? "down"
                          : "warn"
                    }
                  >
                    {documento.status_label}
                  </Badge>
                  {(documento.status === "failed" || documento.status === "pending") && (
                    <Button
                      variante="secondary"
                      tamano="sm"
                      disabled={reindexar.isPending}
                      onClick={() => reindexar.mutate(documento.id)}
                    >
                      {documento.status === "failed" ? "Reintentar" : "Indexar ahora"}
                    </Button>
                  )}
                  <Button
                    variante="danger"
                    tamano="sm"
                    disabled={borrar.isPending}
                    onClick={() => setABorrar(documento)}
                  >
                    Borrar
                  </Button>
                </div>
              </div>
            ))}
          </div>
          {(reindexar.error || borrar.error) && (
            <Aviso tono="error" urgente>
              {(reindexar.error ?? borrar.error) instanceof Error
                ? ((reindexar.error ?? borrar.error) as Error).message
                : "No se pudo completar la operación."}
            </Aviso>
          )}
        </Card>
      )}

      {aBorrar && (
        <Confirmacion
          titulo="Borrar el documento"
          mensaje={
            `Se borrará «${aBorrar.title}» también del almacén en OpenAI, así que dejará de ` +
            "aparecer en las respuestas de la IA. El archivo no se puede recuperar."
          }
          confirmar="Sí, borrarlo"
          cancelar="Cancelar"
          onConfirmar={() => {
            borrar.mutate(aBorrar.id);
            setABorrar(null);
          }}
          onCancelar={() => setABorrar(null)}
        />
      )}

      <p className="body-sm text-ink-muted">
        Lo que subas aquí es lo que la IA puede citar al generar una rutina. El{" "}
        <a href="/admin/aiassist/knowledgedocument/">admin de Django</a> sigue estando como red de
        seguridad, pero ya no hace falta pasar por él.
      </p>
    </div>
  );
}

function CrearAlmacen() {
  const crear = useCrearAlmacen();
  const [nombre, setNombre] = useState("");
  const [descripcion, setDescripcion] = useState("");

  return (
    <Card>
      <h2 className="mb-3">Crear un almacén</h2>
      <Campo
        etiqueta="Nombre"
        value={nombre}
        maxLength={120}
        onChange={(evento) => setNombre(evento.target.value)}
        errores={erroresDe(crear.error, "name")}
      />
      <Campo
        etiqueta="Descripción"
        multilinea
        value={descripcion}
        onChange={(evento) => setDescripcion(evento.target.value)}
        ayuda="Para qué es este almacén: «Libros de hipertrofia», «Guías de técnica»…"
      />
      <div className="form-actions">
        <Button
          variante="primary"
          disabled={!nombre.trim() || crear.isPending}
          onClick={() =>
            crear.mutate(
              { name: nombre.trim(), description: descripcion },
              { onSuccess: () => { setNombre(""); setDescripcion(""); } },
            )
          }
        >
          {crear.isPending ? "Creando…" : "Crear almacén"}
        </Button>
      </div>
      {crear.error && <Aviso tono="error" urgente>{mensajeDe(crear.error)}</Aviso>}
    </Card>
  );
}

function TarjetaDeAlmacen({ almacen }: { almacen: Almacen }) {
  const crearEnOpenAI = useCrearEnOpenAI();

  return (
    <Card>
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <h2>{almacen.name}</h2>
          <p className="caption text-ink-muted">{almacen.description}</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {almacen.is_ready ? (
            <Badge tono="done">Creado en OpenAI</Badge>
          ) : (
            <Badge tono="warn">Sin crear</Badge>
          )}
          <Badge>
            <span className="num">{almacen.documentos.indexados}</span>/
            <span className="num">{almacen.documentos.total}</span> indexados
          </Badge>
          {almacen.documentos.fallidos > 0 && (
            <Badge tono="down">
              <span className="num">{almacen.documentos.fallidos}</span> con error
            </Badge>
          )}
        </div>
      </div>

      {almacen.is_ready ? (
        <SubirDocumento almacen={almacen.id} />
      ) : (
        <>
          <p className="body-sm mt-4 text-ink-muted">
            Este almacén todavía no existe en OpenAI, así que no puede recibir documentos.
          </p>
          <div className="form-actions">
            <Button
              variante="primary"
              disabled={crearEnOpenAI.isPending}
              onClick={() => crearEnOpenAI.mutate(almacen.id)}
            >
              {crearEnOpenAI.isPending ? "Creando…" : "Crear en OpenAI"}
            </Button>
          </div>
          {crearEnOpenAI.error && (
            <Aviso tono="error" urgente>{mensajeDe(crearEnOpenAI.error)}</Aviso>
          )}
        </>
      )}
    </Card>
  );
}

function SubirDocumento({ almacen }: { almacen: number }) {
  const limites = useLimitesDeSubida();
  const subir = useSubirDocumento();
  const [titulo, setTitulo] = useState("");
  const [archivo, setArchivo] = useState<File | null>(null);
  const [clave, setClave] = useState(0);

  const maxMb = limites.data ? Math.round(limites.data.max_bytes / 1_048_576) : null;

  return (
    <div className="mt-4 border-t border-line pt-4">
      <p className="section-kicker">Subir un documento</p>
      <Campo
        etiqueta="Título"
        value={titulo}
        maxLength={200}
        onChange={(evento) => setTitulo(evento.target.value)}
        errores={erroresDe(subir.error, "title")}
      />
      <Campo
        key={clave}
        etiqueta="Archivo"
        type="file"
        accept={limites.data?.extensiones.join(",")}
        onChange={(evento) => setArchivo(evento.target.files?.[0] ?? null)}
        ayuda={
          limites.data
            ? `Se aceptan ${limites.data.extensiones.join(", ")} de hasta ${maxMb} MB.`
            : undefined
        }
        errores={erroresDe(subir.error, "file")}
      />
      <div className="form-actions">
        <Button
          variante="primary"
          disabled={!archivo || !titulo.trim() || subir.isPending}
          onClick={() =>
            archivo &&
            subir.mutate(
              { almacen, titulo: titulo.trim(), archivo },
              {
                onSuccess: () => {
                  setTitulo("");
                  setArchivo(null);
                  setClave((n) => n + 1);
                },
              },
            )
          }
        >
          {subir.isPending ? "Subiendo…" : "Subir e indexar"}
        </Button>
      </div>
      <AvisoPasajero
        marca={subir.isSuccess && subir.submittedAt}
        tono="informacion"
        duracion={10000}
      >
        Subido. El indexado va aparte: si se queda en «pendiente», usa «Indexar ahora».
      </AvisoPasajero>
      {subir.error && <Aviso tono="error" urgente>{mensajeDe(subir.error)}</Aviso>}
    </div>
  );
}
