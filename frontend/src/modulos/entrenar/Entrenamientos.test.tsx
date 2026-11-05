import { screen, waitFor, within } from "@testing-library/react";
import { userEvent } from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { beforeEach, describe, expect, it } from "vitest";

import type { Paginado } from "@/api/tipos";
import { montar } from "@/test/montar";
import { servidor } from "@/test/servidor";

import type { SesionEnHistorial } from "./api";
import { Entrenamientos } from "./Entrenamientos";

const HISTORIAL: Paginado<SesionEnHistorial> = {
  count: 2,
  total_pages: 1,
  next: null,
  previous: null,
  results: [
    {
      id: 9, date: "2026-09-14", routine: 7, routine_name: "Empuje A",
      started_at: "2026-09-14T10:00:00Z", finished_at: null, notes: "", set_count: 4,
      duracion_minutos: null, tonelaje_kg: 0,
    },
    {
      id: 8, date: "2026-09-12", routine: null, routine_name: null,
      started_at: "2026-09-12T10:00:00Z", finished_at: "2026-09-12T11:00:00Z", notes: "",
      set_count: 12, duracion_minutos: 60, tonelaje_kg: 4200,
    },
  ],
};

function conHoy(hoyToca: Record<string, unknown>) {
  servidor.use(
    http.get("/api/inicio/", () =>
      HttpResponse.json({
        hoy: "2026-09-14",
        semana: [],
        hoy_toca: hoyToca,
        peso: { ultimo: null, cambio: null, objetivo: "", meta_kg: null, serie: null },
        racha: {
          semanas: 0, hechas_esta_semana: 0, planificadas_esta_semana: 0, total_sesiones: 0,
        },
        mapa_corporal: {},
      }),
    ),
  );
}

describe("Entrenamientos", () => {
  beforeEach(() => {
    servidor.use(http.get("/api/entrenamientos/", () => HttpResponse.json(HISTORIAL)));
    conHoy({ estado: "descanso", sesion: null, rutina: null });
  });

  it("arriba, lo que toca hoy y su botón: es la pestaña que se toca al llegar al gimnasio", async () => {
    conHoy({
      estado: "rutina",
      sesion: null,
      rutina: {
        id: 7,
        nombre: "Empuje A",
        ejercicios: [
          { id: 1, name: "Press de banca", image: null },
          { id: 2, name: "Fondos", image: null },
        ],
      },
    });

    montar(<Entrenamientos />);

    expect(await screen.findByRole("button", { name: "Empezar" })).toBeVisible();
    expect(screen.getByRole("img", { name: "Press de banca" })).toBeVisible();
  });

  it("cada sesión dice de qué rutina fue, no «Rutina»", async () => {
    montar(<Entrenamientos />);

    expect(await screen.findByRole("link", { name: /Empuje A/ })).toBeVisible();
  });

  it("una sesión sin terminar se retoma; una terminada se mira", async () => {
    montar(<Entrenamientos />);

    const enCurso = await screen.findByRole("link", { name: /Empuje A/ });
    expect(enCurso).toHaveAttribute("href", "/entrenamientos/9/");
    expect(within(enCurso).getAllByText("En curso")[0]).toBeVisible();

    const terminada = screen.getByRole("link", { name: /Entrenamiento libre/ });
    expect(terminada).toHaveAttribute("href", "/entrenamientos/8/cierre/");
  });

  it("sin entrenamientos manda al plan en vez de dejar la lista vacía", async () => {
    servidor.use(
      http.get("/api/entrenamientos/", () =>
        HttpResponse.json({ count: 0, next: null, previous: null, results: [] }),
      ),
    );

    montar(<Entrenamientos />);

    expect(await screen.findByText("Todavía no has entrenado")).toBeVisible();
    expect(screen.getByRole("link", { name: "Ir a mis rutinas" })).toHaveAttribute(
      "href",
      "/plan/",
    );
  });

  it("el entrenamiento libre se crea sin rutina y sin fecha", async () => {
    let recibido: unknown = null;
    servidor.use(
      http.post("/api/entrenamientos/", async ({ request }) => {
        recibido = await request.json();
        return HttpResponse.json({ id: 21 }, { status: 201 });
      }),
    );
    montar(<Entrenamientos />);

    await userEvent.click(await screen.findByRole("button", { name: "Entrenamiento libre" }));

    await waitFor(() => expect(recibido).toEqual({}));
  });

  it("sin más páginas no enseña la paginación", async () => {
    montar(<Entrenamientos />);

    await screen.findByRole("link", { name: /Empuje A/ });
    expect(screen.queryByRole("navigation", { name: "Paginación" })).not.toBeInTheDocument();
  });
});
