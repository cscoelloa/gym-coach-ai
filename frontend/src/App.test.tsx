import { screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";

import { montar } from "@/test/montar";
import { servidor } from "@/test/servidor";

import { App } from "./App";

const ANA = { id: 1, username: "ana", first_name: "Ana", is_staff: false };

function conSesion() {
  servidor.use(http.get("/api/auth/session/", () => HttpResponse.json(ANA)));
}

function sinSesion() {
  servidor.use(
    http.get("/api/auth/session/", () =>
      HttpResponse.json({ detail: "No hay sesión iniciada." }, { status: 401 }),
    ),
  );
}

describe("App", () => {
  it("sin red no manda al acceso: dice que no hay conexión y deja reintentar", async () => {
    servidor.use(http.get("/api/auth/session/", () => HttpResponse.error()));

    montar(<App />, { ruta: "/progreso/" });

    expect(await screen.findByRole("heading", { name: "Sin conexión", level: 1 })).toBeVisible();
    expect(screen.getByRole("button", { name: "Reintentar" })).toBeVisible();
    expect(screen.queryByLabelText("Contraseña")).not.toBeInTheDocument();
  });

  it("si responde el servidor con un error, no dice «sin conexión»: no sería verdad", async () => {
    servidor.use(
      http.get("/api/auth/session/", () => HttpResponse.json({ detail: "x" }, { status: 503 })),
    );

    montar(<App />, { ruta: "/progreso/" });

    expect(
      await screen.findByRole("heading", { name: "No se pudo conectar", level: 1 }),
    ).toBeVisible();
  });

  it("sirve la guía de estilos en la URL que tenía en Django", async () => {
    conSesion();

    montar(<App />, { ruta: "/estilos/" });

    expect(
      await screen.findByRole("heading", { name: "Guía de estilos", level: 1 }),
    ).toBeVisible();
  });

  it("la casa también sin la barra final", async () => {
    conSesion();

    montar(<App />, { ruta: "/estilos" });

    expect(
      await screen.findByRole("heading", { name: "Guía de estilos", level: 1 }),
    ).toBeVisible();
  });

  it("una pantalla con sesión caducada manda al acceso sin perder el destino", async () => {
    sinSesion();

    montar(<App />, { ruta: "/estilos/" });

    expect(await screen.findByRole("heading", { name: "Entrar", level: 1 })).toBeVisible();
  });

  it("las pantallas de acceso no piden sesión", async () => {
    montar(<App />, { ruta: "/entrar/" });

    expect(await screen.findByRole("heading", { name: "Entrar", level: 1 })).toBeVisible();
  });
});
