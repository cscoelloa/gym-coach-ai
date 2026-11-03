import { act, screen, waitFor, within } from "@testing-library/react";
import { userEvent } from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { montar } from "@/test/montar";
import { servidor } from "@/test/servidor";

import type { RegistroDePeso, ResumenDePeso } from "./api";
import { Peso } from "./Peso";

function hoyEnIso(): string {
  const ahora = new Date();
  const mes = String(ahora.getMonth() + 1).padStart(2, "0");
  const dia = String(ahora.getDate()).padStart(2, "0");
  return `${ahora.getFullYear()}-${mes}-${dia}`;
}

const SIN_DATOS: ResumenDePeso = {
  ultimo: null,
  cambio: null,
  objetivo: "Mantener",
  meta_kg: null,
  serie: null,
};

function conRegistros(filas: RegistroDePeso[], resumen: Partial<ResumenDePeso> = {}) {
  servidor.use(
    http.get("/api/peso/resumen/", () => HttpResponse.json({ ...SIN_DATOS, ...resumen })),
    http.get("/api/peso/", () =>
      HttpResponse.json({ count: filas.length, next: null, previous: null, results: filas }),
    ),
  );
}

function registro(extra: Partial<RegistroDePeso> = {}): RegistroDePeso {
  return {
    id: 1,
    date: hoyEnIso(),
    weight_kg: "80.00",
    body_fat_pct: null,
    notes: "",
    created_at: "2026-09-16T08:00:00Z",
    ...extra,
  };
}

beforeEach(() => conRegistros([]));

describe("Peso", () => {
  it("el primer pesaje del día se crea", async () => {
    let metodo = "";
    servidor.use(
      http.post("/api/peso/", async ({ request }) => {
        metodo = request.method;
        return HttpResponse.json(registro(), { status: 201 });
      }),
    );
    montar(<Peso />);

    await userEvent.type(await screen.findByLabelText("Peso (kg)"), "80");
    await userEvent.click(screen.getByRole("button", { name: "Guardar" }));

    await waitFor(() => expect(metodo).toBe("POST"));
  });

  it("la confirmación sale y se va sola", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    try {
      servidor.use(http.post("/api/peso/", () => HttpResponse.json(registro(), { status: 201 })));
      montar(<Peso />);
      const usuario = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });

      await usuario.type(await screen.findByLabelText("Peso (kg)"), "80");
      await usuario.click(screen.getByRole("button", { name: "Guardar" }));
      expect(await screen.findByText("Peso registrado.")).toBeVisible();

      act(() => vi.advanceTimersByTime(4500));
      expect(screen.queryByText("Peso registrado.")).not.toBeInTheDocument();
    } finally {
      vi.useRealTimers();
    }
  });

  it("volver a pesarse el mismo día actualiza en vez de dar error", async () => {
    conRegistros([registro({ id: 9 })]);
    let camino = "";
    let metodo = "";
    servidor.use(
      http.patch("/api/peso/:id/", ({ request, params }) => {
        metodo = request.method;
        camino = String(params["id"]);
        return HttpResponse.json(registro({ id: 9, weight_kg: "81.00" }));
      }),
    );
    montar(<Peso />);

    await userEvent.type(await screen.findByLabelText("Peso (kg)"), "81");
    await userEvent.click(screen.getByRole("button", { name: "Guardar" }));

    await waitFor(() => expect(metodo).toBe("PATCH"));
    expect(camino).toBe("9");
  });

  it("y lo avisa antes de pulsar", async () => {
    conRegistros([registro({ id: 9 })]);

    montar(<Peso />);

    expect(await screen.findByText(/Ya tienes un registro de ese día/)).toBeVisible();
  });

  it("los errores del servidor se pintan en su campo", async () => {
    servidor.use(
      http.post("/api/peso/", () =>
        HttpResponse.json(
          { weight_kg: ["Asegúrese de que este valor es mayor o igual a 20."] },
          { status: 400 },
        ),
      ),
    );
    montar(<Peso />);

    await userEvent.type(await screen.findByLabelText("Peso (kg)"), "7");
    await userEvent.click(screen.getByRole("button", { name: "Guardar" }));

    const campo = screen.getByLabelText("Peso (kg)");
    await waitFor(() => expect(campo).toHaveAttribute("aria-invalid", "true"));
    expect(campo).toHaveAccessibleDescription(/mayor o igual a 20/);
  });

  it("sin registros no dibuja una gráfica vacía", async () => {
    montar(<Peso />);

    expect(await screen.findByText(/Registra tu peso unos días/)).toBeVisible();
    await userEvent.click(screen.getByRole("tab", { name: "Historial" }));
    expect(screen.getByText("Sin registros")).toBeVisible();
  });

  it("el historial va en su pestaña y se pagina", async () => {
    const paginas: (string | null)[] = [];
    servidor.use(
      http.get("/api/peso/", ({ request }) => {
        const pagina = new URL(request.url).searchParams.get("page");
        paginas.push(pagina);
        return HttpResponse.json({
          count: 30,
          next: pagina ? null : "/api/peso/?page=2",
          previous: pagina ? "/api/peso/" : null,
          results: [registro({ id: pagina ? 2 : 1, weight_kg: pagina ? "79.00" : "80.00" })],
        });
      }),
    );
    montar(<Peso />);

    await userEvent.click(await screen.findByRole("tab", { name: /Historial/ }));
    expect(await screen.findByText("80.00 kg")).toBeVisible();

    await userEvent.click(
      within(screen.getByRole("navigation", { name: "Paginación" })).getByRole("button", {
        name: "Siguiente",
      }),
    );

    expect(await screen.findByText("79.00 kg")).toBeVisible();
    expect(paginas).toContain("2");
  });

  it("el historial enseña un guion donde no hay dato, no un cero", async () => {
    conRegistros([registro({ body_fat_pct: null, notes: "" })]);

    montar(<Peso />, { ruta: "/peso/?vista=historial" });

    await screen.findByText("80.00 kg");
    expect(screen.getAllByText("—")).toHaveLength(2);
  });

  it("borrar pregunta antes, y cancelar no borra nada", async () => {
    let borrados = 0;
    servidor.use(
      http.delete("/api/peso/:id/", () => {
        borrados += 1;
        return new HttpResponse(null, { status: 204 });
      }),
    );
    conRegistros([registro()]);
    montar(<Peso />, { ruta: "/peso/?vista=historial" });

    await userEvent.click(await screen.findByRole("button", { name: /^Borrar el registro/ }));
    const dialogo = screen.getByRole("dialog", { name: "Borrar el registro" });
    await userEvent.click(within(dialogo).getByRole("button", { name: "Cancelar" }));
    expect(borrados).toBe(0);

    await userEvent.click(screen.getByRole("button", { name: /^Borrar el registro/ }));
    await userEvent.click(screen.getByRole("button", { name: "Sí, borrar" }));
    await waitFor(() => expect(borrados).toBe(1));
  });
});
