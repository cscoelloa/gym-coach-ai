import { Link, useParams } from "react-router";

import { ErrorDeApi } from "@/api/cliente";
import { useMapaCorporal } from "@/api/mapaCorporal";
import { Badge } from "@/ds/Badge";
import { BodyMap } from "@/ds/BodyMap";
import { Card } from "@/ds/Card";
import { EmptyState } from "@/ds/EmptyState";
import { Cargando, ErrorDePantalla } from "@/ds/estados";
import { Icono } from "@/ds/Icono";
import { MediaDeEjercicio } from "@/ds/MediaDeEjercicio";

import { useEjercicio } from "./api";

const NIVEL_OBJETIVO = 4;
const NIVEL_SECUNDARIO = 2;

export function FichaDeEjercicio() {
  const { slug = "" } = useParams();
  const { data: ejercicio, isPending, error, refetch } = useEjercicio(slug);
  const { data: mapa } = useMapaCorporal();

  if (isPending) return <Cargando />;

  if (error instanceof ErrorDeApi && error.estado === 404) {
    return (
      <EmptyState titulo="Ese ejercicio no está en tu catálogo">
        Puede que el enlace sea viejo. <Link to="/ejercicios/">Vuelve al catálogo</Link> para
        buscarlo.
      </EmptyState>
    );
  }

  if (error || !ejercicio) return <ErrorDePantalla onReintentar={refetch} />;

  const niveles: Record<string, number> = {};
  if (ejercicio.target_muscle) niveles[ejercicio.target_muscle.slug] = NIVEL_OBJETIVO;
  for (const musculo of ejercicio.secondary_muscles) {
    niveles[musculo.slug] ??= NIVEL_SECUNDARIO;
  }

  const pintables = new Set(mapa?.musculos ?? []);
  const fueraDelMapa = [ejercicio.target_muscle, ...ejercicio.secondary_muscles]
    .filter((musculo): musculo is NonNullable<typeof musculo> => Boolean(musculo))
    .filter((musculo) => mapa && !pintables.has(musculo.slug))
    .map((musculo) => musculo.name);

  const media = ejercicio.animation ?? ejercicio.image;

  return (
    <>
      <div className="page-head">
        <h1 className="capitalize">{ejercicio.name}</h1>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-[minmax(0,5fr)_minmax(0,6fr)] lg:items-start">
        <Card className="lg:sticky lg:top-20">
          {media ? (
            <MediaDeEjercicio
              imagen={ejercicio.image}
              animacion={ejercicio.animation}
              atribucion={ejercicio.attribution}
              tamano="md"
            />
          ) : (
            <div className="empty-state">
              <Icono nombre="mancuerna" className="size-8 text-ink-subtle" />
              <span className="empty-title">Sin referencia visual</span>
              <p>Es un ejercicio tuyo. Las imágenes son solo del catálogo importado.</p>
            </div>
          )}
        </Card>

        <div className="flex flex-col gap-4">
          <Card className="space-y-4">
            <div className="flex flex-wrap gap-2">
              <Badge tono="info">{ejercicio.body_part_label}</Badge>
              <Badge>{ejercicio.equipment_label}</Badge>
              {ejercicio.is_cardio && <Badge tono="warn">Cardio</Badge>}
              {ejercicio.is_bodyweight && ejercicio.equipment !== "body weight" && (
                <Badge tono="done">Cuenta tu peso corporal</Badge>
              )}
              {ejercicio.is_unilateral && <Badge tono="record">Unilateral</Badge>}
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-[minmax(0,1fr)_minmax(0,1fr)] sm:items-center">
              <BodyMap niveles={niveles} compacto />

              <div className="space-y-3">
                <div>
                  <h3>Músculo objetivo</h3>
                  {ejercicio.target_muscle ? (
                    <span className="tag-musculo mt-1 px-2.5 py-1 text-[13px]">
                      {ejercicio.target_muscle.name}
                    </span>
                  ) : (
                    <p className="mt-1">—</p>
                  )}
                </div>
                {ejercicio.secondary_muscles.length > 0 && (
                  <div>
                    <h3>También trabaja</h3>
                    <div className="mt-1 flex flex-wrap gap-1.5">
                      {ejercicio.secondary_muscles.map((m) => (
                        <span className="tag-musculo" key={m.slug}>
                          {m.name}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                {fueraDelMapa.length > 0 && (
                  <p className="empty-hint">Fuera del mapa: {fueraDelMapa.join(", ")}.</p>
                )}
              </div>
            </div>
          </Card>

          <Card>
            <h2 className="mb-3">Cómo se hace</h2>
            {ejercicio.steps.length ? (
              <ol className="steps-list">
                {ejercicio.steps.map((paso, indice) => (
                  <li key={indice}>{paso}</li>
                ))}
              </ol>
            ) : (
              <p className="empty-hint">Sin instrucciones.</p>
            )}
          </Card>
        </div>
      </div>
    </>
  );
}
