import { expect, test, type ConsoleMessage, type Page } from "@playwright/test";

import { CLAVE, USUARIO } from "./cuenta";

function vigilarLaConsola(page: Page): string[] {
  const quejas: string[] = [];

  page.on("console", (mensaje: ConsoleMessage) => {
    if (mensaje.type() !== "error") return;
    const url = mensaje.location().url;
    quejas.push(`${mensaje.text()} — ${url || "sin URL"}`);
  });
  page.on("pageerror", (error) => quejas.push(`excepción sin capturar: ${error.message}`));
  page.on("requestfailed", (peticion) => {
    quejas.push(`petición fallida: ${peticion.url()} — ${peticion.failure()?.errorText}`);
  });

  return quejas;
}

async function enInicio(page: Page) {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Tu semana", level: 1 })).toBeVisible();
}

test("entrar lleva a Inicio", async ({ page }) => {
  const quejas = vigilarLaConsola(page);
  await page.context().clearCookies();

  await page.goto("/entrar/");
  await expect(page.getByRole("button", { name: "Entrar" })).toBeVisible();
  await page.screenshot({ path: test.info().outputPath("entrar.png") });
  await page.getByLabel("Usuario").fill(USUARIO);
  await page.getByLabel("Contraseña").fill(CLAVE);
  await page.getByRole("button", { name: "Entrar" }).click();

  await page.waitForURL("http://localhost:8000/");
  await expect(page.getByRole("heading", { name: "Tu semana", level: 1 })).toBeVisible();
  expect(quejas).toEqual([]);
});

test("desde Inicio se navega a Peso sin recargar la página", async ({ page }) => {
  const quejas = vigilarLaConsola(page);
  await enInicio(page);

  await page.evaluate(() => {
    (window as unknown as { __sinRecargar: boolean }).__sinRecargar = true;
  });
  await page.getByRole("link", { name: "Registrar", exact: true }).click();

  await expect(page.getByRole("heading", { name: "Peso corporal", level: 1 })).toBeVisible();
  expect(
    await page.evaluate(() => (window as unknown as { __sinRecargar?: boolean }).__sinRecargar),
  ).toBe(true);
  expect(quejas).toEqual([]);
});

test("registrar un peso lo enseña en el historial y en Inicio", async ({ page }) => {
  const quejas = vigilarLaConsola(page);
  await enInicio(page);
  await page.goto("/peso/");

  await page.getByLabel("Peso (kg)").fill("77.4");
  await page.getByRole("button", { name: "Guardar" }).click();

  await expect(page.getByText("Peso registrado.")).toBeVisible();
  await page.getByRole("tab", { name: /Historial/ }).click();
  await expect(page.getByRole("cell", { name: "77.40 kg" })).toBeVisible();

  await page.goto("/");
  await expect(page.getByText("77.4")).toBeVisible();
  expect(quejas).toEqual([]);

  await page.goto("/peso/?vista=historial");
  const fila = page.getByRole("row").filter({ hasText: "77.40 kg" });
  await fila.getByRole("button", { name: /^Borrar el registro/ }).click();
  await page.getByRole("dialog", { name: "Borrar el registro" }).getByRole("button", {
    name: "Sí, borrar",
  }).click();
  await expect(fila).toHaveCount(0);
});

test("el catálogo filtra por chip y la URL lo recuerda", async ({ page }) => {
  const quejas = vigilarLaConsola(page);
  await enInicio(page);

  await page.goto("/ejercicios/");
  await expect(page.getByRole("heading", { name: "Ejercicios", level: 1 })).toBeVisible();

  await page.getByText("Filtros · músculo, zona y equipamiento", { exact: true }).click();
  const chip = page.getByRole("button", { name: /^Pecho/ });
  await chip.click();

  await expect(page).toHaveURL(/body_part=chest/);
  await expect(chip).toHaveAttribute("aria-pressed", "true");

  await page.goBack();
  await expect(page).not.toHaveURL(/body_part/);
  expect(quejas).toEqual([]);
});

test("desde el catálogo se abre una ficha", async ({ page }) => {
  const quejas = vigilarLaConsola(page);
  await enInicio(page);
  await page.goto("/ejercicios/");

  const primera = page.locator("a.exercise-card").first();
  const nombre = (await primera.locator(".ex-name").textContent())?.trim();
  await primera.click();

  await expect(page).toHaveURL(/\/ejercicios\/[^/]+\/?$/);
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(
    new RegExp(nombre ?? "", "i"),
  );
  await expect(page.getByText(/gymvisual\.com/)).toBeVisible();
  expect(quejas).toEqual([]);
});

test("montar la semana: crear rutina, añadirle un ejercicio y asignarla a un día", async ({
  page,
}) => {
  const quejas = vigilarLaConsola(page);
  await enInicio(page);

  const nombre = `E2E ${Date.now()}`;
  await page.goto("/rutinas/nueva/");
  await page.getByLabel("Nombre").fill(nombre);
  await page.getByRole("button", { name: /Añadir ejercicio/ }).click();
  await page.getByRole("dialog").locator("button.compact-row").first().click();
  await page.getByRole("button", { name: "Añadir al borrador" }).click();
  await expect(page).toHaveURL(/rutinas\/nueva/);
  await page.getByRole("button", { name: "Guardar rutina" }).click();
  await expect(page).toHaveURL(/\/rutinas\/\d+\/?$/);
  await expect(page.getByText(/Rutina guardada/)).toBeVisible();

  await page.goto("/plan/dia/5/");
  await page.getByRole("radio", { name: new RegExp(nombre) }).click();
  await page.getByRole("button", { name: "Guardar" }).click();

  await expect(page).toHaveURL(/\/plan\/?$/);
  await expect(
    page.getByRole("region", { name: "Tu semana" }).getByText(nombre),
  ).toBeVisible();
  expect(quejas).toEqual([]);

  await page
    .getByRole("region", { name: "Tus rutinas" })
    .getByRole("link", { name: new RegExp(nombre) })
    .click();
  await page.getByRole("button", { name: "Eliminar rutina", exact: true }).click();
  await page.getByRole("button", { name: /^Sí, eliminar/ }).click();
  await expect(page).toHaveURL(/\/plan\/?$/);
  await expect(page.getByText(nombre)).toHaveCount(0);
});

test("entrenar: empezar una rutina, registrar una serie y cerrar", async ({ page }) => {
  const quejas = vigilarLaConsola(page);
  await enInicio(page);

  const nombre = `E2E entrenar ${Date.now()}`;
  await page.goto("/rutinas/nueva/");
  await page.getByLabel("Nombre").fill(nombre);
  await page.getByRole("button", { name: /Añadir ejercicio/ }).click();
  await page.getByRole("dialog").locator("button.compact-row").first().click();
  await page.getByRole("button", { name: "Añadir al borrador" }).click();
  await page.getByRole("button", { name: "Guardar rutina" }).click();
  await expect(page).toHaveURL(/\/rutinas\/\d+\/?$/);
  await page.getByRole("button", { name: "Entrenar", exact: true }).click();

  await expect(page).toHaveURL(/\/entrenamientos\/\d+\/?(\?ejercicio=\d+)?$/);
  await expect(page.getByRole("link", { name: "Salir del entrenamiento" })).toBeVisible();
  await expect(page.getByRole("navigation", { name: "Principal" })).toHaveCount(0);
  await expect(page.locator("button.account-trigger")).toHaveCount(0);

  await page.getByRole("spinbutton", { name: "kg" }).fill("60");
  await page.getByRole("spinbutton", { name: "Reps" }).fill("10");
  await page.getByRole("button", { name: "Registrar serie" }).click();

  await expect(page.getByRole("timer")).toBeVisible();
  await page.screenshot({ path: test.info().outputPath("entrenar-foco.png") });
  await page.getByRole("button", { name: "Saltar" }).click();
  await expect(page.getByRole("timer")).toHaveCount(0);

  await page.getByRole("button", { name: "Terminar entrenamiento" }).click();

  await expect(page).toHaveURL(/\/entrenamientos\/\d+\/cierre\/?$/);
  await expect(page).toHaveURL(/\/entrenamientos\/\d+\/cierre\/?$/);
  await expect(page.getByText("Entrenamiento terminado")).toBeVisible();
  await expect(page.getByText("en 1 ejercicio")).toBeVisible();
  await expect(page.getByText("Tonelaje")).toBeVisible();
  await expect(page.getByText("Lo que has trabajado")).toBeVisible();
  expect(quejas).toEqual([]);

  const sesion = new URL(page.url()).pathname.match(/\/entrenamientos\/(\d+)\//)![1];
  await page.goto("/entrenamientos/");
  await expect(
    page.locator(`a[href="/entrenamientos/${sesion}/cierre/"]`),
  ).toBeVisible();

  await page.goto("/plan/");
  await page
    .getByRole("region", { name: "Tus rutinas" })
    .getByRole("link", { name: new RegExp(nombre) })
    .click();
  await page.getByRole("button", { name: "Eliminar rutina", exact: true }).click();
  await page.getByRole("button", { name: /^Sí, eliminar/ }).click();
  await expect(page).toHaveURL(/\/plan\/?$/);
});

test("progreso: el calendario, el mapa y las métricas que se elijan", async ({ page }) => {
  const quejas = vigilarLaConsola(page);
  await enInicio(page);

  await page.goto("/progreso/");
  await expect(page.getByRole("heading", { name: "Progreso", level: 1 })).toBeVisible();

  const calendario = page.locator(".cal-scroll");
  await expect(calendario).toBeVisible();
  const desplazamiento = await calendario.evaluate(
    (nodo) => nodo.scrollWidth - nodo.clientWidth - nodo.scrollLeft,
  );
  expect(desplazamiento).toBeLessThan(2);

  await page.getByRole("tab", { name: "Cuerpo" }).click();
  await expect(page.locator("svg.body-map").first()).toBeVisible();
  await expect(page.locator("svg.body-map [role='button']")).toHaveCount(0);

  await page.getByRole("link", { name: "Elegir métricas" }).click();
  await expect(page).toHaveURL(/\/metricas\/?$/);
  const casillas = page.getByRole("checkbox");
  await expect(casillas.first()).toBeVisible();

  const cuantas = await casillas.count();
  for (let i = 1; i < cuantas; i++) {
    if (await casillas.nth(i).isChecked()) await casillas.nth(i).uncheck();
  }
  await casillas.first().check();
  const elegida = (
    await page.locator("label:has(input:checked) span.title-sm").textContent()
  )?.trim();

  await page.getByRole("button", { name: "Guardar mi panel" }).click();

  await expect(page).toHaveURL(/\/progreso\/\?vista=metricas$/);
  const panel = page.locator(".insight-card").filter({ hasText: elegida ?? "" });
  await expect(panel).toHaveCount(1);
  expect(quejas).toEqual([]);

  await page.goto("/metricas/");
  const todas = page.getByRole("checkbox");
  for (let i = 0; i < (await todas.count()); i++) await todas.nth(i).check();
  await page.getByRole("button", { name: "Guardar mi panel" }).click();
  await expect(page).toHaveURL(/\/progreso\/\?vista=metricas$/);
});

test("la IA: el formulario de generar y el análisis se pintan sin quejas", async ({ page }) => {
  const quejas = vigilarLaConsola(page);
  await enInicio(page);

  await page.goto("/ia/generar/");
  await expect(page.getByRole("heading", { name: "Generar rutina", level: 1 })).toBeVisible();
  await expect(page.getByText(/nunca tu fecha de nacimiento/)).toBeVisible();
  await expect(page.getByRole("button", { name: /^Lunes/ })).toBeVisible();
  await page.getByRole("button", { name: /^Lunes/ }).click();
  await expect(page.getByRole("dialog", { name: "Lunes" })).toBeVisible();
  await page.keyboard.press("Escape");

  await page.goto("/ia/analisis/");
  await expect(
    page.getByRole("heading", { name: "Análisis de progreso", level: 1 }),
  ).toBeVisible();

  expect(quejas).toEqual([]);
});

test("el panel de gestión: las cuatro áreas se pintan y la clave no se ve", async ({ page }) => {
  const quejas = vigilarLaConsola(page);
  await enInicio(page);

  await page.goto("/gestion/");
  await expect(page.getByRole("heading", { name: "Resumen", level: 1 })).toBeVisible();

  const secciones: [string, string][] = [
    ["/gestion/ia/", "Configuración"],
    ["/gestion/generaciones/", "Generaciones"],
    ["/gestion/usuarios/", "Usuarios"],
    ["/gestion/catalogo/", "Catálogo y métricas"],
  ];
  for (const [ruta, titulo] of secciones) {
    await page.goto(ruta);
    await expect(page.getByRole("heading", { name: titulo, level: 1 })).toBeVisible();
  }

  await page.goto("/gestion/ia/");
  await expect(page.getByLabel("Cambiar la clave").first()).toHaveValue("");
  await expect(page.locator("dd").filter({ hasText: /···/ }).first()).toBeVisible();

  await page.goto("/gestion/usuarios/");
  await expect(page.getByRole("table")).toBeVisible();
  const respuesta = await page.request.get("/api/gestion/usuarios/");
  const cuerpo = await respuesta.text();
  for (const campo of ["birth_date", "height_cm", "injuries_notes", "target_weight_kg"]) {
    expect(cuerpo).not.toContain(campo);
  }

  expect(quejas).toEqual([]);
});

test("el perfil se edita y recuerda qué se manda a la IA", async ({ page }) => {
  const quejas = vigilarLaConsola(page);
  await enInicio(page);

  await page.goto("/perfil/");
  await expect(page.getByRole("heading", { name: "Tu perfil", level: 1 })).toBeVisible();
  await page.getByRole("tab", { name: "Salud" }).click();
  await expect(page.getByText(/nunca tu fecha de nacimiento/)).toBeVisible();

  await page.getByRole("tab", { name: "Entrenamiento" }).click();
  const dias = page.getByLabel("Días por semana");
  const antes = await dias.inputValue();
  const nuevo = antes === "4" ? "3" : "4";
  await dias.fill(nuevo);
  await page.getByRole("button", { name: "Guardar cambios" }).click();
  await expect(page.getByText("Perfil actualizado.")).toBeVisible();
  await page.reload();
  await expect(page.getByLabel("Días por semana")).toHaveValue(nuevo);

  await page.goto("/perfil/eliminar/");
  const borrar = page.getByRole("button", { name: "Sí, eliminar mi cuenta" });
  await expect(borrar).toBeDisabled();
  await page.getByLabel(/para confirmar/).fill("e2e");
  await expect(borrar).toBeEnabled();

  expect(quejas).toEqual([]);

  await page.goto("/perfil/?vista=entrenamiento");
  await page.getByLabel("Días por semana").fill(antes);
  await page.getByRole("button", { name: "Guardar cambios" }).click();
  await expect(page.getByText("Perfil actualizado.")).toBeVisible();
});

test("la PWA: manifiesto válido, iconos que existen y service worker registrado", async ({
  page,
}) => {
  const quejas = vigilarLaConsola(page);
  await enInicio(page);

  await expect(page.locator('link[rel="manifest"]')).toHaveAttribute(
    "href",
    "/manifest.webmanifest",
  );

  const manifiesto = await page.request.get("/manifest.webmanifest");
  expect(manifiesto.headers()["content-type"]).toContain("application/manifest+json");
  const datos = await manifiesto.json();
  expect(datos.display).toBe("standalone");
  expect(datos.start_url).toBe("/");

  const tamanos = datos.icons.map((icono: { sizes: string }) => icono.sizes);
  expect(tamanos).toContain("192x192");
  expect(tamanos).toContain("512x512");
  expect(datos.icons.some((i: { purpose: string }) => i.purpose === "maskable")).toBe(true);

  expect(datos.id).toBe("/");
  const atajos = datos.shortcuts.flatMap((atajo: { icons: { src: string }[] }) => atajo.icons);
  for (const icono of [...datos.icons, ...atajos]) {
    const respuesta = await page.request.get(icono.src);
    expect(respuesta.status(), `${icono.src} no existe`).toBe(200);
  }

  await page.evaluate(() => navigator.serviceWorker.ready);
  const registrado = await page.evaluate(async () => {
    const registro = await navigator.serviceWorker.getRegistration("/");
    return registro?.scope ?? null;
  });
  expect(registrado).toContain("localhost:8000/");

  await page.reload();
  await expect(page.getByRole("heading", { name: "Tu semana", level: 1 })).toBeVisible();
  expect(await page.evaluate(() => navigator.serviceWorker.controller !== null)).toBe(true);

  const guardadas = await page.evaluate(async () => {
    const urls: string[] = [];
    for (const nombre of await caches.keys()) {
      for (const peticion of await (await caches.open(nombre)).keys()) urls.push(peticion.url);
    }
    return urls;
  });
  expect(guardadas.some((url) => url.includes("/static/spa/assets/"))).toBe(true);
  expect(guardadas.some((url) => url.endsWith("/__cascara__"))).toBe(true);
  expect(guardadas.filter((url) => new URL(url).pathname.startsWith("/api/"))).toEqual([]);

  expect(quejas).toEqual([]);
});

test("sin red, la aplicación abre y dice que no hay conexión", async ({ page, context }) => {
  await enInicio(page);
  await page.evaluate(() => navigator.serviceWorker.ready);
  await page.reload();
  await expect(page.getByRole("heading", { name: "Tu semana", level: 1 })).toBeVisible();

  await context.setOffline(true);
  await page.goto("/progreso/");

  await expect(page.getByRole("heading", { name: "Sin conexión", level: 1 })).toBeVisible();
  await expect(page).toHaveURL(/\/progreso\/$/);

  await context.setOffline(false);
  await page.getByRole("button", { name: "Reintentar" }).click({ timeout: 2_000 }).catch(() => {});
  await expect(page.getByRole("heading", { name: "Progreso", level: 1 })).toBeVisible();
});

test("la bandeja de avisos se abre y dice lo que hay", async ({ page }) => {
  const quejas = vigilarLaConsola(page);
  await enInicio(page);

  await page.goto("/notificaciones/");

  await expect(page.getByRole("heading", { name: "Notificaciones", level: 1 })).toBeVisible();
  expect(quejas).toEqual([]);
});

test("la guía de estilos se pinta dentro del marco y sin quejas del navegador", async ({
  page,
}) => {
  const quejas = vigilarLaConsola(page);
  await enInicio(page);

  await page.goto("/estilos/");

  await expect(page.getByRole("heading", { name: "Guía de estilos", level: 1 })).toBeVisible();
  await expect(page.getByRole("navigation", { name: "Principal" }).first()).toBeVisible();
  expect(quejas).toEqual([]);
});

test("el CSS del sistema de diseño llega de verdad", async ({ page }) => {
  await enInicio(page);
  await page.goto("/estilos/");

  const fondo = () =>
    page.locator("body").evaluate((nodo) => getComputedStyle(nodo).backgroundColor);

  await page.emulateMedia({ colorScheme: "light" });
  await expect.poll(fondo).toBe("rgb(242, 242, 247)");
  await page.emulateMedia({ colorScheme: "dark" });
  await expect.poll(fondo).toBe("rgb(0, 0, 0)");
});

test("la tipografía autoalojada se aplica", async ({ page }) => {
  await enInicio(page);
  await page.goto("/estilos/");
  await expect(page.getByRole("heading", { name: "Guía de estilos", level: 1 })).toBeVisible();

  const cargadas = await page.evaluate(async () => {
    await document.fonts.ready;
    return [...document.fonts].filter((f) => f.status === "loaded").map((f) => f.family);
  });

  expect(cargadas).toContain("Inter");

  const anchos = await page.evaluate(() => {
    const medir = (texto: string) => {
      const cifra = document.createElement("span");
      cifra.className = "metric-md";
      cifra.textContent = texto;
      document.body.append(cifra);
      const ancho = cifra.getBoundingClientRect().width;
      cifra.remove();
      return ancho;
    };
    return [medir("111"), medir("888")];
  });
  expect(anchos[0]).toBeCloseTo(anchos[1]!, 1);
});

test("conmutar el tema cambia los colores, se recuerda y «Sistema» sigue al teléfono", async ({
  page,
}) => {
  await enInicio(page);
  await page.goto("/estilos/");
  const tema = page.getByRole("main").getByRole("group", { name: "Tema de la interfaz" });

  await tema.getByRole("button", { name: "Oscuro" }).click();

  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await expect(tema.getByRole("button", { name: "Oscuro" })).toHaveAttribute(
    "aria-pressed",
    "true",
  );

  await tema.getByRole("button", { name: "Sistema" }).click();
  await page.emulateMedia({ colorScheme: "light" });
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  await page.emulateMedia({ colorScheme: "dark" });
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await page.emulateMedia({ colorScheme: "light" });
});

test("salir cierra la sesión y lo dice", async ({ page }) => {
  await page.context().clearCookies();
  await page.goto("/entrar/");
  await page.getByLabel("Usuario").fill(USUARIO);
  await page.getByLabel("Contraseña").fill(CLAVE);
  await page.getByRole("button", { name: "Entrar" }).click();
  await page.waitForURL("http://localhost:8000/");

  await page.goto("/estilos/");
  await page.evaluate(() => navigator.serviceWorker.ready);
  await page.locator("button.account-trigger:visible").click();
  await page.getByRole("dialog").getByRole("button", { name: "Cerrar sesión" }).click();

  await expect(page).toHaveURL(/\/sesion-cerrada\/?$/);
  await expect(page.getByRole("heading", { name: "Sesión cerrada", level: 1 })).toBeVisible();
  await expect
    .poll(() =>
      page.evaluate(async () => (await caches.keys()).filter((n) => n.startsWith("gym-"))),
    )
    .toEqual([]);
  await page.goto("/estilos/");
  await expect(page).toHaveURL(/\/entrar\//);
});
