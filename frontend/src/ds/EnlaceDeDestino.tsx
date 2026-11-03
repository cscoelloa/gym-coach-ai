import type { ReactNode } from "react";
import { Link } from "react-router";

import { esRutaDeLaSpa } from "@/rutas";

type Props = {
  a: string;
  className?: string;
  children: ReactNode;
  "aria-current"?: "page";
};

export function EnlaceDeDestino({ a, children, ...resto }: Props) {
  if (esRutaDeLaSpa(a)) {
    return (
      <Link to={a} {...resto}>
        {children}
      </Link>
    );
  }

  return (
    <a href={a} {...resto}>
      {children}
    </a>
  );
}
