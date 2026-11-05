import { screen, waitFor } from "@testing-library/react";
import { userEvent } from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { Route, Routes } from "react-router";
import { beforeEach, describe, expect, it } from "vitest";

import { montar } from "@/test/montar";
import { servidor } from "@/test/servidor";

import type { Inicio as DatosDeInicio } from "./api";
import { Inicio } from "./Inicio";

const VACIO: DatosDeInicio = {
  hoy: "2026-09-16",
  semana: [
    { fecha: "2026-09-14", inicial: "L", numero: 14, hoy: false, futuro: false, entrenado: false, planificado: false },
    { fecha: "2026-09-15", inicial: "M", numero: 15, hoy: false, futuro: false, entrenado: false, planificado: false },
    { fecha: "2026-09-16", inicial: "X", numero: 16, hoy: true, futuro: false, entrenado: false, planificado: false },
    { fecha: "2026-09-17", inicial: "J", numero: 17, hoy: false, futuro: true, entrenado: false, planificado: false },
    { fecha: "2026-09-18", inicial: "V", numero: 18, hoy: false, futuro: true, entrenado: false, planificado: false },
    { fecha: "2026-09-19", inicial: "S", numero: 19, hoy: false, futuro: true, entrenado: false, planificado: false },
    { fecha: "2026-09-20", inicial: "D", numero: 20, hoy: false, futuro: true, entrenado: false, planificado: false },
  ],
  hoy_toca: { estado: "sin_programa", sesion: null, rutina: null },
  peso: { ultimo: null, cambio: null, objetivo: "Mantener", meta_kg: null, serie: null },
  racha: {
    semanas: 0,
    hechas_esta_semana: 0,
    planificadas_esta_semana: 0,
    total_sesiones: 0,
  },
  mapa_corporal: {},
};

function responder(datos: Partial<DatosDeInicio> = {}) {
  servidor.use(
    http.get("/api/inicio/", () => HttpResponse.json({ ...VACIO, ...datos })),
    http.get("/api/mapa-corporal/", () => HttpResponse.json({ vistas: [], musculos: [] })),
  );
}

beforeEach(() => responder());

describe("Inicio", () => {
  it("lo de hoy va primero, y la constancia antes que el peso", async () => {
    montar(<Inicio />);

    const titulos = (await screen.findAllByRole("heading", { level: 2 })).map(
      (h) => h.textContent,
    );
    expect(titulos[0]).toBe("Lo de hoy");
    expect(titulos.indexOf("Constancia")).toBeLessThan(titulos.indexOf("Peso corporal"));
  });

  it("con una rutina asignada enseña cuál y sus ejercicios", async () => {
    responder({
      hoy_toca: {
        estado: "rutina",
        sesion: null,
        rutina: {
          id: 7,
          nombre: "Empuje A",
          ejercicios: [
            { id: 1, name: "Press de banca", image: null },
            { id: 2, name: "Press militar", image: null },
          ],
        },
      },
    });

    montar(<Inicio />);

    expect(await screen.findByText("Empuje A")).toBeVisible();
    expect(screen.getByRole("img", { name: "Press de banca" })).toBeVisible();
    expect(screen.getByRole("img", { name: "Press militar" })).toBeVisible();
    expect(screen.getByRole("button", { name: "Empezar" })).toBeVisible();
  });

  it("empezar crea la sesión de esa rutina y lleva a entrenar", async () => {
    responder({
      hoy_toca: {
        estado: "rutina",
        sesion: null,
        rutina: { id: 7, nombre: "Empuje A", ejercicios: [{ id: 1, name: "Press de banca", image: null }] },
      },
    });
    let recibido: unknown = null;
    servidor.use(
      http.post("/api/entrenamientos/", async ({ request }) => {
        recibido = await request.json();
        return HttpResponse.json({ id: 42 }, { status: 201 });
      }),
    );
    montar(
      <Routes>
        <Route path="/" element={<Inicio />} />
        <Route path="/entrenamientos/:id" element={<p>Entrenando</p>} />
      </Routes>,
    );

    await userEvent.click(await screen.findByRole("button", { name: "Empezar" }));

    await waitFor(() => expect(recibido).toEqual({ routine: 7 }));
    expect(await screen.findByText("Entrenando")).toBeVisible();
  });

  it("en un día de descanso se entrena sin rutina", async () => {
    responder({ hoy_toca: { estado: "descanso", sesion: null, rutina: null } });
    let recibido: unknown = null;
    servidor.use(
      http.post("/api/entrenamientos/", async ({ request }) => {
        recibido = await request.json();
        return HttpResponse.json({ id: 43 }, { status: 201 });
      }),
    );
    montar(<Inicio />);

    await userEvent.click(await screen.findByRole("button", { name: "Entrenar igualmente" }));

    await waitFor(() => expect(recibido).toEqual({}));
  });

  it("una rutina sin ejercicios no ofrece empezar", async () => {
    responder({
      hoy_toca: {
        estado: "rutina",
        sesion: null,
        rutina: { id: 7, nombre: "Empuje A", ejercicios: [] },
      },
    });

    montar(<Inicio />);

    expect(await screen.findByRole("link", { name: "Añadir ejercicios" })).toBeVisible();
    expect(screen.queryByRole("button", { name: "Empezar" })).not.toBeInTheDocument();
  });

  it("descanso y falta de plan no dicen lo mismo", async () => {
    responder({ hoy_toca: { estado: "descanso", sesion: null, rutina: null } });

    montar(<Inicio />);

    expect(await screen.findByText("Descanso")).toBeVisible();
    expect(screen.queryByText(/Todavía no tienes un plan/)).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Entrenar igualmente" })).toBeVisible();
  });

  it("sin programa manda a montar la semana", async () => {
    montar(<Inicio />);

    expect(await screen.findByText("Todavía no tienes un plan")).toBeVisible();
    expect(screen.getByRole("link", { name: "Montar mi semana" })).toBeVisible();
  });

  it("un entrenamiento a medias manda sobre todo lo demás", async () => {
    responder({
      hoy_toca: {
        estado: "sesion_abierta",
        sesion: { id: 42, fecha: "2026-09-16" },
        rutina: null,
      },
    });

    montar(<Inicio />);

    const continuar = await screen.findByRole("link", { name: "Continuar" });
    expect(continuar).toHaveAttribute("href", "/entrenamientos/42/");
  });

  it("el cambio de peso lleva la dirección además del color", async () => {
    responder({
      peso: {
        ultimo: { fecha: "2026-09-16", kg: 81.5 },
        cambio: 1.5,
        objetivo: "Ganar masa",
        meta_kg: 85,
        serie: null,
      },
    });

    montar(<Inicio />);

    expect(await screen.findByText(/↑ 1\.5/)).toBeVisible();
  });

  it("un cambio de cero no pinta insignia", async () => {
    responder({
      peso: {
        ultimo: { fecha: "2026-09-16", kg: 80 },
        cambio: 0,
        objetivo: "Mantener",
        meta_kg: null,
        serie: null,
      },
    });

    montar(<Inicio />);

    await screen.findByText("80");
    expect(screen.queryByText(/[↑↓]/)).not.toBeInTheDocument();
  });

  it("con un solo registro dice que falta otro, en vez de dibujar una línea plana", async () => {
    responder({
      peso: {
        ultimo: { fecha: "2026-09-16", kg: 80 },
        cambio: null,
        objetivo: "Mantener",
        meta_kg: null,
        serie: null,
      },
    });

    montar(<Inicio />);

    expect(await screen.findByText(/Con dos registros o más/)).toBeVisible();
  });

  it("si la API falla ofrece reintentar en vez de quedarse en blanco", async () => {
    servidor.use(http.get("/api/inicio/", () => HttpResponse.error()));

    montar(<Inicio />);

    expect(await screen.findByRole("button", { name: "Reintentar" })).toBeVisible();
  });
});
