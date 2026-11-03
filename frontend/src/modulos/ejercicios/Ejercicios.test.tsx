import { screen, waitFor, within } from "@testing-library/react";
import { userEvent } from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { beforeEach, describe, expect, it } from "vitest";

import { montar } from "@/test/montar";
import { servidor } from "@/test/servidor";

import type { Ejercicio, Facetas } from "./api";
import { Ejercicios } from "./Ejercicios";

function ejercicio(extra: Partial<Ejercicio> = {}): Ejercicio {
  return {
    id: 1,
    external_id: "0001",
    name: "Press de banca",
    slug: "press-banca",
    body_part: "chest",
    body_part_label: "Pecho",
    equipment: "barbell",
    equipment_label: "Barra",
    target_muscle: { slug: "pectorals", name: "Pectorales" },
    secondary_muscles: [],
    is_cardio: false,
    is_bodyweight: false,
    is_unilateral: false,
    image: null,
    animation: null,
    attribution: "",
    steps: [],
    ...extra,
  };
}

const FACETAS: Facetas = {
  total: 1,
  body_part: [
    { valor: "chest", etiqueta: "Pecho", n: 12 },
    { valor: "back", etiqueta: "Espalda", n: 9 },
  ],
  equipment: [{ valor: "barbell", etiqueta: "Barra", n: 7 }],
  muscle: [{ valor: "pectorals", etiqueta: "Pectorales", n: 12 }],
};

const pedidas: string[] = [];

function responder(ejercicios: Ejercicio[] = [ejercicio()]) {
  servidor.use(
    http.get("/api/ejercicios/facetas/", () => HttpResponse.json(FACETAS)),
    http.get("/api/ejercicios/", ({ request }) => {
      pedidas.push(new URL(request.url).search);
      return HttpResponse.json({
        count: ejercicios.length,
        next: null,
        previous: null,
        results: ejercicios,
      });
    }),
    http.get("/api/mapa-corporal/", () => HttpResponse.json({ vistas: [], musculos: [] })),
  );
}

beforeEach(() => {
  pedidas.length = 0;
  responder();
});

describe("Ejercicios", () => {
  it("pinta el catálogo con su recuento", async () => {
    montar(<Ejercicios />, { ruta: "/ejercicios/" });

    expect(await screen.findByRole("link", { name: /Press de banca/ })).toHaveAttribute(
      "href",
      "/ejercicios/press-banca/",
    );
  });

  it("los chips llevan cuántos ejercicios devuelven", async () => {
    montar(<Ejercicios />, { ruta: "/ejercicios/" });

    const pecho = await screen.findByRole("button", { name: /Pecho/ });
    expect(pecho).toHaveTextContent("12");
  });

  it("pulsar un chip lo manda al servidor", async () => {
    montar(<Ejercicios />, { ruta: "/ejercicios/" });
    await screen.findByRole("button", { name: /Pecho/ });

    await userEvent.click(screen.getByRole("button", { name: /Pecho/ }));

    await waitFor(() => expect(pedidas.at(-1)).toContain("body_part=chest"));
  });

  it("pulsar el chip activo lo quita", async () => {
    montar(<Ejercicios />, { ruta: "/ejercicios/?body_part=chest" });

    const pecho = await screen.findByRole("button", { name: /Pecho/ });
    expect(pecho).toHaveAttribute("aria-pressed", "true");
    await userEvent.click(pecho);

    await waitFor(() => expect(pedidas.at(-1)).not.toContain("body_part"));
  });

  it("pulsar un chip conserva los otros filtros", async () => {
    montar(<Ejercicios />, { ruta: "/ejercicios/?q=press&muscle=pectorals" });
    await screen.findByRole("button", { name: /Barra/ });

    await userEvent.click(screen.getByRole("button", { name: /Barra/ }));

    await waitFor(() => expect(pedidas.at(-1)).toContain("equipment=barbell"));
    expect(pedidas.at(-1)).toContain("q=press");
    expect(pedidas.at(-1)).toContain("muscle=pectorals");
  });

  it("«Limpiar» deja la URL sin filtros", async () => {
    montar(<Ejercicios />, { ruta: "/ejercicios/?q=press&body_part=chest" });

    await userEvent.click(await screen.findByRole("button", { name: "Limpiar" }));

    await waitFor(() => expect(pedidas.at(-1)).toBe(""));
  });

  it("los filtros se leen de la URL, no del estado", async () => {
    montar(<Ejercicios />, { ruta: "/ejercicios/?muscle=pectorals&equipment=barbell" });

    await waitFor(() => expect(pedidas[0]).toContain("muscle=pectorals"));
    expect(pedidas[0]).toContain("equipment=barbell");
  });

  it("cambiar de filtro vuelve a la primera página", async () => {
    montar(<Ejercicios />, { ruta: "/ejercicios/?page=7" });
    await screen.findByRole("button", { name: /Barra/ });

    await userEvent.click(screen.getByRole("button", { name: /Barra/ }));

    await waitFor(() => expect(pedidas.at(-1)).not.toContain("page=7"));
  });

  it("buscar no manda una petición por tecla", async () => {
    montar(<Ejercicios />, { ruta: "/ejercicios/" });
    await screen.findByRole("link", { name: /Press de banca/ });
    const antes = pedidas.length;

    await userEvent.type(screen.getByLabelText("Buscar ejercicio"), "press");

    await waitFor(() => expect(pedidas.at(-1)).toContain("q=press"));
    expect(pedidas.length - antes).toBe(1);
  });

  it("sin resultados ofrece quitar los filtros", async () => {
    responder([]);

    montar(<Ejercicios />, { ruta: "/ejercicios/?q=inexistente" });

    expect(await screen.findByText("Ningún ejercicio con esos filtros")).toBeVisible();
    expect(screen.getByRole("button", { name: "Quitar los filtros" })).toBeVisible();
  });

  it("el atajo para crear uno propio está siempre, también sin resultados", async () => {
    responder([]);

    montar(<Ejercicios />, { ruta: "/ejercicios/?q=inexistente" });

    const crear = await screen.findByRole("link", { name: /Crea tu ejercicio/ });
    expect(crear).toHaveAttribute("href", "/ejercicios/nuevo/");
  });

  it("un ejercicio unilateral lo dice en la tarjeta", async () => {
    responder([ejercicio({ is_unilateral: true })]);

    montar(<Ejercicios />, { ruta: "/ejercicios/" });

    const tarjeta = await screen.findByRole("link", { name: /Press de banca/ });
    expect(within(tarjeta).getByText("Unilateral")).toBeVisible();
  });
});
