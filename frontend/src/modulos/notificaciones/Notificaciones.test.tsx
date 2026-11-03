import { screen } from "@testing-library/react";
import { userEvent } from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";

import type { Notificacion } from "@/api/notificaciones";
import { montar } from "@/test/montar";
import { servidor } from "@/test/servidor";

import { Notificaciones } from "./Notificaciones";

const BASE: Notificacion = {
  id: 1,
  kind: "progress_ready",
  kind_label: "Análisis de progreso listo",
  severity: "info",
  title: "Tu análisis semanal",
  body: "Has subido el volumen un 6 %.",
  payload: {},
  is_read: false,
  emailed_at: null,
  created_at: "2026-09-16T08:00:00Z",
};

function conAvisos(avisos: Notificacion[]) {
  servidor.use(
    http.get("/api/notificaciones/", ({ request }) => {
      const soloSinLeer = new URL(request.url).searchParams.get("unread") === "true";
      const lista = soloSinLeer ? avisos.filter((aviso) => !aviso.is_read) : avisos;
      return HttpResponse.json({ count: lista.length, next: null, previous: null, results: lista });
    }),
  );
}

describe("Notificaciones", () => {
  it("el cuerpo que escribe la IA se pinta como texto, nunca como HTML", async () => {
    conAvisos([{ ...BASE, body: "<script>alert('xss')</script>" }]);

    const { container } = montar(<Notificaciones />);

    expect(await screen.findByText(/<script>alert\('xss'\)<\/script>/)).toBeVisible();
    expect(container.querySelector("script")).toBeNull();
  });

  it("marca un aviso como leído", async () => {
    conAvisos([BASE]);
    let recibido: unknown = null;
    servidor.use(
      http.patch("/api/notificaciones/1/", async ({ request }) => {
        recibido = await request.json();
        return HttpResponse.json({ ...BASE, is_read: true });
      }),
    );
    montar(<Notificaciones />);

    await userEvent.click(await screen.findByRole("button", { name: "Marcar leída" }));

    expect(recibido).toEqual({ is_read: true });
  });

  it("un aviso ya leído no ofrece volver a marcarlo", async () => {
    conAvisos([{ ...BASE, is_read: true }]);

    montar(<Notificaciones />);

    await screen.findByText("Tu análisis semanal");
    expect(screen.queryByRole("button", { name: "Marcar leída" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /todas/ })).not.toBeInTheDocument();
  });

  it("los avisos sin leer se distinguen sin depender del color", async () => {
    conAvisos([BASE]);

    montar(<Notificaciones />);

    expect(await screen.findByText("Sin leer:")).toBeInTheDocument();
  });

  it("«Sin leer» enseña solo esos, y dice cuántos son", async () => {
    conAvisos([
      { ...BASE, id: 1, title: "Sin leer todavía" },
      { ...BASE, id: 2, title: "Ya leído", is_read: true },
    ]);
    montar(<Notificaciones />);

    await userEvent.click(await screen.findByRole("tab", { name: "Sin leer 1" }));

    expect(await screen.findByText("Sin leer todavía")).toBeVisible();
    expect(screen.queryByText("Ya leído")).not.toBeInTheDocument();
  });

  it("sin nada pendiente, «Sin leer» dice que se está al día", async () => {
    conAvisos([{ ...BASE, is_read: true }]);
    montar(<Notificaciones />, { ruta: "/notificaciones/?vista=sin-leer" });

    expect(await screen.findByText("Estás al día")).toBeVisible();
  });

  it("la bandeja vacía dice qué aparecerá aquí", async () => {
    conAvisos([]);

    montar(<Notificaciones />);

    expect(await screen.findByText("No tienes notificaciones")).toBeVisible();
    expect(screen.getByText(/estancamiento/)).toBeVisible();
  });
});
