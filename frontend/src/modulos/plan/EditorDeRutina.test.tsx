import { screen, waitFor } from "@testing-library/react";
import { userEvent } from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { Route, Routes } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { montar } from "@/test/montar";
import { servidor } from "@/test/servidor";

import type { EjercicioDeRutina, Rutina } from "./api";
import { EditorDeRutina } from "./EditorDeRutina";

function item(id: number, nombre: string, extra: Partial<EjercicioDeRutina> = {}) {
  return {
    id,
    routine: 7,
    exercise: id * 100,
    exercise_detail: {
      id: id * 100,
      external_id: "0001",
      name: nombre,
      slug: nombre.toLowerCase().replace(/ /g, "-"),
      body_part: "chest",
      body_part_label: "Pecho",
      equipment: "barbell",
      equipment_label: "Barra",
      target_muscle: null,
      secondary_muscles: [],
      is_cardio: false,
      is_bodyweight: false,
      image: null,
      animation: null,
      attribution: "",
      steps: [],
    },
    order: id - 1,
    target_sets: 4,
    target_reps_min: 6,
    target_reps_max: 8,
    rest_seconds: 180,
    ...extra,
  } as EjercicioDeRutina;
}

const RUTINA: Rutina = {
  id: 7,
  name: "Empuje A",
  description: "",
  source: "manual",
  source_label: "Manual",
  created_at: "2026-09-01T10:00:00Z",
  exercises: [item(1, "Press de banca"), item(2, "Press militar")],
};

function responder(rutina: Partial<Rutina> = {}, dias: string[] = ["Lunes"]) {
  servidor.use(
    http.get("/api/rutinas/:id/", () => HttpResponse.json({ ...RUTINA, ...rutina })),
    http.get("/api/plan/", () =>
      HttpResponse.json({
        hoy_weekday: 0,
        programa: { id: 1, nombre: "Volumen", descripcion: "" },
        programas: [],
        semana: [],
        rutinas: [{ id: 7, nombre: "Empuje A", descripcion: "", n_ejercicios: 2, dias }],
      }),
    ),
    http.get("/api/ejercicios/facetas/", () =>
      HttpResponse.json({ total: 0, body_part: [], equipment: [], muscle: [] }),
    ),
    http.get("/api/ejercicios/", () =>
      HttpResponse.json({ count: 0, next: null, previous: null, results: [] }),
    ),
    http.get("/api/mapa-corporal/", () => HttpResponse.json({ vistas: [], musculos: [] })),
  );
}

function montarEditor() {
  return montar(
    <Routes>
      <Route path="/rutinas/:id" element={<EditorDeRutina />} />
    </Routes>,
    { ruta: "/rutinas/7" },
  );
}

beforeEach(() => responder());

afterEach(() => vi.restoreAllMocks());

describe("Editor con borrador", () => {
  it("presenta el resumen y limita el orden", async () => {
    montarEditor();
    expect(await screen.findByText("Press de banca")).toBeVisible();
    expect(screen.getAllByText("4 × 6–8 · 180 s")).toHaveLength(2);
    expect(screen.getByRole("button", { name: "Subir Press de banca" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Bajar Press militar" })).toBeDisabled();
  });

  it("editar solo modifica el borrador hasta guardar todo", async () => {
    let recibido: unknown = null;
    servidor.use(http.patch("/api/rutinas/7/", async ({ request }) => {
      recibido = await request.json();
      return HttpResponse.json({ ...RUTINA, exercises: [item(1, "Press de banca", { target_sets: 5 }), item(2, "Press militar")] });
    }));
    montarEditor();
    await userEvent.click(await screen.findByRole("button", { name: /^Press de banca/ }));
    await userEvent.click(screen.getByRole("button", { name: "Subir Series" }));
    await userEvent.click(screen.getByRole("button", { name: "Aplicar al borrador" }));
    expect(recibido).toBeNull();
    expect(screen.getByRole("button", { name: "Entrenar" })).toBeDisabled();
    await userEvent.click(screen.getByRole("button", { name: "Guardar cambios" }));
    await waitFor(() => expect(recibido).toMatchObject({ name: "Empuje A", exercises: [{ id: 1, target_sets: 5 }, { id: 2 }] }));
    expect(await screen.findByText(/Rutina guardada/)).toBeVisible();
    expect(screen.getByRole("button", { name: "Entrenar" })).toBeEnabled();
  });

  it("reordenar y quitar se mandan juntos, sin peticiones intermedias", async () => {
    let recibido: unknown = null;
    servidor.use(http.patch("/api/rutinas/7/", async ({ request }) => { recibido = await request.json(); return HttpResponse.json({ ...RUTINA, exercises: [item(2, "Press militar")] }); }));
    montarEditor();
    await userEvent.click(await screen.findByRole("button", { name: "Bajar Press de banca" }));
    expect(screen.getByRole("button", { name: "Subir Press militar" })).toBeDisabled();
    await userEvent.click(screen.getByRole("button", { name: /^Press de banca/ }));
    await userEvent.click(screen.getByRole("button", { name: "Quitar de la rutina" }));
    expect(recibido).toBeNull();
    await userEvent.click(screen.getByRole("button", { name: "Guardar cambios" }));
    await waitFor(() => expect(recibido).toMatchObject({ exercises: [{ id: 2 }] }));
    expect((recibido as { exercises: unknown[] }).exercises).toHaveLength(1);
  });

  it("un fallo conserva los cambios y permite reintentar", async () => {
    servidor.use(http.patch("/api/rutinas/7/", () => HttpResponse.json({ detail: "No se pudo guardar." }, { status: 500 })));
    montarEditor();
    const nombre = await screen.findByLabelText("Nombre");
    await userEvent.clear(nombre); await userEvent.type(nombre, "Mi nuevo nombre");
    await userEvent.click(screen.getByRole("button", { name: "Guardar cambios" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("No se pudo guardar.");
    expect(nombre).toHaveValue("Mi nuevo nombre");
    expect(screen.getByRole("button", { name: "Guardar cambios" })).toBeEnabled();
  });

  it("muestra errores anidados junto al ejercicio", async () => {
    servidor.use(http.patch("/api/rutinas/7/", () => HttpResponse.json({ exercises: [{ target_sets: ["Demasiadas series."] }, {}] }, { status: 400 })));
    montarEditor(); await userEvent.type(await screen.findByLabelText("Nombre"), " B");
    await userEvent.click(screen.getByRole("button", { name: "Guardar cambios" }));
    expect(await screen.findByText("Demasiadas series.")).toBeVisible();
  });

  it("avisa de los días afectados", async () => {
    responder({}, ["Lunes", "Jueves"]); montarEditor();
    expect(await screen.findByText(/Asignada a Lunes, Jueves/)).toHaveTextContent("todos esos días");
  });

  it("una rutina vacía se puede completar pero no entrenar", async () => {
    responder({ exercises: [] }); montarEditor();
    expect(await screen.findByText("Empieza con tu primer ejercicio.")).toBeVisible();
    expect(screen.getByRole("button", { name: "Entrenar" })).toBeDisabled();
  });

  it("una ajena muestra 404 sin reintentos", async () => {
    servidor.use(http.get("/api/rutinas/:id/", () => HttpResponse.json({ detail: "No encontrado." }, { status: 404 })));
    montarEditor(); expect(await screen.findByText("Esa rutina no es tuya o ya no existe.")).toBeVisible();
    expect(screen.queryByRole("button", { name: "Reintentar" })).not.toBeInTheDocument();
  });

  it("abre el buscador bajo demanda, con material y paginación", async () => {
    let consulta = "";
    servidor.use(http.get("/api/ejercicios/", ({ request }) => { consulta = request.url; return HttpResponse.json({ count: 1, next: null, previous: null, results: [item(3, "Fondos").exercise_detail] }); }));
    montarEditor(); await screen.findByLabelText("Nombre");
    expect(screen.queryByLabelText("Buscar ejercicio")).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /Añadir ejercicio/ }));
    expect(await screen.findByText("Fondos")).toBeVisible();
    expect(consulta).toContain("mi_material=1"); expect(consulta).toContain("page=1");
    await userEvent.click(screen.getByRole("button", { name: /^Fondos/ }));
    await userEvent.click(screen.getByRole("button", { name: "Añadir al borrador" }));
    expect(screen.getByRole("dialog", { name: "Añadir ejercicio" })).toBeVisible();
    expect(screen.getByRole("button", { name: "Listo · 3" })).toBeVisible();
    await userEvent.click(screen.getByRole("button", { name: "Listo · 3" }));
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(screen.getByText("Fondos")).toBeVisible();
  });

  it("no crea nada al abrir o cancelar una rutina nueva", async () => {
    montar(<EditorDeRutina nueva />, { ruta: "/rutinas/nueva/" });
    expect(screen.getByRole("heading", { name: "Nueva rutina" })).toBeVisible();
    await userEvent.click(screen.getByRole("button", { name: "Guardar rutina" }));
    expect(screen.getByRole("alert")).toHaveTextContent("Escribe un nombre");
    await userEvent.type(screen.getByLabelText("Nombre"), "Pierna");
    await userEvent.click(screen.getByRole("button", { name: "Guardar rutina" }));
    expect(screen.getByRole("alert")).toHaveTextContent("Añade al menos un ejercicio");
  });

  it("permite quedarse al cancelar y descartar después", async () => {
    montar(<Routes><Route path="/rutinas/:id" element={<EditorDeRutina />} /><Route path="/plan" element={<p>Mi semana</p>} /></Routes>, { ruta: "/rutinas/7" });
    await userEvent.type(await screen.findByLabelText("Nombre"), " B");
    await userEvent.click(screen.getByRole("link", { name: "Cancelar" }));
    await userEvent.click(await screen.findByRole("button", { name: "Seguir editando" }));
    expect(screen.queryByRole("dialog", { name: "Cambios sin guardar" })).not.toBeInTheDocument();
    expect(screen.getByLabelText("Nombre")).toHaveValue("Empuje A B");
    await userEvent.click(screen.getByRole("link", { name: "Cancelar" }));
    await userEvent.click(await screen.findByRole("button", { name: "Salir sin guardar" }));
    expect(await screen.findByText("Mi semana")).toBeVisible();
  });

  it("entrena solo la versión guardada", async () => {
    let recibido: unknown;
    servidor.use(http.post("/api/entrenamientos/", async ({ request }) => { recibido = await request.json(); return HttpResponse.json({ id: 42 }); }));
    montar(<Routes><Route path="/rutinas/:id" element={<EditorDeRutina />} /><Route path="/entrenamientos/:id" element={<p>Entrenando</p>} /></Routes>, { ruta: "/rutinas/7" });
    await userEvent.click(await screen.findByRole("button", { name: "Entrenar" }));
    expect(await screen.findByText("Entrenando")).toBeVisible(); expect(recibido).toEqual({ routine: 7 });
  });
});
