import { useState } from "react";
import { Link } from "react-router";

import { Badge } from "@/ds/Badge";
import { Icono } from "@/ds/Icono";

import type { Ejercicio } from "./api";

export function TarjetaDeEjercicio({ ejercicio }: { ejercicio: Ejercicio }) {
  const [animar, setAnimar] = useState(false);
  const imagen = animar && ejercicio.animation ? ejercicio.animation : ejercicio.image;

  return (
    <Link
      className="exercise-card group"
      to={`/ejercicios/${ejercicio.slug}/`}
      onPointerEnter={(evento) => evento.pointerType === "mouse" && setAnimar(true)}
      onPointerLeave={() => setAnimar(false)}
    >
      <span className="exercise-card-media">
        {imagen ? (
          <img
            className="size-full object-contain transition-transform duration-300 group-hover:scale-105"
            src={imagen}
            alt=""
            loading="lazy"
          />
        ) : (
          <Icono nombre="mancuerna" className="size-8 text-ink-subtle" />
        )}
        {ejercicio.is_unilateral && (
          <span className="absolute top-2 left-2">
            <Badge tono="record">Unilateral</Badge>
          </span>
        )}
      </span>
      <span className="flex min-w-0 flex-1 flex-col gap-1 p-3">
        <span className="ex-name line-clamp-2 block">{ejercicio.name}</span>
        <span className="caption flex flex-wrap items-center gap-x-1.5 text-ink-muted">
          <span className="font-semibold text-data">{ejercicio.body_part_label}</span>
          <span aria-hidden="true">·</span>
          {ejercicio.equipment_label}
        </span>
      </span>
    </Link>
  );
}
