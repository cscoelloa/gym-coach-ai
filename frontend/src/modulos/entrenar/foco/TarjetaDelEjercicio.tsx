import { Pill } from "@/ds/Card";
import { Hint } from "@/ds/Hint";
import { CreditoDeMedia, MediaDeEjercicio } from "@/ds/MediaDeEjercicio";

import type { Foco } from "../api";
import { textoDeSerie } from "./textos";

type Actual = NonNullable<Foco["actual"]>;

export function TarjetaDelEjercicio({
  datos,
  actual,
  onComoSeHace,
}: {
  datos: Foco;
  actual: Actual;
  onComoSeHace: () => void;
}) {
  const conMedia = Boolean(actual.imagen || actual.animacion);

  return (
    <section className="focus-area-ejercicio card p-3 sm:p-4">
      <div className={conMedia ? "focus-card-grid" : ""}>
        {conMedia && (
          <MediaDeEjercicio
            imagen={actual.imagen}
            animacion={actual.animacion}
            atribucion={actual.atribucion}
            tamano="foco"
            credito={false}
          />
        )}
        <div className="min-w-0">
          <h1 className="title-md capitalize lg:title-lg">{actual.nombre}</h1>
          <div className="mt-2 flex flex-wrap gap-1.5 *:max-w-none *:whitespace-nowrap">
            <Pill>
              <span className="num">
                {actual.series}×{actual.reps_min}-{actual.reps_max}
              </span>
            </Pill>
            {actual.unilateral && <Pill activa>Unilateral</Pill>}
            {datos.mejor && (
              <Pill>
                Mejor: <span className="num">{datos.mejor}</span> kg
              </Pill>
            )}
            <button
              type="button"
              className="pill pill-active hover:no-underline"
              onClick={onComoSeHace}
            >
              Cómo se hace
            </button>
          </div>
          {datos.ultima_vez && (
            <p className="body-sm mt-2 text-ink-muted">
              <span className="tag mr-1.5 text-ink-subtle">La última vez</span>
              <span className="num">
                {datos.ultima_vez.series.map(([kg, r]) => textoDeSerie(kg, r)).join(" · ")}
                {datos.ultima_vez.por_lado && " (por lado)"}
              </span>
            </p>
          )}
        </div>
      </div>
      {datos.sugerencia && (
        <div className="mt-3">
          <Hint>{datos.sugerencia}</Hint>
        </div>
      )}
      {conMedia && actual.atribucion && (
        <CreditoDeMedia atribucion={actual.atribucion} className="mt-2" />
      )}
    </section>
  );
}
