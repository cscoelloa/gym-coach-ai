import type { ReactNode } from "react";

import { Marca, Placa } from "@/ds/Marca";

import { Vitrina } from "./Vitrina";

export function MarcoDeAcceso({
  kicker,
  titulo,
  entradilla,
  children,
}: {
  kicker: string;
  titulo: string;
  entradilla: string;
  children: ReactNode;
}) {
  return (
    <main className="auth-page">
      <div className="auth-shell">
        <section className="auth-brand" aria-label="PROJECT_GYM">
          <div className="flex items-center gap-3">
            <Marca />
          </div>
          <Vitrina />
        </section>

        <section className="auth-panel">
          <div className="w-full max-w-sm">
            <div className="mb-8 flex flex-col items-center gap-3 text-center lg:hidden">
              <Placa className="size-20 rounded-[22px] shadow-[var(--shadow-pop)]" />
              <span className="title-sm text-ink">
                Project<span className="text-primary">/Gym</span>
              </span>
            </div>
            <p className="section-kicker text-primary">{kicker}</p>
            <h1>{titulo}</h1>
            <p className="body mt-2 text-ink-muted">{entradilla}</p>
            {children}
          </div>
        </section>
      </div>
    </main>
  );
}
