import { screen, waitFor, within } from "@testing-library/react";
import { userEvent } from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { Route, Routes } from "react-router";
import { beforeEach, describe, expect, it } from "vitest";

import { montar } from "@/test/montar";
import { servidor } from "@/test/servidor";

import type { MetricaCalculada, MetricaDelCatalogo, Progreso as Datos } from "./api";
import { Metricas } from "./Metricas";
import { Progreso } from "./Progreso";

const SEMANAS = Array.from({ length: 3 }, (_, columna) => ({
  etiqueta: columna === 0 ? "sept" : "",
  dias: Array.from({ length: 7 }, (_, fila) => ({
    fecha: `2026-09-${String(1 + columna * 7 + fila).padStart(2, "0")}`,
    nivel: fila === 0 ? 3 : 0,
    minutos: fila === 0 ? 65 : 0,
    sesiones: fila === 0 ? 1 : 0,
  })),
}));

const PROGRESO: Datos = {
  hoy: "2026-09-20",
  cifras: {
    total_sesiones: 42,
    sesiones_este_mes: 7,
    racha_semanas: 3,
    peso_30_dias: -1.8,
  },
  calendario: { semanas: SEMANAS, niveles: [0, 1, 2, 3, 4] },
  peso: { serie: null },
  mapa_corporal: {
    niveles: { pectorals: 3, lats: 1 },
    series: { pectorals: 12 },
    total_series: 18.5,
    desde: "2026-09-14",
  },
  por_dia_de_semana: [
    { weekday: 0, inicial: "L", sesiones: 5 },
    { weekday: 1, inicial: "M", sesiones: 0 },
    { weekday: 2, inicial: "X", sesiones: 4 },
    { weekday: 3, inicial: "J", sesiones: 0 },
    { weekday: 4, inicial: "V", sesiones: 3 },
    { weekday: 5, inicial: "S", sesiones: 1 },
    { weekday: 6, inicial: "D", sesiones: 0 },
  ],
  semanas_por_dia: 12,
};

function metrica(extra: Partial<MetricaCalculada> = {}): MetricaCalculada {
  return {
    key: "stalled_exercises",
    label: "Ejercicios estancados",
    description: "Cuántos llevan seis semanas sin subir de peso.",
    unit: "",
    category: "strength",
    category_label: "Fuerza",
    chart: "scalar",
    value: null,
    series: [],
    columns: [],
    rows: [],
    coverage: 1,
    coverage_pct: 100,
    notes: [],
    has_no_data: false,
    is_reliable: true,
    empty_hint: "Todavía no hay datos.",
    needs: [],
    ...extra,
  };
}

function cajon(etiqueta: string): HTMLElement {
  const nombre = screen.getByText(etiqueta);
  return nombre.closest(".stat-tile") as HTMLElement;
}

function responder(datos: Partial<Datos> = {}, metricas: MetricaCalculada[] = []) {
  servidor.use(
    http.get("/api/progreso/", () => HttpResponse.json({ ...PROGRESO, ...datos })),
    http.get("/api/mis-metricas/", () => HttpResponse.json(metricas)),
    http.get("/api/mapa-corporal/", () => HttpResponse.json({ vistas: [], musculos: [] })),
  );
}

beforeEach(() => responder());

describe("Progreso — la cabecera", () => {
  it("enseña las cuatro cifras tal como llegan", async () => {
    montar(<Progreso />);

    await screen.findByText("Entrenamientos");
    expect(within(cajon("Entrenamientos")).getByText("42")).toBeVisible();
    expect(within(cajon("Este mes")).getByText("7")).toBeVisible();
    expect(within(cajon("Racha")).getByText("3")).toBeVisible();
    expect(within(cajon("Peso 30 días")).getByText("-1.8")).toBeVisible();
  });

  it("sin dos pesajes dice por qué, en vez de poner un cero", async () => {
    responder({ cifras: { ...PROGRESO.cifras, peso_30_dias: null } });

    montar(<Progreso />);

    expect(await screen.findByText("Hacen falta dos pesajes separados.")).toBeVisible();
  });

  it("la dirección del peso se lee sin depender del color", async () => {
    montar(<Progreso />);

    expect(await screen.findByText(/↓ en 30 días/)).toBeVisible();
  });

  it("el calendario pinta un día por celda, con el nombre del mes en su columna", async () => {
    montar(<Progreso />);

    await screen.findByText("Entrenamientos");
    expect(document.querySelectorAll(".heat-cell")).toHaveLength(3 * 7 + 5);
    expect(screen.getByText("sept")).toBeVisible();
  });

  it("cada día del calendario dice qué pasó ese día", async () => {
    montar(<Progreso />);

    await screen.findByText("Entrenamientos");
    const conTitulo = document.querySelector('.heat-cell[title*="1 entrenamiento"]');
    expect(conTitulo?.getAttribute("title")).toMatch(/65 min/);
  });

  it("sin dos pesos no dibuja una gráfica de un punto", async () => {
    montar(<Progreso />, { ruta: "/progreso/?vista=cuerpo" });

    expect(
      await screen.findByText(/Con dos registros o más verás aquí la tendencia/),
    ).toBeVisible();
  });

  it("los siete días de la semana salen siempre, también los que están a cero", async () => {
    montar(<Progreso />);

    const barras = await screen.findByRole("list", { name: "Sesiones por día" });
    expect(within(barras).getAllByRole("listitem")).toHaveLength(7);
    expect(within(barras).getByText("D")).toBeVisible();
  });
});

function montarMetricas() {
  return montar(<Progreso />, { ruta: "/progreso/?vista=metricas" });
}

describe("Progreso — las pestañas", () => {
  it("separa la pantalla en Actividad, Cuerpo y Métricas, con las cifras siempre arriba", async () => {
    montar(<Progreso />);

    await screen.findByText("Entrenamientos");
    expect(screen.getByRole("tab", { name: "Actividad" })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByRole("heading", { name: "Mapa de actividad" })).toBeVisible();
    expect(screen.queryByRole("heading", { name: "Peso corporal" })).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole("tab", { name: "Cuerpo" }));

    expect(screen.getByRole("heading", { name: "Peso corporal" })).toBeVisible();
    expect(screen.getByRole("heading", { name: "Qué has entrenado" })).toBeVisible();
    expect(within(cajon("Entrenamientos")).getByText("42")).toBeVisible();
  });

  it("las métricas no se piden hasta abrir su pestaña", async () => {
    let pedidas = 0;
    servidor.use(
      http.get("/api/mis-metricas/", () => {
        pedidas += 1;
        return HttpResponse.json([]);
      }),
    );
    montar(<Progreso />);
    await screen.findByText("Entrenamientos");
    expect(pedidas).toBe(0);

    await userEvent.click(screen.getByRole("tab", { name: "Métricas" }));

    expect(await screen.findByText("No tienes ninguna métrica seleccionada")).toBeVisible();
    expect(pedidas).toBe(1);
  });
});

describe("Progreso — las tarjetas de métrica", () => {
  it("una métrica sin datos no enseña su insignia aunque traiga un valor", async () => {
    responder({}, [
      metrica({ value: 0, coverage: 0, coverage_pct: 0, has_no_data: true, is_reliable: false }),
    ]);

    montarMetricas();

    const titulo = await screen.findByText("Ejercicios estancados");
    const tarjeta = titulo.closest(".insight-card") as HTMLElement;
    expect(within(tarjeta).queryByText("0")).not.toBeInTheDocument();
    expect(within(tarjeta).getByText("Todavía no hay datos.")).toBeVisible();
  });

  it("y lo dice una sola vez, sin el aviso de cobertura", async () => {
    responder({}, [
      metrica({ value: 0, coverage: 0, coverage_pct: 0, has_no_data: true, is_reliable: false }),
    ]);

    montarMetricas();

    await screen.findByText("Todavía no hay datos.");
    expect(screen.queryByText(/de los datos necesarios/)).not.toBeInTheDocument();
  });

  it("la descripción se queda aunque no haya datos", async () => {
    responder({}, [metrica({ has_no_data: true })]);

    montarMetricas();

    expect(
      await screen.findByText("Cuántos llevan seis semanas sin subir de peso."),
    ).toBeVisible();
  });

  it("con una cifra poco fiable sí avisa, y dice qué falta", async () => {
    responder({}, [
      metrica({
        key: "session_density",
        label: "Densidad de entrenamiento",
        value: 12.4,
        unit: "kg/min",
        coverage: 0.25,
        coverage_pct: 25,
        has_no_data: false,
        is_reliable: false,
        needs: ["la hora de inicio y fin de tus sesiones"],
      }),
    ]);

    montarMetricas();

    expect(await screen.findByText(/de los datos necesarios está registrado/)).toBeVisible();
    expect(screen.getByText(/la hora de inicio y fin de tus sesiones/)).toBeVisible();
    expect(screen.getByText("12.4")).toBeVisible();
  });

  it("una cifra fiable no arrastra ningún aviso", async () => {
    responder({}, [metrica({ value: 3, unit: "kg" })]);

    montarMetricas();

    const titulo = await screen.findByText("Ejercicios estancados");
    const tarjeta = titulo.closest(".insight-card") as HTMLElement;
    expect(within(tarjeta).getByText("3")).toBeVisible();
    expect(screen.queryByText(/de los datos necesarios/)).not.toBeInTheDocument();
  });

  it("una métrica de tabla enseña sus filas y dice cuántas se ha dejado", async () => {
    responder({}, [
      metrica({
        key: "personal_records",
        label: "Récords",
        chart: "table",
        columns: ["Ejercicio", "kg"],
        rows: Array.from({ length: 14 }, (_, i) => [`Ejercicio ${i}`, 80 + i]),
      }),
    ]);

    montarMetricas();

    expect(await screen.findByText("Ejercicio 0")).toBeVisible();
    expect(screen.getByText("Ejercicio 9")).toBeVisible();
    expect(screen.queryByText("Ejercicio 10")).not.toBeInTheDocument();
    expect(screen.getByText("Se muestran 10 de 14.")).toBeVisible();
  });

  it("sin ninguna elegida invita al catálogo en vez de dejar un hueco", async () => {
    montarMetricas();

    expect(await screen.findByText("No tienes ninguna métrica seleccionada")).toBeVisible();
    expect(screen.getByRole("link", { name: "Ir al catálogo" })).toHaveAttribute(
      "href",
      "/metricas/",
    );
  });

  it("si fallan las métricas la cabecera se sigue viendo", async () => {
    servidor.use(
      http.get("/api/mis-metricas/", () => HttpResponse.json({ detail: "Uf." }, { status: 500 })),
    );

    montarMetricas();

    await screen.findByText("Entrenamientos");
    expect(within(cajon("Entrenamientos")).getByText("42")).toBeVisible();
    expect(await screen.findByText("No se han podido cargar los datos")).toBeVisible();
  });
});

const CATALOGO: MetricaDelCatalogo[] = [
  {
    key: "weekly_tonnage",
    label: "Tonelaje semanal",
    description: "Kilos movidos por semana.",
    unit: "kg",
    category: "volume",
    category_label: "Volumen",
    chart: "line",
    visible: true,
  },
  {
    key: "adherence_rate",
    label: "Adherencia",
    description: "Sesiones hechas sobre planificadas.",
    unit: "%",
    category: "consistency",
    category_label: "Consistencia",
    chart: "scalar",
    visible: false,
  },
];

function montarCatalogo(datos = CATALOGO) {
  servidor.use(http.get("/api/metricas/", () => HttpResponse.json(datos)));
  return montar(
    <Routes>
      <Route path="/metricas" element={<Metricas />} />
      <Route path="/progreso" element={<p>Mi panel</p>} />
    </Routes>,
    { ruta: "/metricas" },
  );
}

describe("Metricas", () => {
  it("agrupa por categoría y marca lo que ya está en el panel", async () => {
    montarCatalogo();

    expect(await screen.findByRole("heading", { name: "Volumen" })).toBeVisible();
    expect(screen.getByRole("heading", { name: "Consistencia" })).toBeVisible();
    expect(screen.getByRole("checkbox", { name: /Tonelaje semanal/ })).toBeChecked();
    expect(screen.getByRole("checkbox", { name: /Adherencia/ })).not.toBeChecked();
  });

  it("marcar no guarda: hay que pulsar el botón", async () => {
    let llamado = false;
    servidor.use(
      http.put("/api/metricas/preferencias/", () => {
        llamado = true;
        return HttpResponse.json({ visibles: [] });
      }),
    );
    montarCatalogo();

    await userEvent.click(await screen.findByRole("checkbox", { name: /Adherencia/ }));

    expect(llamado).toBe(false);
  });

  it("guarda la lista entera, no solo lo que se ha tocado", async () => {
    let recibido: unknown = null;
    servidor.use(
      http.put("/api/metricas/preferencias/", async ({ request }) => {
        recibido = await request.json();
        return HttpResponse.json({ visibles: [] });
      }),
    );
    montarCatalogo();

    await userEvent.click(await screen.findByRole("checkbox", { name: /Adherencia/ }));
    await userEvent.click(screen.getByRole("button", { name: "Guardar mi panel" }));

    await waitFor(() =>
      expect(recibido).toEqual({ keys: ["weekly_tonnage", "adherence_rate"] }),
    );
  });

  it("desmarcar todo manda una lista vacía y no se cae", async () => {
    let recibido: unknown = null;
    servidor.use(
      http.put("/api/metricas/preferencias/", async ({ request }) => {
        recibido = await request.json();
        return HttpResponse.json({ visibles: [] });
      }),
    );
    montarCatalogo();

    await userEvent.click(await screen.findByRole("checkbox", { name: /Tonelaje semanal/ }));
    await userEvent.click(screen.getByRole("button", { name: "Guardar mi panel" }));

    await waitFor(() => expect(recibido).toEqual({ keys: [] }));
  });

  it("al guardar lleva al panel, que es lo que se acaba de configurar", async () => {
    servidor.use(
      http.put("/api/metricas/preferencias/", () => HttpResponse.json({ visibles: [] })),
    );
    montarCatalogo();

    await userEvent.click(await screen.findByRole("button", { name: "Guardar mi panel" }));

    expect(await screen.findByText("Mi panel")).toBeVisible();
  });

  it("dice cuántas van elegidas, y se actualiza al tocar", async () => {
    montarCatalogo();

    await screen.findByRole("checkbox", { name: /Adherencia/ });
    const cuenta = () => screen.getByText(/seleccionadas/).textContent ?? "";
    expect(cuenta()).toMatch(/1 de 2/);

    await userEvent.click(screen.getByRole("checkbox", { name: /Adherencia/ }));

    expect(cuenta()).toMatch(/2 de 2/);
  });
});
