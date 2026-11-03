import { screen, waitFor, within } from "@testing-library/react";
import { userEvent } from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { Route, Routes } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { montar } from "@/test/montar";
import { servidor } from "@/test/servidor";

import type { OpcionesDePerfil, Perfil as DatosDePerfil } from "./api";
import { EliminarCuenta } from "./EliminarCuenta";
import { Perfil } from "./Perfil";

vi.mock("@/lib/navegar", () => ({ salirDeLaSpa: vi.fn() }));
const { salirDeLaSpa } = await import("@/lib/navegar");

const PERFIL: DatosDePerfil = {
  id: 1,
  username: "ana",
  email: "ana@example.com",
  first_name: "Ana",
  last_name: "Ruiz",
  goal: "bulk",
  experience_level: "intermediate",
  sex: "female",
  birth_date: "1998-03-15",
  height_cm: 168,
  age: 28,
  target_weight_kg: "62.00",
  weekly_weight_change_target_kg: "0.25",
  available_days_per_week: 4,
  available_equipment: ["barbell"],
  injuries_notes: "",
};

const OPCIONES: OpcionesDePerfil = {
  goal: [
    { valor: "bulk", etiqueta: "Volumen" },
    { valor: "cut", etiqueta: "Definición" },
  ],
  experience_level: [
    { valor: "beginner", etiqueta: "Principiante" },
    { valor: "intermediate", etiqueta: "Intermedio" },
  ],
  sex: [
    { valor: "female", etiqueta: "Mujer" },
    { valor: "male", etiqueta: "Hombre" },
  ],
  available_equipment: [
    { valor: "barbell", etiqueta: "Barra" },
    { valor: "cable", etiqueta: "Poleas" },
  ],
};

function responder(extra: Partial<DatosDePerfil> = {}) {
  servidor.use(
    http.get("/api/perfil/", () => HttpResponse.json({ ...PERFIL, ...extra })),
    http.get("/api/perfil/opciones/", () => HttpResponse.json(OPCIONES)),
  );
}

describe("Perfil", () => {
  beforeEach(() => responder());

  it("dice para qué sirven los datos de salud y que la fecha no se manda", async () => {
    montar(<Perfil />, { ruta: "/perfil/?vista=salud" });

    expect(await screen.findByText(/edad calculada/)).toBeVisible();
    expect(screen.getByText(/nunca tu fecha de nacimiento/)).toBeVisible();
  });

  it("el equipamiento sale del servidor, no de una lista propia", async () => {
    montar(<Perfil />, { ruta: "/perfil/?vista=entrenamiento" });

    expect(await screen.findByRole("checkbox", { name: "Barra" })).toBeChecked();
    expect(screen.getByRole("checkbox", { name: "Poleas" })).not.toBeChecked();
  });

  it("sin tocar nada no deja guardar", async () => {
    montar(<Perfil />);

    expect(await screen.findByRole("button", { name: "Guardar cambios" })).toBeDisabled();
  });

  it("manda solo lo que ha cambiado", async () => {
    let recibido: unknown = null;
    servidor.use(
      http.patch("/api/perfil/", async ({ request }) => {
        recibido = await request.json();
        return HttpResponse.json({ ...PERFIL, height_cm: 170 });
      }),
    );
    montar(<Perfil />, { ruta: "/perfil/?vista=salud" });

    const altura = await screen.findByLabelText("Altura (cm)");
    await userEvent.clear(altura);
    await userEvent.type(altura, "170");
    await userEvent.click(screen.getByRole("button", { name: "Guardar cambios" }));

    await waitFor(() => expect(recibido).toEqual({ height_cm: 170 }));
  });

  it("marcar equipamiento lo añade sin perder lo que ya estaba", async () => {
    let recibido: { available_equipment?: string[] } | null = null;
    servidor.use(
      http.patch("/api/perfil/", async ({ request }) => {
        recibido = (await request.json()) as { available_equipment?: string[] };
        return HttpResponse.json(PERFIL);
      }),
    );
    montar(<Perfil />, { ruta: "/perfil/?vista=entrenamiento" });

    await userEvent.click(await screen.findByRole("checkbox", { name: "Poleas" }));
    await userEvent.click(screen.getByRole("button", { name: "Guardar cambios" }));

    await waitFor(() =>
      expect(recibido?.available_equipment?.sort()).toEqual(["barbell", "cable"]),
    );
  });

  it("los errores del servidor salen en su campo", async () => {
    servidor.use(
      http.patch("/api/perfil/", () =>
        HttpResponse.json({ height_cm: ["Debe estar entre 100 y 250."] }, { status: 400 }),
      ),
    );
    montar(<Perfil />, { ruta: "/perfil/?vista=salud" });

    const altura = await screen.findByLabelText("Altura (cm)");
    await userEvent.clear(altura);
    await userEvent.type(altura, "5");
    await userEvent.click(screen.getByRole("button", { name: "Guardar cambios" }));

    expect(await screen.findByText("Debe estar entre 100 y 250.")).toBeVisible();
  });

  it("separa el perfil en Cuenta, Entrenamiento y Salud, y lo cambiado se conserva", async () => {
    let recibido: unknown = null;
    servidor.use(
      http.patch("/api/perfil/", async ({ request }) => {
        recibido = await request.json();
        return HttpResponse.json(PERFIL);
      }),
    );
    montar(<Perfil />);

    expect(await screen.findByRole("tab", { name: "Cuenta" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    await userEvent.click(screen.getByRole("tab", { name: "Salud" }));
    const altura = screen.getByLabelText("Altura (cm)");
    await userEvent.clear(altura);
    await userEvent.type(altura, "181");
    await userEvent.click(screen.getByRole("tab", { name: "Entrenamiento" }));
    await userEvent.click(screen.getByRole("checkbox", { name: "Poleas" }));

    await userEvent.click(screen.getByRole("button", { name: "Guardar cambios" }));

    await waitFor(() =>
      expect(recibido).toEqual({ height_cm: 181, available_equipment: ["barbell", "cable"] }),
    );
  });

  it("si el servidor rechaza un campo de otra pestaña, esa pestaña lo dice", async () => {
    servidor.use(
      http.patch("/api/perfil/", () =>
        HttpResponse.json({ height_cm: ["Debe estar entre 100 y 250."] }, { status: 400 }),
      ),
    );
    montar(<Perfil />, { ruta: "/perfil/?vista=salud" });
    const altura = await screen.findByLabelText("Altura (cm)");
    await userEvent.clear(altura);
    await userEvent.type(altura, "20");
    await userEvent.click(screen.getByRole("tab", { name: "Cuenta" }));

    await userEvent.click(screen.getByRole("button", { name: "Guardar cambios" }));

    expect(await screen.findByRole("tab", { name: /Salud.*con errores/ })).toBeVisible();
    expect(screen.getByRole("tab", { name: "Cuenta" })).toBeVisible();
  });

  it("el nombre de usuario no se puede cambiar, y se explica", async () => {
    montar(<Perfil />);

    await screen.findByText("Datos de la cuenta");
    expect(screen.queryByLabelText(/Nombre de usuario/)).not.toBeInTheDocument();
    expect(screen.getByText(/no se cambia/)).toBeVisible();
  });

  it("la descarga es un enlace, no un botón que monte un blob", async () => {
    montar(<Perfil />);

    const enlace = await screen.findByRole("link", { name: "Descargar mis datos" });
    expect(enlace).toHaveAttribute("href", "/api/cuenta/");
    expect(enlace).toHaveAttribute("download");
  });

  it("la edad se enseña calculada, junto a la fecha", async () => {
    montar(<Perfil />, { ruta: "/perfil/?vista=salud" });

    expect(await screen.findByText(/Ahora mismo: 28 años/)).toBeVisible();
  });
});

function montarBorrado() {
  servidor.use(
    http.get("/api/auth/session/", () =>
      HttpResponse.json({ id: 1, username: "ana", first_name: "Ana", is_staff: false }),
    ),
  );
  return montar(
    <Routes>
      <Route path="/perfil/eliminar" element={<EliminarCuenta />} />
      <Route path="/perfil" element={<p>Mi perfil</p>} />
    </Routes>,
    { ruta: "/perfil/eliminar" },
  );
}

describe("EliminarCuenta", () => {
  it("enumera lo que se borra en vez de resumirlo", async () => {
    montarBorrado();

    const lista = await screen.findByRole("list");
    expect(within(lista).getAllByRole("listitem").length).toBeGreaterThanOrEqual(5);
    expect(within(lista).getByText(/historial de entrenamientos/)).toBeVisible();
  });

  it("dice también lo que NO se borra", async () => {
    montarBorrado();

    expect(await screen.findByText(/se conserva únicamente el consumo/)).toBeVisible();
  });

  it("recuerda descargar los datos antes, con el enlace puesto", async () => {
    montarBorrado();

    const aviso = await screen.findByRole("alert");
    expect(within(aviso).getByRole("link", { name: "descárgalo antes" })).toHaveAttribute(
      "href",
      "/api/cuenta/",
    );
  });

  it("no deja borrar hasta escribir el nombre de usuario exacto", async () => {
    montarBorrado();

    const boton = await screen.findByRole("button", {
      name: "Eliminar mi cuenta definitivamente",
    });
    expect(boton).toBeDisabled();

    await userEvent.type(screen.getByLabelText(/Escribe «ana»/), "an");
    expect(boton).toBeDisabled();

    await userEvent.type(screen.getByLabelText(/Escribe «ana»/), "a");
    expect(boton).toBeEnabled();
  });

  it("al borrar sale de la SPA con una recarga entera", async () => {
    servidor.use(
      http.delete("/api/cuenta/", () =>
        HttpResponse.json({ rutinas: 3, entrenamientos: 12, registros_de_peso: 40 }),
      ),
    );
    montarBorrado();

    await userEvent.type(await screen.findByLabelText(/Escribe «ana»/), "ana");
    await userEvent.click(
      screen.getByRole("button", { name: "Eliminar mi cuenta definitivamente" }),
    );

    await waitFor(() => expect(salirDeLaSpa).toHaveBeenCalledWith("/entrar/"));
  });

  it("cancelar vuelve al perfil sin borrar nada", async () => {
    let llamado = false;
    servidor.use(
      http.delete("/api/cuenta/", () => {
        llamado = true;
        return HttpResponse.json({});
      }),
    );
    montarBorrado();

    await userEvent.click(await screen.findByRole("button", { name: "Cancelar" }));

    expect(await screen.findByText("Mi perfil")).toBeVisible();
    expect(llamado).toBe(false);
  });
});
