import { useState } from "react";

import { Aviso } from "@/ds/Aviso";
import { AvisoPasajero } from "@/ds/AvisoPasajero";
import { Badge } from "@/ds/Badge";
import { Button } from "@/ds/Button";
import { Campo } from "@/ds/Campo";
import { Card } from "@/ds/Card";
import { Cargando, ErrorDePantalla } from "@/ds/estados";

import { useGuardarProveedor, useProbarProveedor, useProveedores, type Proveedor } from "../api";
import { erroresDe } from "./errores";

export function Proveedores() {
  const { data, isPending, error, refetch } = useProveedores();
  const probar = useProbarProveedor();
  const guardar = useGuardarProveedor();
  const [clave, setClave] = useState<Record<number, string>>({});

  if (isPending) return <Cargando />;
  if (error || !data) return <ErrorDePantalla onReintentar={refetch} />;

  return (
    <div className="space-y-4">
      {data.length === 0 && (
        <Aviso tono="aviso">
          No hay ningún proveedor configurado. Sin uno activo, generar rutinas y analizar el
          progreso fallan para todo el mundo.
        </Aviso>
      )}

      {data.map((proveedor) => (
        <Card key={proveedor.id}>
          <div className="mb-3 flex flex-wrap items-start justify-between gap-2">
            <div className="min-w-0">
              <h2>{proveedor.provider_label}</h2>
              <p className="body-sm num text-ink-muted">{proveedor.effective_model}</p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              {proveedor.is_active ? (
                <Badge tono="done">Activo</Badge>
              ) : (
                <Badge tono="neutral">Inactivo</Badge>
              )}
              {!proveedor.has_usable_key && <Badge tono="down">Clave ilegible</Badge>}
            </div>
          </div>

          <section className="border-t border-line pt-4">
            <p className="section-kicker">Ajustes del modelo</p>
            <Ajustes proveedor={proveedor} />
          </section>

          <section className="mt-5 border-t border-line pt-4">
            <p className="section-kicker">Clave</p>
            <dl className="body-sm mb-3 flex flex-wrap gap-x-2">
              <dt className="text-ink-muted">En uso</dt>
              <dd className="num">{proveedor.masked_api_key}</dd>
            </dl>
            <Campo
              etiqueta="Cambiar la clave"
              type="password"
              autoComplete="off"
              value={clave[proveedor.id] ?? ""}
              onChange={(evento) =>
                setClave((previo) => ({ ...previo, [proveedor.id]: evento.target.value }))
              }
              ayuda="Se guarda cifrada. Déjalo vacío para no tocarla."
            />
            {clave[proveedor.id] && (
              <div className="form-actions">
                <Button
                  variante="primary"
                  disabled={guardar.isPending}
                  onClick={() =>
                    guardar.mutate(
                      { id: proveedor.id, api_key: clave[proveedor.id] },
                      {
                        onSuccess: () =>
                          setClave((previo) => ({ ...previo, [proveedor.id]: "" })),
                      },
                    )
                  }
                >
                  Guardar la clave
                </Button>
              </div>
            )}
          </section>

          <div className="form-actions border-t border-line pt-4">
            <Button
              variante="secondary"
              disabled={probar.isPending}
              onClick={() => probar.mutate(proveedor.id)}
            >
              {probar.isPending ? "Probando…" : "Probar conexión"}
            </Button>
            {!proveedor.is_active && (
              <Button
                variante="secondary"
                onClick={() => guardar.mutate({ id: proveedor.id, is_active: true })}
              >
                Activar
              </Button>
            )}
          </div>

          {probar.data && (
            <AvisoPasajero marca={probar.isSuccess && probar.submittedAt} duracion={10000}>
              Conexión correcta con {probar.data.modelo}: {probar.data.latencia_ms} ms,{" "}
              {probar.data.tokens} tokens. La prueba queda en la auditoría — también cuesta.
            </AvisoPasajero>
          )}
          {probar.error && (
            <Aviso tono="error" urgente>
              {probar.error instanceof Error ? probar.error.message : "No se pudo conectar."}
            </Aviso>
          )}
        </Card>
      ))}
    </div>
  );
}

function Ajustes({ proveedor }: { proveedor: Proveedor }) {
  const guardar = useGuardarProveedor();
  const [borrador, setBorrador] = useState({
    model: proveedor.model,
    max_tokens: String(proveedor.max_tokens),
    timeout_seconds: String(proveedor.timeout_seconds),
    effort: proveedor.effort,
  });

  const cambiado =
    borrador.model !== proveedor.model ||
    Number(borrador.max_tokens) !== proveedor.max_tokens ||
    Number(borrador.timeout_seconds) !== proveedor.timeout_seconds ||
    borrador.effort !== proveedor.effort;

  return (
    <>
      <div className="form-grid">
        <Campo
          etiqueta="Modelo"
          value={borrador.model}
          placeholder={proveedor.effective_model}
          onChange={(evento) => setBorrador({ ...borrador, model: evento.target.value })}
          ayuda="Vacío usa el de por defecto del proveedor."
          errores={erroresDe(guardar.error, "model")}
        />
        <Campo
          etiqueta="Tope de salida (tokens)"
          type="number"
          min={256}
          inputMode="numeric"
          value={borrador.max_tokens}
          onChange={(evento) => setBorrador({ ...borrador, max_tokens: evento.target.value })}
          ayuda="OpenAI lo reserva del cupo por minuto aunque no se use."
          errores={erroresDe(guardar.error, "max_tokens")}
        />
        <Campo
          etiqueta="Espera (s)"
          type="number"
          min={1}
          inputMode="numeric"
          value={borrador.timeout_seconds}
          onChange={(evento) =>
            setBorrador({ ...borrador, timeout_seconds: evento.target.value })
          }
          errores={erroresDe(guardar.error, "timeout_seconds")}
        />
        <div className="field">
          <label htmlFor={`esfuerzo-${proveedor.id}`}>Esfuerzo</label>
          <select
            id={`esfuerzo-${proveedor.id}`}
            value={borrador.effort}
            onChange={(evento) => setBorrador({ ...borrador, effort: evento.target.value })}
          >
            <option value="">Por defecto del proveedor</option>
            {ESFUERZOS.map(([valor, etiqueta]) => (
              <option key={valor} value={valor}>
                {etiqueta}
              </option>
            ))}
          </select>
          <span className="helptext">Solo lo admiten algunos modelos.</span>
        </div>
      </div>

      {cambiado && (
        <div className="form-actions">
          <Button
            variante="primary"
            disabled={guardar.isPending}
            onClick={() =>
              guardar.mutate({
                id: proveedor.id,
                model: borrador.model,
                max_tokens: Number(borrador.max_tokens),
                timeout_seconds: Number(borrador.timeout_seconds),
                effort: borrador.effort,
              })
            }
          >
            {guardar.isPending ? "Guardando…" : "Guardar ajustes"}
          </Button>
          <Button
            onClick={() =>
              setBorrador({
                model: proveedor.model,
                max_tokens: String(proveedor.max_tokens),
                timeout_seconds: String(proveedor.timeout_seconds),
                effort: proveedor.effort,
              })
            }
          >
            Descartar
          </Button>
        </div>
      )}
    </>
  );
}

const ESFUERZOS: [string, string][] = [
  ["low", "Bajo"],
  ["medium", "Medio"],
  ["high", "Alto"],
  ["xhigh", "Muy alto"],
  ["max", "Máximo"],
];
