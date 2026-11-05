import { screen, waitFor, within } from "@testing-library/react";
import { userEvent } from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { Route, Routes } from "react-router";
import { beforeEach, describe, expect, it } from "vitest";

import { montar } from "@/test/montar";
import { servidor } from "@/test/servidor";

import type { Plan as DatosDePlan } from "./api";
import { DiaDelPlan } from "./DiaDelPlan";
import { Plan } from "./Plan";

const DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"];

const VACIO: DatosDePlan = {
  hoy_weekday: 2,
  programa: null,
  programas: [],
  semana: DIAS.map((etiqueta, weekday) => ({
    weekday,
    etiqueta,
    entrada_id: null,
    rutina: null,
  })),
  rutinas: [],
};

const CON_PROGRAMA: DatosDePlan = {
  ...VACIO,
  programa: { id: 1, nombre: "Volumen", descripcion: "" },
  programas: [{ id: 1, nombre: "Volumen", activo: true }],
  semana: DIAS.map((etiqueta, weekday) => ({
    weekday,
    etiqueta,
    entrada_id: weekday + 10,
    rutina:
      weekday === 0 ? { id: 7, nombre: "Empuje A", n_ejercicios: 4, imagenes: [] } : null,
  })),
  rutinas: [
    { id: 7, nombre: "Empuje A", descripcion: "", n_ejercicios: 4, imagenes: [], dias: ["Lunes"] },
    { id: 8, nombre: "Pierna", descripcion: "", n_ejercicios: 6, imagenes: [], dias: [] },
  ],
};

const RUTINA_7 = {
  id: 7,
  name: "Empuje A",
  description: "",
  source: "manual",
  source_label: "Manual",
  created_at: "2026-01-01T00:00:00Z",
  exercises: [
    {
      id: 1,
      routine: 7,
      exercise: 101,
      order: 0,
      target_sets: 4,
      target_reps_min: 6,
      target_reps_max: 8,
      rest_seconds: 180,
      exercise_detail: {
        id: 101,
        external_id: "x1",
        name: "Press de banca",
        slug: "press-banca",
        body_part: "chest",
        body_part_label: "Pecho",
        equipment: "barbell",
        equipment_label: "Barra",
        target_muscle: { slug: "pectorals", name: "Pectoral" },
        secondary_muscles: [],
        is_cardio: false,
        is_bodyweight: false,
        image: null,
        animation: null,
        attribution: "",
        steps: [],
      },
    },
  ],
};

function responder(datos: DatosDePlan) {
  servidor.use(http.get("/api/plan/", () => HttpResponse.json(datos)));
}

function responderRutina7() {
  servidor.use(http.get("/api/rutinas/7/", () => HttpResponse.json(RUTINA_7)));
}

beforeEach(() => responder(CON_PROGRAMA));

describe("Plan", () => {
  it("sin programa manda a crear uno", async () => {
    responder(VACIO);

    montar(<Plan />, { ruta: "/plan/" });

    expect(await screen.findByText("Organiza tu primera semana")).toBeVisible();
    expect(screen.getByRole("link", { name: "Crear programa" })).toHaveAttribute(
      "href",
      "/programas/nuevo/",
    );
  });

  it("un día sin rutina es descanso, no falta de plan", async () => {
    montar(<Plan />, { ruta: "/plan/" });

    await screen.findByRole("region", { name: "Tu semana" });
    expect(screen.getAllByText("Descanso")).toHaveLength(6);
    expect(screen.queryByText("Organiza tu primera semana")).not.toBeInTheDocument();
  });

  it("los siete días están siempre", async () => {
    montar(<Plan />, { ruta: "/plan/" });

    for (const dia of DIAS) {
      expect(await screen.findByText(dia)).toBeVisible();
    }
  });

  it("un día con rutina se desglosa, con editar y entrenar", async () => {
    responderRutina7();
    montar(<Plan />, { ruta: "/plan/" });

    const semana = await screen.findByRole("region", { name: "Tu semana" });
    await userEvent.click(within(semana).getByRole("button", { name: /Lunes/ }));
    const hoja = await screen.findByRole("dialog", { name: "Lunes" });
    expect(within(hoja).getByRole("heading", { name: "Lunes" })).toHaveFocus();
    expect(within(hoja).getByRole("button", { name: "Cerrar panel" })).not.toHaveFocus();
    expect(await within(hoja).findByText("Press de banca")).toBeVisible();
    expect(within(hoja).getByRole("link", { name: "Editar rutina" })).toHaveAttribute(
      "href",
      "/rutinas/7/",
    );
    expect(within(hoja).getByRole("button", { name: /Entrenar/ })).toBeVisible();
  });

  it("desde el desglose se puede cambiar la rutina del día", async () => {
    responderRutina7();
    montar(<Plan />, { ruta: "/plan/" });

    const semana = await screen.findByRole("region", { name: "Tu semana" });
    await userEvent.click(within(semana).getByRole("button", { name: /Lunes/ }));
    await userEvent.click(await screen.findByRole("button", { name: /Cambiar la rutina/ }));
    expect(screen.getByRole("radio", { name: /Empuje A/ })).toBeChecked();
  });

  it("un día de descanso abre la asignación directamente", async () => {
    montar(<Plan />, { ruta: "/plan/" });

    const semana = await screen.findByRole("region", { name: "Tu semana" });
    await userEvent.click(within(semana).getByRole("button", { name: /Martes/ }));
    const hoja = await screen.findByRole("dialog", { name: "Martes" });
    expect(within(hoja).getByRole("radio", { name: /Descanso/ })).toBeChecked();
  });

  it("la biblioteca dice en qué días está cada rutina", async () => {
    montar(<Plan />, { ruta: "/plan/" });

    const biblioteca = await screen.findByRole("region", { name: "Tus rutinas" });
    const empuje = within(biblioteca).getByRole("link", { name: /Empuje A/ });
    expect(within(empuje).getByText(/4 ejercicios · Lunes/)).toBeVisible();
  });

  it("una rutina sin asignar lo dice", async () => {
    montar(<Plan />, { ruta: "/plan/" });

    const biblioteca = await screen.findByRole("region", { name: "Tus rutinas" });
    const pierna = within(biblioteca).getByRole("link", { name: /Pierna/ });
    expect(within(pierna).getByText(/sin asignar/)).toBeVisible();
  });

  it("con un solo programa no ofrece cambiar de programa", async () => {
    montar(<Plan />, { ruta: "/plan/" });

    await screen.findByRole("region", { name: "Tu semana" });
    expect(screen.queryByRole("button", { name: "Volumen" })).not.toBeInTheDocument();
  });

  it("con varios sí, y activa el que se pulse", async () => {
    responder({
      ...CON_PROGRAMA,
      programas: [
        { id: 1, nombre: "Volumen", activo: true },
        { id: 2, nombre: "Definición", activo: false },
      ],
    });
    let activado: string | null = null;
    servidor.use(
      http.post("/api/programas/:id/activate/", ({ params }) => {
        activado = String(params["id"]);
        return HttpResponse.json({});
      }),
    );
    montar(<Plan />, { ruta: "/plan/" });

    await userEvent.click(await screen.findByRole("button", { name: "Programas" }));
    await userEvent.click(screen.getByRole("button", { name: /Definición/ }));

    await waitFor(() => expect(activado).toBe("2"));
  });
});

describe("DiaDelPlan", () => {
  function montarDia(weekday: number) {
    return montar(
      <Routes>
        <Route path="/plan/dia/:weekday" element={<DiaDelPlan />} />
      </Routes>,
      { ruta: `/plan/dia/${weekday}` },
    );
  }

  it("descanso va primero, antes que las rutinas", async () => {
    montarDia(1);

    await screen.findByText("Descanso");
    const opciones = screen.getAllByRole("radio");
    expect(opciones).toHaveLength(3);
    expect(opciones[0]).toBeChecked();
  });

  it("marca la rutina que ya está asignada", async () => {
    montarDia(0);

    const empuje = await screen.findByRole("radio", { name: /Empuje A/ });
    expect(empuje).toBeChecked();
  });

  it("guarda lo elegido sobre la entrada de ese día", async () => {
    let recibido: unknown = null;
    let camino = "";
    servidor.use(
      http.patch("/api/dias/:id/", async ({ request, params }) => {
        recibido = await request.json();
        camino = String(params["id"]);
        return HttpResponse.json({});
      }),
    );
    montarDia(1);

    await userEvent.click(await screen.findByRole("radio", { name: /Pierna/ }));
    await userEvent.click(screen.getByRole("button", { name: "Guardar" }));

    await waitFor(() => expect(recibido).toEqual({ routine: 8 }));
    expect(camino).toBe("11");
  });

  it("elegir no guarda: hay que pulsar Guardar", async () => {
    let llamado = false;
    servidor.use(
      http.patch("/api/dias/:id/", () => {
        llamado = true;
        return HttpResponse.json({});
      }),
    );
    montarDia(1);

    await userEvent.click(await screen.findByRole("radio", { name: /Pierna/ }));

    expect(llamado).toBe(false);
  });

  it("un día que no existe lo dice en vez de quedarse en blanco", async () => {
    montarDia(9);

    expect(await screen.findByText("Ese día no está en tu plan")).toBeVisible();
  });

  it("sin rutinas ofrece crear una", async () => {
    responder({ ...CON_PROGRAMA, rutinas: [] });

    montarDia(1);

    expect(await screen.findByText("No tienes ninguna rutina todavía")).toBeVisible();
    expect(screen.getByRole("link", { name: "Crear una rutina" })).toBeVisible();
    expect(screen.queryByRole("radio")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Guardar" })).not.toBeInTheDocument();
  });
});
