import { useState } from "react";
import { Link, useNavigate } from "react-router";

import { Aviso } from "@/ds/Aviso";
import { Badge } from "@/ds/Badge";
import { Button, EnlaceBoton } from "@/ds/Button";
import { Campo } from "@/ds/Campo";
import { Card, PageHeader } from "@/ds/Card";
import { Cargando, ErrorDePantalla } from "@/ds/estados";
import { SegmentedControl } from "@/ds/SegmentedControl";

import {
  codigoDe,
  useFormularioDeGeneracion,
  useGenerar,
  type DiaDelReparto,
} from "./api";
import { RepartoSemanal, repartoInicial } from "./RepartoSemanal";

function Fallo({ error }: { error: unknown }) {
  const codigo = codigoDe(error);
  const mensaje = error instanceof Error ? error.message : "No se ha podido generar la rutina.";

  if (codigo === "sin_candidatos") {
    return (
      <Aviso tono="aviso" urgente>
        {mensaje}{" "}
        <Link to="/perfil/">Completar el perfil</Link>
      </Aviso>
    );
  }

  if (codigo === "cuota") {
    return <Aviso tono="informacion">{mensaje}</Aviso>;
  }

  if (codigo === "reparto" || codigo === "descanso") {
    return <Aviso tono="aviso" urgente>{mensaje}</Aviso>;
  }

  return (
    <Aviso tono="error" urgente>
      {mensaje}
      {codigo === "proveedor" && " Vuelve a intentarlo en un momento; esto no gasta generaciones."}
    </Aviso>
  );
}

export function GenerarRutina() {
  const { data, isPending, error, refetch } = useFormularioDeGeneracion();
  const generar = useGenerar();
  const navegar = useNavigate();

  const [reparto, setReparto] = useState<DiaDelReparto[] | null>(null);
  const [objetivo, setObjetivo] = useState<string | null>(null);
  const [notas, setNotas] = useState("");

  if (isPending) return <Cargando />;
  if (error || !data) return <ErrorDePantalla onReintentar={refetch} />;

  const objetivoElegido = objetivo ?? data.objetivo_por_defecto;
  const reglas = data.objetivos.find((o) => o.valor === objetivoElegido);

  const semana = reparto ?? repartoInicial(data.dias_sugeridos, data.ejercicios.por_defecto);
  const diasElegidos = semana.filter((dia) => dia.muscles.length);
  const sinCupo = data.restantes <= 0;

  return (
    <>
      <PageHeader
        kicker="Con ayuda de la IA"
        titulo="Generar rutina"
        entradilla="Se te mostrará la propuesta antes de guardar nada."
      >
        <Badge tono={sinCupo ? "down" : "record"}>
          <span className="num">{data.restantes}</span> generación
          {data.restantes === 1 ? "" : "es"} esta hora
        </Badge>
      </PageHeader>

      {!data.tiene_equipamiento && (
        <Card className="mb-4 border-primary">
          <strong>Todavía no has indicado tu equipamiento.</strong>
          <p className="body-sm mt-1 text-ink-muted">
            Sin eso se asume un gimnasio completo y pueden salir ejercicios que no puedas hacer.{" "}
            <Link to="/perfil/">Completar el perfil</Link>
          </p>
        </Card>
      )}

      {generar.error && (
        <div className="mb-4">
          <Fallo error={generar.error} />
        </div>
      )}

      <div className="grid grid-cols-1 items-start gap-4 lg:grid-cols-2">
        <Card>
          <h2 className="mb-3">Parámetros</h2>

          <p className="section-kicker">Objetivo del entrenamiento</p>
          <SegmentedControl
            etiqueta="Objetivo del entrenamiento"
            opciones={data.objetivos.map((o) => ({ valor: o.valor, etiqueta: o.etiqueta }))}
            valor={objetivoElegido}
            onCambio={setObjetivo}
          />
          {reglas && <p className="caption mt-2 mb-5 text-ink-muted">{reglas.resumen}</p>}

          <RepartoSemanal
            reparto={semana}
            musculos={data.musculos}
            limites={data.ejercicios}
            onCambio={setReparto}
          />

          <p className="caption mt-2 mb-4 text-ink-muted">
            Un músculo necesita 48 h para recuperarse: si dos días seguidos repiten el mismo, se
            te dice antes de gastar una generación.
          </p>

          <Campo
            etiqueta="¿Algo que deba tener en cuenta?"
            multilinea
            maxLength={1000}
            value={notas}
            onChange={(evento) => setNotas(evento.target.value)}
            placeholder="Ej.: quiero priorizar espalda, tengo poco tiempo los viernes…"
            ayuda="Esto se le pasa a la IA como dato sobre tu situación, nunca como instrucción."
          />

          <div className="form-actions">
            <Button
              variante="primary"
              disabled={sinCupo || generar.isPending || !diasElegidos.length}
              onClick={() =>
                generar.mutate(
                  { notes: notas, split: diasElegidos, training_goal: objetivoElegido },
                  {
                    onSuccess: (propuesta) =>
                      navegar(`/ia/propuestas/${propuesta.generacion.id}/`),
                  },
                )
              }
            >
              {generar.isPending ? "Generando…" : "Generar propuesta"}
            </Button>
          </div>

          <p className="caption mt-3 text-ink-muted">
            {generar.isPending
              ? "Estamos hablando con el modelo. No cierres esta pantalla."
              : "Puede tardar un minuto."}
          </p>
        </Card>

        <Card>
          <h2 className="mb-3">Qué se le envía</h2>
          <ul className="list-disc space-y-1 pl-5 body-sm text-ink-muted">
            <li>
              Tu objetivo, nivel, altura y <strong>edad</strong> — nunca tu fecha de nacimiento.
            </li>
            <li>Tu equipamiento disponible y tus limitaciones.</li>
            <li>Tus métricas de progreso, con su cobertura para que sepa de qué fiarse.</li>
            <li>Una lista cerrada de ejercicios del catálogo entre los que debe elegir.</li>
          </ul>
          <p className="caption mt-3 text-ink-muted">
            La IA no puede inventar ejercicios: solo escoger de esa lista. Si devuelve algo que no
            está, se rechaza y se le pide que lo corrija.
          </p>
          <div className="mt-4">
            <EnlaceBoton a="/plan/" variante="secondary" tamano="sm">
              Prefiero montarla yo
            </EnlaceBoton>
          </div>
        </Card>
      </div>
    </>
  );
}
