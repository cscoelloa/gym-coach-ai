import type { ButtonHTMLAttributes, ReactNode } from "react";
import { Link } from "react-router";

import { esRutaDeLaSpa } from "@/rutas";

export type VarianteDeBoton = "primary" | "secondary" | "ghost" | "danger";
export type TamanoDeBoton = "sm" | "md" | "lg";

function clases(
  variante: VarianteDeBoton,
  tamano: TamanoDeBoton,
  bloque: boolean,
  extra: string,
): string {
  return [
    "btn",
    `btn-${variante}`,
    tamano === "md" ? "" : `btn-${tamano}`,
    bloque ? "btn-block" : "",
    extra,
  ]
    .filter(Boolean)
    .join(" ");
}

type PropsBoton = ButtonHTMLAttributes<HTMLButtonElement> & {
  variante?: VarianteDeBoton;
  tamano?: TamanoDeBoton;
  bloque?: boolean;
  children: ReactNode;
};

export function Button({
  variante = "secondary",
  tamano = "md",
  bloque = false,
  className = "",
  type = "button",
  children,
  ...resto
}: PropsBoton) {
  return (
    <button type={type} className={clases(variante, tamano, bloque, className)} {...resto}>
      {children}
    </button>
  );
}

type PropsEnlace = {
  a: string;
  variante?: VarianteDeBoton;
  tamano?: TamanoDeBoton;
  bloque?: boolean;
  className?: string;
  children: ReactNode;
};

export function EnlaceBoton({
  a,
  variante = "secondary",
  tamano = "md",
  bloque = false,
  className = "",
  children,
}: PropsEnlace) {
  const clase = clases(variante, tamano, bloque, className);

  if (esRutaDeLaSpa(a)) {
    return (
      <Link to={a} className={clase}>
        {children}
      </Link>
    );
  }

  return (
    <a href={a} className={clase}>
      {children}
    </a>
  );
}
