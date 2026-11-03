import { screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { Route, Routes } from "react-router";
import { beforeEach, describe, expect, it } from "vitest";

import { montar } from "@/test/montar";
import { servidor } from "@/test/servidor";

import type { Ejercicio } from "./api";
import { FichaDeEjercicio } from "./FichaDeEjercicio";

const MAPA = {
  vistas: [],
  musculos: ["pectorals", "triceps"],
};

function ficha(extra: Partial<Ejercicio> = {}): Ejercicio {
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
    secondary_muscles: [{ slug: "triceps", name: "Tríceps" }],
    is_cardio: false,
    is_bodyweight: false,
    is_unilateral: false,
    image: "/media/press.png",
    animation: null,
    attribution: "© Gym visual — https://gymvisual.com/",
    steps: ["Baja la barra al pecho.", "Empuja hasta estirar."],
    ...extra,
  };
}

function responder(datos: Partial<Ejercicio> | null, estado = 200) {
  servidor.use(
    http.get("/api/mapa-corporal/", () => HttpResponse.json(MAPA)),
    http.get("/api/ejercicios/:slug/", () =>
      datos === null
        ? HttpResponse.json({ detail: "No encontrado." }, { status: estado })
        : HttpResponse.json(ficha(datos)),
    ),
  );
}

function montarFicha(slug = "press-banca") {
  return montar(
    <Routes>
      <Route path="/ejercicios/:slug" element={<FichaDeEjercicio />} />
    </Routes>,
    { ruta: `/ejercicios/${slug}` },
  );
}

beforeEach(() => responder({}));

describe("FichaDeEjercicio", () => {
  it("enseña los pasos y la atribución", async () => {
    montarFicha();

    expect(await screen.findByText("Baja la barra al pecho.")).toBeVisible();
    expect(screen.getByText(/gymvisual\.com/)).toBeVisible();
  });

  it("dice los músculos que el mapa no sabe pintar", async () => {
    responder({
      secondary_muscles: [
        { slug: "triceps", name: "Tríceps" },
        { slug: "rotator-cuff", name: "Manguito rotador" },
      ],
    });

    montarFicha();

    expect(await screen.findByText(/Fuera del mapa: Manguito rotador/)).toBeVisible();
  });

  it("un ejercicio propio dice por qué no tiene imagen", async () => {
    responder({ image: null, animation: null, attribution: "" });

    montarFicha();

    expect(await screen.findByText("Sin referencia visual")).toBeVisible();
  });

  it("un ejercicio que no es tuyo no se distingue de uno que no existe", async () => {
    responder(null, 404);

    montarFicha("de-otra-persona");

    expect(await screen.findByText("Ese ejercicio no está en tu catálogo")).toBeVisible();
  });

  it("un fallo de red ofrece reintentar, no dice que no existe", async () => {
    servidor.use(
      http.get("/api/mapa-corporal/", () => HttpResponse.json(MAPA)),
      http.get("/api/ejercicios/:slug/", () => HttpResponse.error()),
    );

    montarFicha();

    expect(await screen.findByRole("button", { name: "Reintentar" })).toBeVisible();
  });

  it("no repite «peso corporal» cuando el equipamiento ya lo dice", async () => {
    responder({ equipment: "body weight", equipment_label: "Peso corporal", is_bodyweight: true });

    montarFicha();

    expect(await screen.findAllByText(/peso corporal/i)).toHaveLength(1);
  });

  it("pero lo marca cuando el material es otro", async () => {
    responder({ equipment: "barbell", equipment_label: "Barra", is_bodyweight: true });

    montarFicha();

    expect(await screen.findByText("Cuenta tu peso corporal")).toBeVisible();
  });

  it("sin instrucciones lo dice en vez de dejar la lista vacía", async () => {
    responder({ steps: [] });

    montarFicha();

    expect(await screen.findByText("Sin instrucciones.")).toBeVisible();
  });
});
