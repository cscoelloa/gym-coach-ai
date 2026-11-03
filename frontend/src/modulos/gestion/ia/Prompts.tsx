import { useState } from "react";

import { Aviso } from "@/ds/Aviso";
import { AvisoPasajero } from "@/ds/AvisoPasajero";
import { Badge } from "@/ds/Badge";
import { Button } from "@/ds/Button";
import { Campo } from "@/ds/Campo";
import { Card } from "@/ds/Card";
import { Cargando, ErrorDePantalla } from "@/ds/estados";

import { useGuardarPrompt, usePrompts, useVistaPreviaDePrompt, type Prompt } from "../api";

export function Prompts() {
  const { data, isPending, error, refetch } = usePrompts();
  const [abierto, setAbierto] = useState<number | null>(null);

  if (isPending) return <Cargando />;
  if (error || !data) return <ErrorDePantalla onReintentar={refetch} />;

  return (
    <div className="space-y-3">
      {data.map((prompt) => (
        <Card key={prompt.id}>
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="min-w-0">
              <h2>{prompt.key_label}</h2>
              <p className="caption text-ink-muted">
                {prompt.name} · v<span className="num">{prompt.version}</span>
              </p>
            </div>
            <div className="flex items-center gap-2">
              {prompt.is_active && <Badge tono="done">Activo</Badge>}
              <Button
                variante="secondary"
                tamano="sm"
                onClick={() => setAbierto(abierto === prompt.id ? null : prompt.id)}
              >
                {abierto === prompt.id ? "Cerrar" : "Editar"}
              </Button>
            </div>
          </div>

          {abierto === prompt.id && <EditorDePrompt prompt={prompt} />}
        </Card>
      ))}
    </div>
  );
}

function EditorDePrompt({ prompt }: { prompt: Prompt }) {
  const guardar = useGuardarPrompt();
  const previa = useVistaPreviaDePrompt();
  const [system, setSystem] = useState(prompt.system_prompt);
  const [plantilla, setPlantilla] = useState(prompt.user_template);

  const sinCambios = system === prompt.system_prompt && plantilla === prompt.user_template;

  return (
    <div className="mt-4">
      <p className="caption mb-2 text-ink-muted">Variables disponibles:</p>
      <div className="mb-3 flex flex-wrap gap-1">
        {prompt.available_variables.map((variable) => (
          <code className="surface-2 rounded px-1.5 py-0.5 caption num" key={variable}>
            {`{{ ${variable} }}`}
          </code>
        ))}
      </div>

      <Campo
        etiqueta="Instrucciones de sistema"
        multilinea
        filas={6}
        value={system}
        onChange={(evento) => setSystem(evento.target.value)}
      />
      <Campo
        etiqueta="Plantilla del mensaje"
        multilinea
        filas={10}
        value={plantilla}
        onChange={(evento) => setPlantilla(evento.target.value)}
      />

      <div className="form-actions">
        <Button
          variante="primary"
          disabled={sinCambios || guardar.isPending}
          onClick={() =>
            guardar.mutate({ id: prompt.id, system_prompt: system, user_template: plantilla })
          }
        >
          {guardar.isPending ? "Guardando…" : "Guardar"}
        </Button>
        <Button
          variante="secondary"
          disabled={previa.isPending}
          onClick={() => previa.mutate(prompt.id)}
        >
          Vista previa
        </Button>
      </div>

      {guardar.error && (
        <Aviso tono="error" urgente>
          {guardar.error instanceof Error ? guardar.error.message : "No se pudo guardar."}
        </Aviso>
      )}
      <AvisoPasajero marca={guardar.isSuccess && guardar.submittedAt}>Guardado.</AvisoPasajero>

      {previa.data && (
        <div className="mt-4">
          {previa.data.desconocidas.length > 0 && (
            <Aviso tono="aviso">
              Estas variables no existen y se renderizarán vacías:{" "}
              <span className="num">{previa.data.desconocidas.join(", ")}</span>
            </Aviso>
          )}
          <p className="section-kicker mt-3">Cómo queda</p>
          <pre className="surface-2 mt-1 max-h-80 overflow-auto whitespace-pre-wrap rounded-md p-3 caption">
            {previa.data.system}
            {"\n\n---\n\n"}
            {previa.data.mensaje}
          </pre>
        </div>
      )}
    </div>
  );
}
