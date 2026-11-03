import type { ReactNode } from "react";
import { Link } from "react-router";

import { esRutaDeLaSpa } from "@/rutas";

export function ExerciseCard({
  a,
  nombre,
  grupo,
  equipamiento,
  ultima,
  glifo,
}: {
  a?: string;
  nombre: string;
  grupo: string;
  equipamiento?: string;
  ultima?: string;
  glifo?: ReactNode;
}) {
  const cuerpo = (
    <>
      {glifo && (
        <span className="ex-glyph" aria-hidden="true">
          {glifo}
        </span>
      )}
      <span className="ex-body">
        <span className="ex-name">{nombre}</span>
        <span className="ex-meta">
          {grupo}
          {equipamiento && (
            <>
              {" "}
              <span className="text-ink-subtle">/</span> {equipamiento}
            </>
          )}
        </span>
      </span>
      {ultima && <span className="ex-last">{ultima}</span>}
    </>
  );

  if (!a) return <div className="ex-item">{cuerpo}</div>;

  if (esRutaDeLaSpa(a)) {
    return (
      <Link to={a} className="ex-item">
        {cuerpo}
      </Link>
    );
  }

  return (
    <a href={a} className="ex-item">
      {cuerpo}
    </a>
  );
}
