import { onlineManager } from "@tanstack/react-query";
import { act, screen, waitFor, within } from "@testing-library/react";
import { userEvent } from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { Route, Routes, useLocation } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { montar } from "@/test/montar";
import { servidor } from "@/test/servidor";

import type { Foco } from "../api";
import { Entrenar } from "./Entrenar";

const descansoFalso = { fin: null as number | null, total: 0 };

function descansoEnCurso() {
  if (descansoFalso.fin === null) return null;
  const restante = (descansoFalso.fin - Date.now()) / 1000;
  return restante > 0 ? { restante, total: descansoFalso.total } : null;
}

function arrancarDescanso(segundos: number | null) {
  descansoFalso.fin = segundos ? Date.now() + segundos * 1000 : null;
  descansoFalso.total = segundos ?? 0;
  return descansoEnCurso();
}

const DESCANSO_DE: Record<number, number> = { 101: 180, 102: 90 };

const FOCO: Foco = {
  sesion: {
    id: 5,
    fecha: "2026-09-14",
    notas: "",
    terminada: false,
    rutina: { id: 7, nombre: "Empuje A" },
  },
  indice: 1,
  total_ejercicios: 2,
  planificados: [
    { id: 11, nombre: "Press de banca", series: 3, hechas: 0 },
    { id: 12, nombre: "Fondos", series: 3, hechas: 0 },
  ],
  siguiente: 2,
  actual: {
    id: 11,
    ejercicio_id: 101,
    nombre: "Press de banca",
    slug: "press-banca",
    imagen: "/media/exercises/images/0001.jpg",
    animacion: "/media/exercises/animations/0001.gif",
    atribucion: "© Gym visual — https://gymvisual.com/",
    series: 3,
    reps_min: 6,
    reps_max: 8,
    descanso: 180,
    unilateral: false,
    completo: false,
  },
  filas: [
    { numero: 1, serie_id: null, activa: true, peso: "82.5", reps: 8, rpe: null },
    { numero: 2, serie_id: null, activa: false, peso: "82.5", reps: 8, rpe: null },
    { numero: 3, serie_id: null, activa: false, peso: "82.5", reps: 8, rpe: null },
  ],
  ultima_vez: { fecha: "2026-09-07", series: [["80", 8]], por_lado: false },
  mejor: "85",
  sugerencia: null,
  avance: { hechas: 0, objetivo: 6 },
  descanso_en_curso: null,
};

const FOCO_2: Foco = {
  ...FOCO,
  indice: 2,
  siguiente: 1,
  actual: { ...FOCO.actual!, id: 12, ejercicio_id: 102, nombre: "Fondos", descanso: 90 },
};

function conHechas(base: Foco, hechas: number, cambios: Partial<Foco> = {}): Foco {
  return {
    ...base,
    actual: { ...base.actual!, completo: hechas >= base.actual!.series },
    filas: base.filas.map((fila, i) => ({
      ...fila,
      serie_id: i < hechas ? 50 + i : null,
      activa: i === hechas,
    })),
    ...cambios,
  };
}

function servidorQueCuenta(hechas: number, cambiosAlCompletar: Partial<Foco> = {}) {
  let registradas = hechas;
  servidor.use(
    http.get("/api/entrenamientos/:id/foco/", ({ request }) => {
      if (new URL(request.url).searchParams.get("ejercicio") === "2") {
        return HttpResponse.json({ ...FOCO_2, descanso_en_curso: descansoEnCurso() });
      }
      const completo = registradas >= FOCO.actual!.series;
      return HttpResponse.json({
        ...conHechas(FOCO, registradas, completo ? cambiosAlCompletar : {}),
        descanso_en_curso: descansoEnCurso(),
      });
    }),
    http.post("/api/series/", () => {
      registradas += 1;
      const ultima = registradas === FOCO.actual!.series && cambiosAlCompletar.siguiente === null;
      const descanso = arrancarDescanso(ultima ? null : 180);
      return HttpResponse.json({ id: 99, descanso }, { status: 201 });
    }),
  );
}

function responderFoco(...focos: Foco[]) {
  servidor.use(
    http.get("/api/entrenamientos/:id/foco/", ({ request }) => {
      const indice = Number(new URL(request.url).searchParams.get("ejercicio") ?? 1);
      const foco = focos.find((f) => f.indice === indice) ?? focos[0]!;
      return HttpResponse.json({ ...foco, descanso_en_curso: descansoEnCurso() });
    }),
  );
}

function responderSeries() {
  servidor.use(
    http.post("/api/series/", async ({ request }) => {
      const { exercise } = (await request.json()) as { exercise: number };
      return HttpResponse.json(
        { id: 1, descanso: arrancarDescanso(DESCANSO_DE[exercise] ?? null) },
        { status: 201 },
      );
    }),
  );
}

function Ubicacion() {
  const { pathname, search } = useLocation();
  return <output aria-label="Dirección">{pathname + search}</output>;
}

function montarEntrenar(ruta = "/entrenamientos/5/") {
  return montar(
    <>
      <Routes>
        <Route path="/entrenamientos/:id" element={<Entrenar />} />
        <Route path="/entrenamientos/:id/cierre" element={<p>Pantalla de cierre</p>} />
      </Routes>
      <Ubicacion />
    </>,
    { ruta },
  );
}

function adelantarElReloj(segundos: number) {
  const real = Date.now.bind(Date);
  vi.spyOn(Date, "now").mockImplementation(() => real() + segundos * 1000);
}

beforeEach(() => {
  arrancarDescanso(null);
  responderFoco(FOCO, FOCO_2);
  responderSeries();
});
afterEach(() => vi.restoreAllMocks());

describe("Entrenar", () => {
  it("arranca en el ejercicio que dice la URL, no siempre en el primero", async () => {
    montarEntrenar("/entrenamientos/5/?ejercicio=2");

    expect(await screen.findByRole("heading", { name: "Fondos" })).toBeVisible();
  });

  it("pasar al siguiente cambia la URL en vez de guardarlo en memoria", async () => {
    montarEntrenar();
    await screen.findByRole("heading", { name: "Press de banca" });

    await userEvent.click(screen.getByRole("button", { name: /Siguiente/ }));

    expect(await screen.findByRole("heading", { name: "Fondos" })).toBeVisible();
  });

  it("la fila activa llega rellena con lo que propone el servidor", async () => {
    montarEntrenar();

    expect(await screen.findByLabelText("kg")).toHaveValue(82.5);
    expect(screen.getByLabelText("Reps")).toHaveValue(8);
  });

  it("«la última vez» de una serie sin kilos dice las reps, no «×10»", async () => {
    responderFoco({
      ...FOCO,
      ultima_vez: { fecha: "2026-09-07", series: [["", 10], ["5", 8]], por_lado: false },
    });

    montarEntrenar();

    expect(await screen.findByText("10 reps · 5×8")).toBeVisible();
  });

  it("no recalcula el avance: pinta el que viene", async () => {
    responderFoco({ ...FOCO, avance: { hechas: 2, objetivo: 6 } });

    montarEntrenar();

    expect(await screen.findByText(/2 \/ 6 series/)).toBeVisible();
  });

  it("registrar manda la serie sin número: lo pone el servidor", async () => {
    let recibido: Record<string, unknown> | null = null;
    servidor.use(
      http.post("/api/series/", async ({ request }) => {
        recibido = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json({ id: 1 }, { status: 201 });
      }),
    );
    montarEntrenar();
    await screen.findByLabelText("kg");

    await userEvent.click(screen.getByRole("button", { name: "Registrar serie" }));

    await waitFor(() => expect(recibido).not.toBeNull());
    expect(recibido).toEqual({ session: 5, exercise: 101, weight_kg: "82.5", reps: 8 });
    expect(recibido).not.toHaveProperty("set_number");
  });

  it("si registrar falla, lo dice: la serie no puede parecer guardada", async () => {
    servidor.use(http.post("/api/series/", () => HttpResponse.error()));
    montarEntrenar();
    await screen.findByLabelText("kg");

    await userEvent.click(screen.getByRole("button", { name: "Registrar serie" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("No se pudo registrar la serie");
    expect(screen.getByRole("button", { name: "Registrar serie" })).toBeEnabled();
  });

  it("sin red no deja registrar: una serie no se guarda para enviarla luego", async () => {
    montarEntrenar();
    await screen.findByLabelText("kg");

    act(() => onlineManager.setOnline(false));

    expect(screen.getByRole("button", { name: "Registrar serie" })).toBeDisabled();
    expect(screen.getByText(/para registrar la serie hace falta red/)).toBeVisible();
    act(() => onlineManager.setOnline(true));
    expect(screen.getByRole("button", { name: "Registrar serie" })).toBeEnabled();
  });

  it("al registrar arranca el descanso del ejercicio en pantalla", async () => {
    montarEntrenar();
    await screen.findByLabelText("kg");

    await userEvent.click(screen.getByRole("button", { name: "Registrar serie" }));

    expect(await screen.findByRole("timer")).toHaveTextContent("3:00");
  });

  it("corregir una serie manda un PATCH con kilos y reps, y NO arranca el descanso", async () => {
    responderFoco(conHechas(FOCO, 1));
    let recibido: Record<string, unknown> | null = null;
    let url = "";
    servidor.use(
      http.patch("/api/series/:id/", async ({ request }) => {
        url = new URL(request.url).pathname;
        recibido = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json({ id: 50 });
      }),
    );
    montarEntrenar();

    await userEvent.click(await screen.findByRole("button", { name: /Corregir la serie 1/ }));
    const panel = screen.getByRole("dialog", { name: "Serie 1" });
    const kg = within(panel).getByLabelText("kg");
    await userEvent.clear(kg);
    await userEvent.type(kg, "85");
    await userEvent.click(within(panel).getByRole("button", { name: "Guardar" }));

    await waitFor(() => expect(recibido).not.toBeNull());
    expect(url).toBe("/api/series/50/");
    expect(recibido).toEqual({ weight_kg: "85", reps: 8 });
    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
    expect(screen.queryByRole("timer")).not.toBeInTheDocument();
  });

  it("corregir no reinicia un descanso que ya estaba corriendo", async () => {
    servidorQueCuenta(0);
    servidor.use(http.patch("/api/series/:id/", () => HttpResponse.json({ id: 50 })));
    montarEntrenar();
    await screen.findByLabelText("kg");
    await userEvent.click(screen.getByRole("button", { name: "Registrar serie" }));
    await screen.findByRole("timer");
    adelantarElReloj(10);
    await waitFor(() => expect(screen.getByRole("timer")).toHaveTextContent("2:50"));

    await userEvent.click(await screen.findByRole("button", { name: /Corregir la serie 1/ }));
    await userEvent.click(
      within(screen.getByRole("dialog")).getByRole("button", { name: "Guardar" }),
    );

    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
    expect(screen.getByRole("timer")).toHaveTextContent(/^2:[45]\d$/);
  });

  it("borrar una serie se hace desde el mismo panel y NO arranca el descanso", async () => {
    responderFoco(conHechas(FOCO, 1));
    servidor.use(http.delete("/api/series/:id/", () => new HttpResponse(null, { status: 204 })));
    montarEntrenar();

    await userEvent.click(await screen.findByRole("button", { name: /Corregir la serie 1/ }));
    await userEvent.click(
      within(screen.getByRole("dialog")).getByRole("button", { name: "Borrar la serie 1" }),
    );

    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
    expect(screen.queryByRole("timer")).not.toBeInTheDocument();
  });

  it("cambiar de ejercicio NO corta el descanso", async () => {
    montarEntrenar();
    await screen.findByLabelText("kg");
    await userEvent.click(screen.getByRole("button", { name: "Registrar serie" }));
    await screen.findByRole("timer");

    await userEvent.click(screen.getByRole("button", { name: /Siguiente/ }));

    expect(await screen.findByRole("heading", { name: "Fondos" })).toBeVisible();
    expect(screen.getByRole("timer")).toBeVisible();
  });

  it("al registrar la última serie pasa solo al siguiente, con el descanso corriendo", async () => {
    servidorQueCuenta(2);
    montarEntrenar();
    await screen.findByRole("heading", { name: "Press de banca" });

    await userEvent.click(screen.getByRole("button", { name: "Registrar serie" }));

    expect(await screen.findByRole("heading", { name: "Fondos" })).toBeVisible();
    expect(screen.getByRole("timer")).toHaveTextContent("3:00");
  });

  it("una serie que no completa el ejercicio no mueve la pantalla", async () => {
    servidorQueCuenta(0);
    montarEntrenar();
    await screen.findByLabelText("kg");

    await userEvent.click(screen.getByRole("button", { name: "Registrar serie" }));

    await screen.findByRole("timer");
    expect(screen.getByRole("heading", { name: "Press de banca" })).toBeVisible();
  });

  it("una serie de más en un ejercicio ya completo no mueve la pantalla", async () => {
    servidorQueCuenta(3);
    montarEntrenar();
    await screen.findByLabelText("kg");

    await userEvent.click(screen.getByRole("button", { name: "Registrar serie" }));

    await screen.findByRole("timer");
    expect(screen.getByRole("heading", { name: "Press de banca" })).toBeVisible();
  });

  it("con la última serie de todo no hay descanso y se ofrece terminar", async () => {
    servidorQueCuenta(2, { siguiente: null });
    montarEntrenar();
    await screen.findByLabelText("kg");

    await userEvent.click(screen.getByRole("button", { name: "Registrar serie" }));

    expect(
      await screen.findByRole("button", { name: "Terminar entrenamiento" }),
    ).toBeVisible();
    await waitFor(() => expect(screen.queryByRole("timer")).not.toBeInTheDocument());
    expect(screen.getByRole("heading", { name: "Press de banca" })).toBeVisible();
  });

  it("en el último ejercicio el botón es terminar, y lleva al cierre", async () => {
    servidor.use(
      http.post("/api/entrenamientos/:id/finalizar/", () => HttpResponse.json({ series: 0 })),
    );
    montarEntrenar("/entrenamientos/5/?ejercicio=2");

    await userEvent.click(
      await screen.findByRole("button", { name: "Terminar entrenamiento" }),
    );

    expect(await screen.findByText("Pantalla de cierre")).toBeVisible();
  });

  it("sin ejercicio en la URL abre el que dice el servidor y lo deja en la URL", async () => {
    const pedidos: (string | null)[] = [];
    servidor.use(
      http.get("/api/entrenamientos/:id/foco/", ({ request }) => {
        const pedido = new URL(request.url).searchParams.get("ejercicio");
        pedidos.push(pedido);
        return HttpResponse.json(pedido === null || pedido === "2" ? FOCO_2 : FOCO);
      }),
    );

    montarEntrenar("/entrenamientos/5/");

    expect(await screen.findByRole("heading", { name: "Fondos" })).toBeVisible();
    await waitFor(() =>
      expect(screen.getByRole("status", { name: "Dirección" })).toHaveTextContent(
        "/entrenamientos/5/?ejercicio=2",
      ),
    );
    expect(pedidos[0]).toBeNull();
  });

  it("al volver a la pantalla, el descanso sigue donde iba", async () => {
    arrancarDescanso(180);
    adelantarElReloj(105);

    montarEntrenar("/entrenamientos/5/?ejercicio=1");

    expect(await screen.findByRole("timer")).toHaveTextContent("1:15");
  });

  it("«Saltar» lo quita y se lo dice al servidor", async () => {
    let recibido: unknown = null;
    servidor.use(
      http.post("/api/entrenamientos/:id/descanso/", async ({ request }) => {
        recibido = await request.json();
        arrancarDescanso(null);
        return HttpResponse.json({ descanso: null });
      }),
    );
    montarEntrenar();
    await screen.findByLabelText("kg");
    await userEvent.click(screen.getByRole("button", { name: "Registrar serie" }));
    await screen.findByRole("timer");

    await userEvent.click(screen.getByRole("button", { name: "Saltar" }));

    expect(screen.queryByRole("timer")).not.toBeInTheDocument();
    await waitFor(() => expect(recibido).toEqual({ accion: "saltar" }));
  });

  it("«+30 s» suma en el acto y lo guarda el servidor", async () => {
    let recibido: unknown = null;
    servidor.use(
      http.post("/api/entrenamientos/:id/descanso/", async ({ request }) => {
        recibido = await request.json();
        descansoFalso.fin! += 30_000;
        descansoFalso.total += 30;
        return HttpResponse.json({ descanso: descansoEnCurso() });
      }),
    );
    montarEntrenar();
    await screen.findByLabelText("kg");
    await userEvent.click(screen.getByRole("button", { name: "Registrar serie" }));
    await screen.findByRole("timer");

    await userEvent.click(screen.getByRole("button", { name: "+30 s" }));

    expect(screen.getByRole("timer")).toHaveTextContent(/^3:[23]\d$/);
    await waitFor(() => expect(recibido).toEqual({ accion: "alargar" }));
  });

  it("enseña la animación, no la foto fija, y su atribución", async () => {
    montarEntrenar();
    await screen.findByRole("heading", { name: "Press de banca" });

    const imagen = document.querySelector(".ex-frame img");
    expect(imagen).toHaveAttribute("src", "/media/exercises/animations/0001.gif");
    expect(document.querySelector(".ex-frame source")).toHaveAttribute(
      "media",
      "(prefers-reduced-motion: reduce)",
    );
    expect(screen.getByText(/gymvisual\.com/)).toBeVisible();
  });

  it("la animación se puede pausar, y pausada se ve la foto", async () => {
    montarEntrenar();
    await screen.findByRole("heading", { name: "Press de banca" });

    await userEvent.click(screen.getByRole("button", { name: "Pausar la animación" }));

    expect(document.querySelector(".ex-frame img")).toHaveAttribute(
      "src",
      "/media/exercises/images/0001.jpg",
    );
    expect(screen.getByRole("button", { name: "Reproducir la animación" })).toBeVisible();
  });

  it("«Cómo se hace» se abre aquí mismo: no saca de la pantalla ni corta el descanso", async () => {
    servidor.use(
      http.get("/api/ejercicios/:slug/", () =>
        HttpResponse.json({
          id: 101, external_id: "0001", name: "Press de banca", slug: "press-banca",
          body_part: "chest", body_part_label: "Pecho", equipment: "barbell",
          equipment_label: "Barra", target_muscle: null, secondary_muscles: [],
          is_cardio: false, is_bodyweight: false,
          image: "/media/exercises/images/0001.jpg",
          animation: "/media/exercises/animations/0001.gif",
          attribution: "© Gym visual — https://gymvisual.com/",
          steps: ["Baja la barra al pecho.", "Empuja hasta estirar."],
        }),
      ),
    );
    montarEntrenar("/entrenamientos/5/?ejercicio=1");
    await screen.findByLabelText("kg");
    await userEvent.click(screen.getByRole("button", { name: "Registrar serie" }));
    await screen.findByRole("timer");

    await userEvent.click(screen.getByRole("button", { name: "Cómo se hace" }));

    const hoja = screen.getByRole("dialog", { name: "Cómo se hace" });
    expect(await within(hoja).findByText("Baja la barra al pecho.")).toBeVisible();
    expect(screen.getByRole("status", { name: "Dirección" })).toHaveTextContent(
      "/entrenamientos/5/?ejercicio=1",
    );
    expect(screen.getByRole("timer")).toBeInTheDocument();
  });

  it("los ejercicios de la rutina están a un toque, con sus series hechas", async () => {
    montarEntrenar();
    await screen.findByRole("heading", { name: "Press de banca" });

    const ejercicios = screen.getByRole("navigation", { name: "Ejercicios de la rutina" });
    expect(within(ejercicios).getByRole("button", { name: /Press de banca/ })).toHaveAttribute(
      "aria-current",
      "step",
    );

    await userEvent.click(within(ejercicios).getByRole("button", { name: /Fondos/ }));

    expect(await screen.findByRole("heading", { name: "Fondos" })).toBeVisible();
  });

  it("no ofrece «anterior» en el primero", async () => {
    montarEntrenar();

    expect(await screen.findByRole("button", { name: /Anterior/ })).toBeDisabled();
  });

  it("no deja salir sin querer: la única salida es la ✕", async () => {
    montarEntrenar();

    const salir = await screen.findByRole("link", { name: "Salir del entrenamiento" });
    expect(salir).toHaveAttribute("href", "/entrenamientos/");
  });

  it("una sesión libre no se queda en blanco", async () => {
    responderFoco({
      ...FOCO,
      sesion: { ...FOCO.sesion, rutina: null },
      total_ejercicios: 0,
      planificados: [],
      actual: null,
      filas: [],
      avance: { hechas: 0, objetivo: 0 },
    });

    montarEntrenar();

    expect(await screen.findByText("Esta sesión no sigue una rutina")).toBeVisible();
    expect(screen.getByRole("button", { name: "Terminar" })).toBeVisible();
  });
});
