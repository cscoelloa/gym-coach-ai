import type { ReactNode } from "react";

import { useTituloDeLaPantalla } from "@/lib/marco";

type Hero = "primary" | "data";

export function Cabecera({
  titulo,
  descripcion,
  kicker,
  acciones,
  hero,
}: {
  titulo: string;
  descripcion?: ReactNode;
  kicker?: string;
  acciones?: ReactNode;
  hero?: Hero;
}) {
  const observar = useTituloDeLaPantalla(titulo);

  if (hero) {
    const tono = hero === "data" ? "hero-data" : "";
    return (
      <header className={`hero ${tono} page-hero`.trim()}>
        <div className="min-w-0">
          {kicker && <p className="hero-kicker">{kicker}</p>}
          <h1 ref={observar}>{titulo}</h1>
          {descripcion && <p className="body-sm mt-1.5 text-ink-muted">{descripcion}</p>}
        </div>
        {acciones && <div className="flex flex-wrap items-center gap-2">{acciones}</div>}
      </header>
    );
  }

  return (
    <header className="page-head">
      <div className="min-w-0">
        {kicker && <p className="section-kicker">{kicker}</p>}
        <h1 ref={observar}>{titulo}</h1>
        {descripcion && <p className="body-sm mt-1.5 text-ink-muted">{descripcion}</p>}
      </div>
      {acciones && <div className="flex flex-wrap items-center gap-2">{acciones}</div>}
    </header>
  );
}
