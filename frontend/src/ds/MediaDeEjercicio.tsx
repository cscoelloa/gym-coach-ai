import { useState } from "react";

import { Icono } from "./Icono";

export type TamanoDeMedia = "sm" | "md" | "lg" | "foco";

export function MediaDeEjercicio({
  imagen,
  animacion,
  atribucion,
  tamano = "md",
  credito = true,
  className = "",
}: {
  imagen: string | null;
  animacion: string | null;
  atribucion: string;
  tamano?: TamanoDeMedia;
  credito?: boolean;
  className?: string;
}) {
  const [pausada, setPausada] = useState(false);
  const fija = imagen ?? animacion;
  if (!fija) return null;

  const enMovimiento = Boolean(animacion) && !pausada;

  return (
    <figure className={`ex-figure ex-figure-${tamano} ${className}`.trim()}>
      <div className="ex-frame">
        {enMovimiento ? (
          <picture>
            {imagen && <source srcSet={imagen} media="(prefers-reduced-motion: reduce)" />}
            <img className="ex-frame-img" src={animacion!} alt="" decoding="async" />
          </picture>
        ) : (
          <img className="ex-frame-img" src={fija} alt="" decoding="async" />
        )}
        {animacion && imagen && (
          <button
            type="button"
            className="ex-frame-toggle"
            onClick={() => setPausada(!pausada)}
          >
            <Icono nombre={pausada ? "reproducir" : "pausa"} className="size-4" />
            <span className="sr-only">
              {pausada ? "Reproducir la animación" : "Pausar la animación"}
            </span>
          </button>
        )}
      </div>
      {credito && atribucion && <figcaption className="ex-credit">{atribucion}</figcaption>}
    </figure>
  );
}

export function CreditoDeMedia({
  atribucion,
  className = "",
}: {
  atribucion: string;
  className?: string;
}) {
  return <p className={`ex-credit ${className}`.trim()}>{atribucion}</p>;
}
