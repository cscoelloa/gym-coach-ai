import { screen, waitFor, within } from "@testing-library/react";
import { userEvent } from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { Route, Routes } from "react-router";
import { beforeEach, describe, expect, it } from "vitest";

import { montar } from "@/test/montar";
import { servidor } from "@/test/servidor";

import { AnalisisDeProgreso } from "./AnalisisDeProgreso";
import type { EstadoDelAnalisis, Propuesta } from "./api";
import { GenerarRutina } from "./GenerarRutina";
import { PropuestaDeRutina } from "./PropuestaDeRutina";

const PROPUESTA: Propuesta = {
  generacion: {
    id: 7,
    fecha: "2026-09-20T10:00:00Z",
    proveedor: "Anthropic (Claude)",
    modelo: "claude-opus-5",
    latencia_ms: 2000,
    tokens_entrada: 800,
    tokens_salida: 300,
  },
  nombre: "Empuje/Tirón",
  descripcion: "Para ganar masa en cuatro días.",
  motivo: "Dos empujes por semana con volumen moderado.",
  rutinas: [
    {
      nombre: "Empuje",
      ejercicios: [
        {
          external_id: "0001", nombre: "Press de banca", slug: "press-banca", imagen: null,
          en_catalogo: true, series: 4, reps_min: 6, reps_max: 8, descanso: 150,
        },
      ],
    },
  ],
  semana: [
    { weekday: 0, etiqueta: "Lunes", rutina: "Empuje" },
    { weekday: 1, etiqueta: "Martes", rutina: null },
    { weekday: 2, etiqueta: "Miércoles", rutina: null },
    { weekday: 3, etiqueta: "Jueves", rutina: "Empuje" },
    { weekday: 4, etiqueta: "Viernes", rutina: null },
    { weekday: 5, etiqueta: "Sábado", rutina: null },
    { weekday: 6, etiqueta: "Domingo", rutina: null },
  ],
  ya_aplicada: false,
};

const MUSCULOS = [
  { valor: "pectorals", etiqueta: "Pectorales", n: 158 },
  { valor: "triceps", etiqueta: "Tríceps", n: 141 },
  { valor: "lats", etiqueta: "Dorsales", n: 81 },
  { valor: "quads", etiqueta: "Cuádriceps", n: 44 },
];

const FORMULARIO = {
  restantes: 3,
  dias_por_defecto: 4,
  tiene_equipamiento: true,
  musculos: MUSCULOS,
  dias_sugeridos: [0, 1, 3, 4],
  ejercicios: { min: 3, max: 10, por_defecto: 6 },
  max_musculos_por_dia: 5,
  objetivos: [
    { valor: "hypertrophy", etiqueta: "Hipertrofia", resumen: "3-4 series · 6-20 reps · 120 s" },
    { valor: "strength", etiqueta: "Fuerza", resumen: "3-6 series · 3-8 reps · 180 s" },
  ],
  objetivo_por_defecto: "hypertrophy",
};

function responderFormulario(extra: Partial<typeof FORMULARIO> = {}) {
  servidor.use(
    http.get("/api/ia/generar/", () => HttpResponse.json({ ...FORMULARIO, ...extra })),
  );
}

function fallo(codigo: string, detail: string, estado: number) {
  return HttpResponse.json({ detail, codigo }, { status: estado });
}

function montarGenerar() {
  return montar(
    <Routes>
      <Route path="/ia/generar" element={<GenerarRutina />} />
      <Route path="/ia/propuestas/:id" element={<p>Propuesta </p>} />
    </Routes>,
    { ruta: "/ia/generar" },
  );
}

async function rellenarDia(
  dia: string,
  musculos: { etiqueta: string; n: number }[],
  { enfasis, ejercicios }: { enfasis?: string; ejercicios?: number } = {},
) {
  await userEvent.click(await screen.findByRole("button", { name: new RegExp(`^${dia}`) }));
  const panel = screen.getByRole("dialog", { name: dia });

  for (const musculo of musculos) {
    await userEvent.click(
      within(panel).getByRole("button", { name: `${musculo.etiqueta} ${musculo.n}` }),
    );
  }
  if (enfasis) await userEvent.click(within(panel).getByRole("button", { name: enfasis }));
  if (ejercicios !== undefined) {
    const campo = within(panel).getByLabelText(/Ejercicios ese día/);
    await userEvent.clear(campo);
    await userEvent.type(campo, String(ejercicios));
  }

  await userEvent.click(within(panel).getByRole("button", { name: "Guardar el día" }));
}

describe("GenerarRutina", () => {
  beforeEach(() => responderFormulario());

  it("arranca con la semana entera en descanso y dice cuántas generaciones quedan", async () => {
    montarGenerar();

    expect(await screen.findByRole("button", { name: /^Lunes/ })).toHaveTextContent("Descanso");
    expect(screen.getByRole("button", { name: /^Domingo/ })).toHaveTextContent("Descanso");
    expect(screen.getByText("3", { selector: ".num" })).toBeVisible();
  });

  it("arranca en hipertrofia y dice lo que implica", async () => {
    montarGenerar();

    const objetivos = await screen.findByRole("group", { name: "Objetivo del entrenamiento" });
    expect(within(objetivos).getByRole("button", { name: "Hipertrofia" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect(screen.getByText("3-4 series · 6-20 reps · 120 s")).toBeVisible();
  });

  it("cambiar de objetivo cambia lo que se manda", async () => {
    let recibido: { training_goal?: string } | null = null;
    servidor.use(
      http.post("/api/ia/generar/", async ({ request }) => {
        recibido = (await request.json()) as { training_goal?: string };
        return HttpResponse.json(PROPUESTA, { status: 201 });
      }),
    );
    montarGenerar();

    await rellenarDia("Lunes", [MUSCULOS[0]!]);
    await userEvent.click(screen.getByRole("button", { name: "Fuerza" }));
    expect(screen.getByText("3-6 series · 3-8 reps · 180 s")).toBeVisible();
    await userEvent.click(screen.getByRole("button", { name: "Generar propuesta" }));

    await waitFor(() => expect(recibido?.training_goal).toBe("strength"));
  });

  it("sin ningún día marcado no se puede generar", async () => {
    montarGenerar();

    expect(await screen.findByRole("button", { name: "Generar propuesta" })).toBeDisabled();
  });

  it("un día guardado enseña sus músculos y cuántos ejercicios lleva", async () => {
    montarGenerar();

    await rellenarDia("Lunes", [MUSCULOS[0]!, MUSCULOS[1]!], { ejercicios: 8 });

    expect(screen.getByRole("button", { name: /^Lunes/ })).toHaveTextContent(
      "Pectorales, Tríceps · 8 ejercicios",
    );
  });

  it("avisa de que falta el equipamiento antes de gastar una generación", async () => {
    responderFormulario({ tiene_equipamiento: false });

    montarGenerar();

    expect(await screen.findByText(/no has indicado tu equipamiento/)).toBeVisible();
  });

  it("dice qué se le manda al modelo, y que la fecha de nacimiento no", async () => {
    montarGenerar();

    expect(await screen.findByText(/nunca tu fecha de nacimiento/)).toBeVisible();
  });

  it("generar manda el reparto tal cual y no guarda nada: lleva a la propuesta", async () => {
    let recibido: unknown = null;
    servidor.use(
      http.post("/api/ia/generar/", async ({ request }) => {
        recibido = await request.json();
        return HttpResponse.json(PROPUESTA, { status: 201 });
      }),
    );
    montarGenerar();

    await rellenarDia("Lunes", [MUSCULOS[0]!, MUSCULOS[1]!], {
      enfasis: "Pectorales",
      ejercicios: 8,
    });
    await rellenarDia("Miércoles", [MUSCULOS[3]!]);
    await userEvent.type(
      await screen.findByLabelText(/Algo que deba tener en cuenta/),
      "los viernes tengo poco tiempo",
    );
    await userEvent.click(screen.getByRole("button", { name: "Generar propuesta" }));

    await waitFor(() =>
      expect(recibido).toEqual({
        notes: "los viernes tengo poco tiempo",
        training_goal: "hypertrophy",
        split: [
          { weekday: 0, muscles: ["pectorals", "triceps"], emphasis: "pectorals", exercises: 8 },
          { weekday: 2, muscles: ["quads"], emphasis: null, exercises: 6 },
        ],
      }),
    );
    expect(await screen.findByText(/Propuesta/)).toBeVisible();
  });

  it("sin cupo no deja pulsar", async () => {
    responderFormulario({ restantes: 0 });

    montarGenerar();

    await rellenarDia("Lunes", [MUSCULOS[0]!]);

    expect(screen.getByRole("button", { name: "Generar propuesta" })).toBeDisabled();
  });

  it("el conflicto de 48 h se avisa y no se pinta como un fallo del modelo", async () => {
    servidor.use(
      http.post("/api/ia/generar/", () =>
        fallo("descanso", "Lunes y Martes repiten Pectorales.", 400),
      ),
    );
    montarGenerar();

    await rellenarDia("Lunes", [MUSCULOS[0]!]);
    await rellenarDia("Martes", [MUSCULOS[0]!]);
    await userEvent.click(screen.getByRole("button", { name: "Generar propuesta" }));

    expect(await screen.findByText(/repiten Pectorales/)).toBeVisible();
  });

  it("sin equipamiento que encaje manda al perfil, no a reintentar", async () => {
    servidor.use(
      http.post("/api/ia/generar/", () =>
        fallo("sin_candidatos", "No hay ejercicios que encajen con tu equipamiento.", 409),
      ),
    );
    montarGenerar();

    await rellenarDia("Lunes", [MUSCULOS[0]!]);
    await userEvent.click(screen.getByRole("button", { name: "Generar propuesta" }));

    const aviso = await screen.findByRole("alert");
    expect(within(aviso).getByRole("link", { name: "Completar el perfil" })).toBeVisible();
  });

  it("con el proveedor caído dice que se reintente y que no gasta generaciones", async () => {
    servidor.use(
      http.post("/api/ia/generar/", () =>
        fallo("proveedor", "Fallo al hablar con el proveedor: caído", 502),
      ),
    );
    montarGenerar();

    await rellenarDia("Lunes", [MUSCULOS[0]!]);
    await userEvent.click(screen.getByRole("button", { name: "Generar propuesta" }));

    expect(await screen.findByText(/no gasta generaciones/)).toBeVisible();
  });

  it("quedarse sin cupo no se pinta como un error", async () => {
    servidor.use(
      http.post("/api/ia/generar/", () =>
        fallo("cuota", "Has alcanzado el límite de 3 generaciones por hora.", 429),
      ),
    );
    montarGenerar();

    await rellenarDia("Lunes", [MUSCULOS[0]!]);
    await userEvent.click(screen.getByRole("button", { name: "Generar propuesta" }));

    expect(await screen.findByText(/límite de 3 generaciones/)).toBeVisible();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });
});

function montarPropuesta(datos: Propuesta = PROPUESTA) {
  servidor.use(http.get("/api/ia/propuestas/:id/", () => HttpResponse.json(datos)));
  return montar(
    <Routes>
      <Route path="/ia/propuestas/:id" element={<PropuestaDeRutina />} />
      <Route path="/plan" element={<p>Mi plan</p>} />
      <Route path="/ia/generar" element={<p>Generar otra</p>} />
    </Routes>,
    { ruta: "/ia/propuestas/7" },
  );
}

describe("PropuestaDeRutina", () => {
  it("deja claro que todavía no está guardada", async () => {
    montarPropuesta();

    expect(await screen.findByText("Propuesta — todavía no guardada")).toBeVisible();
    expect(screen.getByRole("heading", { name: "Empuje/Tirón", level: 1 })).toBeVisible();
  });

  it("enseña los siete días, también los de descanso", async () => {
    montarPropuesta();

    await screen.findByText("Lunes");
    expect(screen.getAllByText("Descanso")).toHaveLength(5);
    expect(screen.getAllByText("Empuje")).toHaveLength(3);
  });

  it("el texto del modelo se pinta como texto, no como HTML", async () => {
    montarPropuesta({ ...PROPUESTA, motivo: '<img src=x onerror="alert(1)">Hola' });

    const parrafo = await screen.findByText(/Hola/);
    expect(parrafo.textContent).toContain("<img");
    expect(document.querySelector("img[onerror]")).toBeNull();
  });

  it("aceptar crea el programa y lleva al plan", async () => {
    let llamado = false;
    servidor.use(
      http.post("/api/ia/propuestas/:id/aceptar/", () => {
        llamado = true;
        return HttpResponse.json({ programa: { id: 3, nombre: "Empuje/Tirón" } }, { status: 201 });
      }),
    );
    montarPropuesta();

    await userEvent.click(await screen.findByRole("button", { name: "Guardar y activar" }));

    await waitFor(() => expect(llamado).toBe(true));
    expect(await screen.findByText("Mi plan")).toBeVisible();
  });

  it("descartar lleva a generar otra, no al plan", async () => {
    servidor.use(
      http.post("/api/ia/propuestas/:id/descartar/", () => new HttpResponse(null, { status: 204 })),
    );
    montarPropuesta();

    await userEvent.click(await screen.findByRole("button", { name: "Descartar" }));

    expect(await screen.findByText("Generar otra")).toBeVisible();
  });

  it("una propuesta ya aplicada no ofrece volver a guardarla", async () => {
    montarPropuesta({ ...PROPUESTA, ya_aplicada: true });

    expect(await screen.findByText("Ya aplicada")).toBeVisible();
    expect(screen.queryByRole("button", { name: "Guardar y activar" })).not.toBeInTheDocument();
  });

  it("avisa de los ejercicios que ya no están en el catálogo", async () => {
    montarPropuesta({
      ...PROPUESTA,
      rutinas: [
        {
          nombre: "Empuje",
          ejercicios: [
            { ...PROPUESTA.rutinas[0]!.ejercicios[0]!, en_catalogo: false, nombre: "9999" },
          ],
        },
      ],
    });

    expect(await screen.findByText(/ya no está en el catálogo/)).toBeVisible();
    expect(screen.getByText("ya no está")).toBeVisible();
  });

  it("dice lo que costó la llamada", async () => {
    montarPropuesta();

    expect(await screen.findByText(/claude-opus-5/)).toBeVisible();
    expect(screen.getByText("800+300")).toBeVisible();
  });

  it("una propuesta que no existe lo dice en vez de quedarse en blanco", async () => {
    servidor.use(
      http.get("/api/ia/propuestas/:id/", () =>
        HttpResponse.json({ detail: "No encontrado." }, { status: 404 }),
      ),
    );

    montar(
      <Routes>
        <Route path="/ia/propuestas/:id" element={<PropuestaDeRutina />} />
      </Routes>,
      { ruta: "/ia/propuestas/99" },
    );

    expect(await screen.findByText("Esta propuesta no existe")).toBeVisible();
  });
});

const ANALISIS: EstadoDelAnalisis = {
  restantes: 2,
  sesiones: 12,
  sesiones_necesarias: 6,
  generacion: {
    id: 9, fecha: "2026-09-20T10:00:00Z", proveedor: "Anthropic (Claude)",
    modelo: "claude-opus-5", latencia_ms: 3000, tokens_entrada: 1200, tokens_salida: 400,
  },
  analisis: {
    summary: "Vas bien en general.",
    patterns: ["Volumen estable"],
    stalled: [{ exercise: "Press de banca", weeks_stalled: 6, likely_cause: "poco volumen" }],
    recommendations: ["Sube una serie en press"],
    proposed_changes: [
      { target: "Lunes", change: "Añadir una serie", reason: "Estancamiento" },
    ],
    data_caveats: ["Sin RPE no se puede juzgar la intensidad."],
  },
};

function montarAnalisis(datos: Partial<EstadoDelAnalisis> = {}, ruta = "/ia/analisis/") {
  servidor.use(
    http.get("/api/ia/analisis/", () => HttpResponse.json({ ...ANALISIS, ...datos })),
  );
  return montar(<AnalisisDeProgreso />, { ruta });
}

describe("AnalisisDeProgreso", () => {
  it("enseña el resumen, los patrones y los cambios propuestos, cada uno en su pestaña", async () => {
    montarAnalisis();

    expect(await screen.findByText("Vas bien en general.")).toBeVisible();
    await userEvent.click(screen.getByRole("tab", { name: /Estancamientos/ }));
    expect(screen.getByText("Volumen estable")).toBeVisible();
    await userEvent.click(screen.getByRole("tab", { name: /Cambios/ }));
    expect(screen.getByText("Añadir una serie")).toBeVisible();
  });

  it("cada pestaña dice cuántas cosas tiene dentro", async () => {
    montarAnalisis();

    expect(await screen.findByRole("tab", { name: "Estancamientos 1" })).toBeVisible();
    expect(screen.getByRole("tab", { name: "Cambios 1" })).toBeVisible();
  });

  it("«lo que no se puede afirmar» va antes que las recomendaciones", async () => {
    montarAnalisis();

    const caveats = await screen.findByText("Lo que no se puede afirmar todavía");
    const recomendaciones = screen.getByText("Recomendaciones");
    expect(caveats.compareDocumentPosition(recomendaciones)).toBe(
      Node.DOCUMENT_POSITION_FOLLOWING,
    );
  });

  it("los cambios no se aplican solos: mandan al plan", async () => {
    montarAnalisis({}, "/ia/analisis/?vista=cambios");

    await screen.findByText("Cambios propuestos a tu rutina");
    expect(screen.getByRole("link", { name: "tus rutinas" })).toHaveAttribute("href", "/plan/");
  });

  it("sin historial suficiente no deja pulsar, y dice cuánto falta", async () => {
    montarAnalisis({ sesiones: 2, analisis: null, generacion: null });

    expect(await screen.findByText("Hacen falta más entrenamientos")).toBeVisible();
    expect(screen.getByText(/2 \/ 6 sesiones/)).toBeVisible();
    expect(screen.getByRole("button", { name: "Analizar ahora" })).toBeDisabled();
  });

  it("con historial pero sin análisis invita a pedirlo", async () => {
    montarAnalisis({ analisis: null, generacion: null });

    expect(await screen.findByText("Todavía no has pedido ningún análisis")).toBeVisible();
    expect(screen.getByRole("button", { name: "Analizar ahora" })).toBeEnabled();
  });

  it("pedir uno nuevo pinta el resultado sin recargar", async () => {
    montarAnalisis({ analisis: null, generacion: null });
    servidor.use(
      http.post("/api/ia/analisis/", () => HttpResponse.json(ANALISIS, { status: 201 })),
    );

    await userEvent.click(await screen.findByRole("button", { name: "Analizar ahora" }));

    expect(await screen.findByText("Vas bien en general.")).toBeVisible();
  });

  it("el texto del análisis se pinta como texto", async () => {
    montarAnalisis({
      analisis: { ...ANALISIS.analisis!, summary: '<script>alert(1)</script>Ojo' },
    });

    const resumen = await screen.findByText(/Ojo/);
    expect(resumen.textContent).toContain("<script>");
    expect(document.querySelector("script")).toBeNull();
  });

  it("sin cupo no deja pulsar", async () => {
    montarAnalisis({ restantes: 0 });

    expect(await screen.findByRole("button", { name: "Analizar de nuevo" })).toBeDisabled();
  });
});
