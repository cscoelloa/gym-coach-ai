import { screen, waitFor, within } from "@testing-library/react";
import { userEvent } from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { beforeEach, describe, expect, it } from "vitest";

import { montar } from "@/test/montar";
import { servidor } from "@/test/servidor";

import type {
  Almacen,
  Documento,
  GeneracionDetalle,
  GeneracionEnLista,
  MetricaDeGestion,
  Prompt,
  Proveedor,
  ResumenDelPanel,
  UsuarioDeGestion,
} from "./api";
import { Auditoria } from "./Auditoria";
import { CatalogoYMetricas } from "./CatalogoYMetricas";
import { GestionDeIa } from "./ia/GestionDeIa";
import { ResumenDeGestion } from "./ResumenDeGestion";
import { Usuarios } from "./Usuarios";

const RESUMEN: ResumenDelPanel = {
  dias: 7,
  proveedor: { nombre: "Anthropic (Claude)", modelo: "claude-opus-5", clave_usable: true },
  generaciones: { total: 12, errores: 0 },
  documentos: { total: 4, fallidos: 0, pendientes: 0 },
  usuarios: { total: 31, nuevos: 3, bloqueados: 0 },
  metricas: { activas: 12, total: 12 },
};

function responderResumen(extra: Partial<ResumenDelPanel> = {}) {
  servidor.use(
    http.get("/api/gestion/resumen/", () => HttpResponse.json({ ...RESUMEN, ...extra })),
  );
}

describe("ResumenDeGestion", () => {
  beforeEach(() => responderResumen());

  it("con todo en orden no pinta ni un aviso", async () => {
    montar(<ResumenDeGestion />);

    await screen.findByText("Anthropic (Claude)");
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("sin proveedor avisa de que la IA no funciona para nadie", async () => {
    responderResumen({ proveedor: null });

    montar(<ResumenDeGestion />);

    expect(await screen.findByText(/No hay ningún proveedor de IA activo/)).toBeVisible();
  });

  it("con la clave ilegible lo dice, que es el fallo silencioso de esta zona", async () => {
    responderResumen({
      proveedor: { nombre: "Anthropic (Claude)", modelo: "claude-opus-5", clave_usable: false },
    });

    montar(<ResumenDeGestion />);

    expect(await screen.findByText(/no se puede descifrar/)).toBeVisible();
  });

  it("avisa de los documentos sin indexar diciendo qué implica", async () => {
    responderResumen({ documentos: { total: 4, fallidos: 2, pendientes: 0 } });

    montar(<ResumenDeGestion />);

    expect(await screen.findByText(/respondiendo sin ese contexto/)).toBeVisible();
  });
});

const PROVEEDOR: Proveedor = {
  id: 1,
  provider: "anthropic",
  provider_label: "Anthropic (Claude)",
  model: "",
  effective_model: "claude-opus-5",
  masked_api_key: "sk-···1234",
  has_usable_key: true,
  max_tokens: 16000,
  effort: "",
  timeout_seconds: 120,
  is_active: true,
  created_at: "2026-09-01T10:00:00Z",
  updated_at: "2026-09-01T10:00:00Z",
};

const PROMPT: Prompt = {
  id: 2,
  key: "routine_generation",
  key_label: "Generación de rutinas",
  name: "Rutinas v1",
  system_prompt: "Eres un entrenador.",
  user_template: "Perfil: {{ perfil }}",
  version: 1,
  is_active: true,
  available_variables: ["perfil", "objetivo", "candidatos"],
  created_at: "2026-09-01T10:00:00Z",
};

const ALMACEN: Almacen = {
  id: 3,
  name: "Libros",
  description: "Manuales de fuerza",
  openai_vector_store_id: "vs_1",
  is_ready: true,
  is_active: true,
  documentos: { total: 3, indexados: 2, fallidos: 1 },
  created_at: "2026-09-01T10:00:00Z",
};

const DOCUMENTO: Documento = {
  id: 4,
  vector_store: 3,
  almacen: "Libros",
  title: "Practical Programming",
  file: "/media/knowledge/pp.pdf",
  status: "failed",
  status_label: "Fallido",
  error: "se agotó el tiempo",
  attributes: {},
  subido_por: "jefa",
  created_at: "2026-09-01T10:00:00Z",
};

const PROGRAMACION = {
  id: 1,
  goal: "hypertrophy",
  goal_label: "Hipertrofia",
  sets_min: 3,
  sets_max: 4,
  reps_min: 6,
  reps_max: 20,
  rest_min_compound: 120,
  rest_min_isolation: 90,
  sets_min_per_muscle_day: 6,
  resumen: "3-4 series · 6-20 repeticiones · 120 s de descanso",
};

function responderIa() {
  servidor.use(
    http.get("/api/gestion/programacion/", () => HttpResponse.json([PROGRAMACION])),
    http.get("/api/gestion/proveedores/", () => HttpResponse.json([PROVEEDOR])),
    http.get("/api/gestion/prompts/", () => HttpResponse.json([PROMPT])),
    http.get("/api/gestion/almacenes/", () => HttpResponse.json([ALMACEN])),
    http.get("/api/gestion/documentos/", () => HttpResponse.json([DOCUMENTO])),
    http.get("/api/gestion/documentos/limites/", () =>
      HttpResponse.json({ extensiones: [".pdf", ".docx", ".txt", ".md"], max_bytes: 52428800 }),
    ),
  );
}

describe("GestionDeIa — proveedores", () => {
  beforeEach(responderIa);

  it("la clave se enseña enmascarada y el campo de cambiarla va vacío", async () => {
    montar(<GestionDeIa />);

    expect(await screen.findByText("sk-···1234")).toBeVisible();
    expect(screen.getByLabelText("Cambiar la clave")).toHaveValue("");
  });

  it("probar dice cuánto tardó y recuerda que también cuesta", async () => {
    servidor.use(
      http.post("/api/gestion/proveedores/:id/probar/", () =>
        HttpResponse.json({ ok: true, latencia_ms: 800, tokens: 15, modelo: "claude-opus-5" }),
      ),
    );
    montar(<GestionDeIa />);

    await userEvent.click(await screen.findByRole("button", { name: "Probar conexión" }));

    expect(await screen.findByText(/800 ms/)).toBeVisible();
    expect(screen.getByText(/también cuesta/)).toBeVisible();
  });

  it("una clave mala lo dice sin dejar la pantalla rota", async () => {
    servidor.use(
      http.post("/api/gestion/proveedores/:id/probar/", () =>
        HttpResponse.json({ ok: false, detail: "401 unauthorized" }, { status: 502 }),
      ),
    );
    montar(<GestionDeIa />);

    await userEvent.click(await screen.findByRole("button", { name: "Probar conexión" }));

    expect(await screen.findByText("401 unauthorized")).toBeVisible();
  });

  it("solo ofrece guardar cuando se ha escrito una clave", async () => {
    montar(<GestionDeIa />);

    await screen.findByText("sk-···1234");
    expect(screen.queryByRole("button", { name: "Guardar la clave" })).not.toBeInTheDocument();

    await userEvent.type(screen.getByLabelText("Cambiar la clave"), "sk-nueva");

    expect(screen.getByRole("button", { name: "Guardar la clave" })).toBeVisible();
  });

  it("marca el proveedor con la clave ilegible", async () => {
    servidor.use(
      http.get("/api/gestion/proveedores/", () =>
        HttpResponse.json([{ ...PROVEEDOR, has_usable_key: false }]),
      ),
    );

    montar(<GestionDeIa />);

    expect(await screen.findByText("Clave ilegible")).toBeVisible();
  });

  it("el tope de salida se edita desde la tarjeta, sin tocar la clave", async () => {
    let recibido: { max_tokens?: number; api_key?: string } | null = null;
    servidor.use(
      http.patch("/api/gestion/proveedores/:id/", async ({ request }) => {
        recibido = (await request.json()) as { max_tokens?: number };
        return HttpResponse.json({ ...PROVEEDOR, max_tokens: 3000 });
      }),
    );
    montar(<GestionDeIa />);

    const campo = await screen.findByLabelText(/Tope de salida/);
    await userEvent.clear(campo);
    await userEvent.type(campo, "3000");
    await userEvent.click(screen.getByRole("button", { name: "Guardar ajustes" }));

    await waitFor(() => expect(recibido?.max_tokens).toBe(3000));
    expect(recibido).not.toHaveProperty("api_key");
  });

  it("sin cambios no hay nada que guardar", async () => {
    montar(<GestionDeIa />);

    await screen.findByLabelText(/Tope de salida/);
    expect(screen.queryByRole("button", { name: "Guardar ajustes" })).not.toBeInTheDocument();
  });
});

describe("GestionDeIa — prompts", () => {
  beforeEach(responderIa);

  async function abrirPrompts() {
    montar(<GestionDeIa />);
    await userEvent.click(await screen.findByRole("tab", { name: "Prompts" }));
  }

  it("enseña las variables disponibles antes del campo", async () => {
    await abrirPrompts();
    await userEvent.click(await screen.findByRole("button", { name: "Editar" }));

    expect(screen.getByText("{{ perfil }}")).toBeVisible();
    expect(screen.getByText("{{ candidatos }}")).toBeVisible();
  });

  it("la vista previa avisa de las variables que no existen", async () => {
    servidor.use(
      http.post("/api/gestion/prompts/:id/vista_previa/", () =>
        HttpResponse.json({
          system: "Eres un entrenador.",
          mensaje: "Perfil: «perfil»",
          variables: ["perfil"],
          desconocidas: ["edda"],
        }),
      ),
    );
    await abrirPrompts();
    await userEvent.click(await screen.findByRole("button", { name: "Editar" }));

    await userEvent.click(screen.getByRole("button", { name: "Vista previa" }));

    expect(await screen.findByText(/se renderizarán vacías/)).toBeVisible();
    expect(screen.getByText("edda")).toBeVisible();
  });

  it("sin cambios no deja guardar", async () => {
    await abrirPrompts();
    await userEvent.click(await screen.findByRole("button", { name: "Editar" }));

    expect(screen.getByRole("button", { name: "Guardar" })).toBeDisabled();
  });

  it("una plantilla rota se rechaza y lo dice", async () => {
    servidor.use(
      http.patch("/api/gestion/prompts/:id/", () =>
        HttpResponse.json(
          { detail: "Error de sintaxis en la plantilla: se esperaba una condición" },
          { status: 400 },
        ),
      ),
    );
    await abrirPrompts();
    await userEvent.click(await screen.findByRole("button", { name: "Editar" }));

    await userEvent.type(screen.getByLabelText("Plantilla del mensaje"), "{{");
    await userEvent.click(screen.getByRole("button", { name: "Guardar" }));

    expect(await screen.findByText(/Error de sintaxis/)).toBeVisible();
  });
});

describe("GestionDeIa — documentos", () => {
  beforeEach(responderIa);

  it("enseña cuántos hay indexados y cuántos han fallado", async () => {
    montar(<GestionDeIa />);
    await userEvent.click(await screen.findByRole("tab", { name: "Documentos" }));

    expect(await screen.findByText("Libros")).toBeVisible();
    expect(screen.getByText(/2/)).toBeVisible();
    expect(screen.getByText("se agotó el tiempo")).toBeVisible();
  });

  it("solo ofrece reintentar en los que fallaron", async () => {
    servidor.use(
      http.get("/api/gestion/documentos/", () =>
        HttpResponse.json([
          DOCUMENTO,
          { ...DOCUMENTO, id: 5, status: "indexed", status_label: "Indexado", error: "" },
        ]),
      ),
    );
    montar(<GestionDeIa />);
    await userEvent.click(await screen.findByRole("tab", { name: "Documentos" }));

    await screen.findByText("Indexado");
    expect(screen.getAllByRole("button", { name: "Reintentar" })).toHaveLength(1);
  });

  it("sube un documento como multipart, no como JSON", async () => {
    let tipo: string | null = null;
    servidor.use(
      http.post("/api/gestion/documentos/", ({ request }) => {
        tipo = request.headers.get("content-type");
        return HttpResponse.json({ ...DOCUMENTO, id: 9 }, { status: 201 });
      }),
    );
    montar(<GestionDeIa />);
    await userEvent.click(await screen.findByRole("tab", { name: "Documentos" }));

    await userEvent.type(await screen.findByLabelText("Título"), "Guía de series");
    await userEvent.upload(
      screen.getByLabelText("Archivo"),
      new File(["# hipertrofia"], "guia.md", { type: "text/markdown" }),
    );
    await userEvent.click(screen.getByRole("button", { name: "Subir e indexar" }));

    await waitFor(() => expect(tipo).toMatch(/^multipart\/form-data; boundary=/));
    expect(await screen.findByText(/El indexado va aparte/)).toBeVisible();
  });

  it("el mensaje del validador se pinta en el campo del archivo", async () => {
    servidor.use(
      http.post("/api/gestion/documentos/", () =>
        HttpResponse.json(
          { file: ["El contenido del archivo no corresponde a un .pdf."] },
          { status: 400 },
        ),
      ),
    );
    montar(<GestionDeIa />);
    await userEvent.click(await screen.findByRole("tab", { name: "Documentos" }));

    await userEvent.type(await screen.findByLabelText("Título"), "Trampa");
    await userEvent.upload(
      screen.getByLabelText("Archivo"),
      new File(["MZ"], "trampa.pdf", { type: "application/pdf" }),
    );
    await userEvent.click(screen.getByRole("button", { name: "Subir e indexar" }));

    const campo = await screen.findByLabelText("Archivo");
    expect(campo).toHaveAccessibleDescription(/no corresponde a un .pdf/);
  });

  it("sin almacén ofrece crearlo, que es lo único que se puede hacer", async () => {
    servidor.use(http.get("/api/gestion/almacenes/", () => HttpResponse.json([])));
    let creado: unknown = null;
    servidor.use(
      http.post("/api/gestion/almacenes/", async ({ request }) => {
        creado = await request.json();
        return HttpResponse.json({ ...ALMACEN, id: 7 }, { status: 201 });
      }),
    );
    montar(<GestionDeIa />);
    await userEvent.click(await screen.findByRole("tab", { name: "Documentos" }));

    await userEvent.type(await screen.findByLabelText("Nombre"), "Hipertrofia");
    await userEvent.click(screen.getByRole("button", { name: "Crear almacén" }));

    await waitFor(() =>
      expect(creado).toEqual({ name: "Hipertrofia", description: "" }),
    );
  });

  it("un almacén sin crear en OpenAI no admite documentos todavía", async () => {
    servidor.use(
      http.get("/api/gestion/almacenes/", () =>
        HttpResponse.json([{ ...ALMACEN, is_ready: false, openai_vector_store_id: "" }]),
      ),
    );
    montar(<GestionDeIa />);
    await userEvent.click(await screen.findByRole("tab", { name: "Documentos" }));

    expect(await screen.findByRole("button", { name: "Crear en OpenAI" })).toBeVisible();
    expect(screen.queryByRole("button", { name: "Subir e indexar" })).not.toBeInTheDocument();
  });

  it("mientras se indexa, vuelve a preguntar hasta que termina", async () => {
    let peticiones = 0;
    servidor.use(
      http.get("/api/gestion/documentos/", () => {
        peticiones++;
        return HttpResponse.json([
          peticiones < 2
            ? { ...DOCUMENTO, status: "indexing", status_label: "Indexando", error: "" }
            : { ...DOCUMENTO, status: "indexed", status_label: "Indexado", error: "" },
        ]);
      }),
    );
    montar(<GestionDeIa />);
    await userEvent.click(await screen.findByRole("tab", { name: "Documentos" }));

    expect(await screen.findByText("Indexando")).toBeVisible();
    expect(await screen.findByText("Indexado", undefined, { timeout: 8000 })).toBeVisible();
  }, 15000);

  it("borrar pide confirmación y dice que también se va de OpenAI", async () => {
    let borrado = 0;
    servidor.use(
      http.delete("/api/gestion/documentos/:id/", () => {
        borrado++;
        return new HttpResponse(null, { status: 204 });
      }),
    );
    montar(<GestionDeIa />);
    await userEvent.click(await screen.findByRole("tab", { name: "Documentos" }));

    await userEvent.click(await screen.findByRole("button", { name: "Borrar" }));
    expect(await screen.findByText(/también del almacén en OpenAI/)).toBeVisible();
    expect(borrado).toBe(0);

    await userEvent.click(screen.getByRole("button", { name: "Sí, borrarlo" }));
    await waitFor(() => expect(borrado).toBe(1));
  });
});

describe("GestionDeIa — programación", () => {
  beforeEach(responderIa);

  it("enseña los números con los que se valida cada objetivo", async () => {
    montar(<GestionDeIa />);
    await userEvent.click(await screen.findByRole("tab", { name: "Programación" }));

    expect(await screen.findByText("Hipertrofia")).toBeVisible();
    expect(screen.getByLabelText("Series mínimas por ejercicio")).toHaveValue(3);
    expect(screen.getByLabelText("Series mínimas por músculo y día")).toHaveValue(6);
  });

  it("guardar manda los números nuevos, que valen para la siguiente generación", async () => {
    let recibido: { sets_min?: number } | null = null;
    servidor.use(
      http.patch("/api/gestion/programacion/:id/", async ({ request }) => {
        recibido = (await request.json()) as { sets_min?: number };
        return HttpResponse.json({ ...PROGRAMACION, sets_min: 4 });
      }),
    );
    montar(<GestionDeIa />);
    await userEvent.click(await screen.findByRole("tab", { name: "Programación" }));

    const campo = await screen.findByLabelText("Series mínimas por ejercicio");
    await userEvent.clear(campo);
    await userEvent.type(campo, "4");
    await userEvent.click(screen.getByRole("button", { name: "Guardar" }));

    await waitFor(() => expect(recibido?.sets_min).toBe(4));
  });
});

const GENERACION: GeneracionEnLista = {
  id: 9,
  usuario: "socia",
  kind: "routine",
  kind_label: "Rutina",
  provider: "anthropic",
  model: "claude-opus-5",
  status: "ok",
  status_label: "Correcta",
  input_tokens: 800,
  output_tokens: 300,
  latency_ms: 2000,
  error: "",
  created_at: "2026-09-20T10:00:00Z",
};

const DETALLE: GeneracionDetalle = {
  ...GENERACION,
  prompt_rendered: "Eres un entrenador. Lesiones: hombro derecho.",
  raw_response: '{"name": "Empuje"}',
  parsed_output: { name: "Empuje" },
};

describe("Auditoria", () => {
  beforeEach(() => {
    servidor.use(
      http.get("/api/gestion/generaciones/resumen/", () =>
        HttpResponse.json({
          dias: 7, total: 12, errores: 1, tokens: 14200,
          por_tipo: [{ tipo: "routine", etiqueta: "Rutina", total: 10, errores: 1 }],
        }),
      ),
      http.get("/api/gestion/generaciones/", () =>
        HttpResponse.json({ count: 1, next: null, previous: null, results: [GENERACION] }),
      ),
      http.get("/api/gestion/generaciones/:id/", () => HttpResponse.json(DETALLE)),
    );
  });

  it("el listado no lleva el prompt ni la respuesta cruda", async () => {
    montar(<Auditoria />);

    await screen.findByText("socia");
    expect(screen.queryByText(/hombro derecho/)).not.toBeInTheDocument();
  });

  it("al abrir una fila sí, en una hoja, y avisa de lo que se está mirando", async () => {
    montar(<Auditoria />);

    await userEvent.click(await screen.findByRole("button", { name: /^Ver la generación/ }));

    const hoja = screen.getByRole("dialog", { name: /^Generación #/ });
    expect(await within(hoja).findByText(/hombro derecho/)).toBeVisible();
    expect(screen.getByText(/No salgas de esta pantalla con ella abierta/)).toBeVisible();
  });

  it("filtrar por estado vuelve a pedir la lista", async () => {
    let ultima = "";
    servidor.use(
      http.get("/api/gestion/generaciones/", ({ request }) => {
        ultima = new URL(request.url).search;
        return HttpResponse.json({ count: 0, next: null, previous: null, results: [] });
      }),
    );
    montar(<Auditoria />);

    await userEvent.click(await screen.findByRole("button", { name: "Con error" }));

    await waitFor(() => expect(ultima).toContain("estado=error"));
  });

  it("el resumen dice el gasto de la semana", async () => {
    montar(<Auditoria />);

    expect(await screen.findByText("14.200")).toBeVisible();
  });
});

const USUARIO: UsuarioDeGestion = {
  id: 5,
  username: "socia",
  email: "socia@example.com",
  first_name: "Sonia",
  is_active: true,
  is_staff: false,
  date_joined: "2026-08-01T10:00:00Z",
  last_login: "2026-09-19T10:00:00Z",
  entrenamientos: 14,
  rutinas: 3,
  generaciones: 2,
  bloqueado: false,
};

describe("Usuarios", () => {
  function responder(extra: Partial<UsuarioDeGestion> = {}) {
    servidor.use(
      http.get("/api/gestion/usuarios/", () => HttpResponse.json([{ ...USUARIO, ...extra }])),
    );
  }

  beforeEach(() => responder());

  it("no enseña ni un dato de salud", async () => {
    montar(<Usuarios />);

    await screen.findByText("socia");
    const tabla = screen.getByRole("table");
    for (const prohibido of ["altura", "peso", "lesion", "nacimiento", "sexo"]) {
      expect(
        within(tabla).queryByText(new RegExp(prohibido, "i")),
      ).not.toBeInTheDocument();
    }
  });

  it("dice qué lleva hecho cada cuenta", async () => {
    montar(<Usuarios />);

    const fila = (await screen.findByText("socia")).closest("tr")!;
    expect(within(fila).getByText("14")).toBeVisible();
  });

  it("solo ofrece desbloquear a quien está bloqueado", async () => {
    montar(<Usuarios />);
    await screen.findByText("socia");
    expect(screen.queryByRole("button", { name: "Desbloquear" })).not.toBeInTheDocument();

    responder({ bloqueado: true });
    montar(<Usuarios />);

    expect(await screen.findByRole("button", { name: "Desbloquear" })).toBeVisible();
  });

  it("desactivar una cuenta manda solo ese campo", async () => {
    let recibido: unknown = null;
    servidor.use(
      http.patch("/api/gestion/usuarios/:id/", async ({ request }) => {
        recibido = await request.json();
        return HttpResponse.json({ ...USUARIO, is_active: false });
      }),
    );
    montar(<Usuarios />);

    await userEvent.click(await screen.findByRole("button", { name: "Desactivar" }));

    await waitFor(() => expect(recibido).toEqual({ is_active: false }));
  });

  it("filtra por estado: lo que se busca casi siempre es quién está bloqueado", async () => {
    servidor.use(
      http.get("/api/gestion/usuarios/", () =>
        HttpResponse.json([
          USUARIO,
          { ...USUARIO, id: 6, username: "bloqueada", bloqueado: true },
          { ...USUARIO, id: 7, username: "inactiva", is_active: false, bloqueado: true },
        ]),
      ),
    );
    montar(<Usuarios />);
    await screen.findByText("socia");

    await userEvent.click(screen.getByRole("button", { name: "Bloqueadas · 1" }));

    expect(screen.getByText("bloqueada")).toBeVisible();
    expect(screen.queryByText("socia")).not.toBeInTheDocument();
    expect(screen.queryByText("inactiva")).not.toBeInTheDocument();
  });

  it("recuerda por qué no están los datos de salud", async () => {
    montar(<Usuarios />);

    expect(await screen.findByText(/son datos de salud y no hacen falta/)).toBeVisible();
  });
});

const METRICA: MetricaDeGestion = {
  id: 7,
  key: "weekly_tonnage",
  label: "Tonelaje semanal",
  description: "Kilos movidos por semana.",
  unit: "kg",
  category: "volume",
  category_label: "Volumen",
  chart: "line",
  is_active: true,
  send_to_ai: true,
  default_visible: true,
  en_paneles: 4,
};

describe("CatalogoYMetricas", () => {
  beforeEach(() => {
    servidor.use(
      http.get("/api/gestion/catalogo/", () =>
        HttpResponse.json({
          total: 1324, propios: 7, con_imagen: 1300, musculos: 30,
          por_zona: [
            { valor: "chest", etiqueta: "Pecho", n: 200 },
            { valor: "upper legs", etiqueta: "Piernas", n: 150 },
          ],
          por_material: [{ valor: "barbell", etiqueta: "Barra", n: 300 }],
        }),
      ),
      http.get("/api/gestion/metricas/", () => HttpResponse.json([METRICA])),
    );
  });

  it("dice cuántos ejercicios hay y cómo se reparten", async () => {
    montar(<CatalogoYMetricas />);

    expect(await screen.findByText("1324")).toBeVisible();
    expect(screen.getByText("Pecho")).toBeVisible();
  });

  it("explica que el catálogo no se edita aquí", async () => {
    montar(<CatalogoYMetricas />);

    expect(await screen.findByText(/se perdería en la siguiente importación/)).toBeVisible();
  });

  it("dice en cuántos paneles está cada métrica", async () => {
    montar(<CatalogoYMetricas />, { ruta: "/gestion/catalogo/?vista=metricas" });

    const insignia = await screen.findByText("4");
    expect(insignia.closest(".badge")?.textContent).toMatch(/en\s*4\s*paneles/);
  });

  it("apagar una métrica manda solo ese interruptor", async () => {
    let recibido: unknown = null;
    servidor.use(
      http.patch("/api/gestion/metricas/:id/", async ({ request }) => {
        recibido = await request.json();
        return HttpResponse.json({ ...METRICA, is_active: false });
      }),
    );
    montar(<CatalogoYMetricas />, { ruta: "/gestion/catalogo/?vista=metricas" });

    await userEvent.click(await screen.findByRole("checkbox", { name: "Se calcula" }));

    await waitFor(() => expect(recibido).toEqual({ is_active: false }));
  });

  it("no hay dónde editar la clave ni la descripción", async () => {
    montar(<CatalogoYMetricas />, { ruta: "/gestion/catalogo/?vista=metricas" });

    await screen.findByText("Tonelaje semanal");
    expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
  });
});
