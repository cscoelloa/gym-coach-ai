import { describe, expect, it } from "vitest";

import { RUTAS_DE_LA_SPA } from "@/rutas";

import { RUTAS } from ".";

function normalizar(ruta: string): string {
  const sinBarra = ruta.length > 1 ? ruta.replace(/\/$/, "") : ruta;
  return sinBarra.replace(/:[A-Za-z_]+/g, ":");
}

describe("Las rutas de los módulos", () => {
  it("cada URL de la SPA tiene su pantalla en algún módulo", () => {
    const pintadas = new Set(RUTAS.map((r) => normalizar(r.ruta)));
    const huerfanas = RUTAS_DE_LA_SPA.map(normalizar).filter((r) => !pintadas.has(r));

    expect(huerfanas, "en rutas.ts pero en ningún módulo: se abrirían en blanco").toEqual([]);
  });

  it("cada pantalla de un módulo está declarada en rutas.ts", () => {
    const declaradas = new Set(RUTAS_DE_LA_SPA.map(normalizar));
    const sueltas = RUTAS.map((r) => normalizar(r.ruta)).filter((r) => !declaradas.has(r));

    expect(sueltas, "en un módulo pero no en rutas.ts: los enlaces recargarían la página").toEqual(
      [],
    );
  });

  it("ninguna URL la declaran dos módulos", () => {
    const vistas = RUTAS.map((r) => normalizar(r.ruta));

    expect(vistas.filter((r, i) => vistas.indexOf(r) !== i)).toEqual([]);
  });
});
