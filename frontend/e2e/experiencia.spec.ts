import { expect, test } from "@playwright/test";

test("borrador: atrás, Cuenta y recarga protegen cambios; los paneles restauran el foco", async ({ page }) => {
  await page.goto("/plan/");
  await page.getByRole("link", { name: /Nueva/ }).click();
  await page.getByLabel("Nombre").fill("Borrador sin guardar");
  const avisoDeCambios = page.getByRole("dialog", { name: "Cambios sin guardar" });
  await page.goBack();
  await expect(avisoDeCambios.getByRole("heading", { name: "Cambios sin guardar" })).toBeFocused();
  await avisoDeCambios.getByRole("button", { name: "Seguir editando" }).click();
  await expect(avisoDeCambios).toHaveCount(0);
  await expect(page.getByLabel("Nombre")).toHaveValue("Borrador sin guardar");
  await page.locator("button.account-trigger:visible").click();
  const panel = page.getByRole("dialog", { name: "Tu cuenta" });
  await expect(panel.getByRole("button", { name: "Cerrar sesión" })).toBeVisible();
  const peligro = await page.evaluate(() => {
    const muestra = document.createElement("span");
    muestra.style.color = "var(--danger)";
    document.body.append(muestra);
    const color = getComputedStyle(muestra).color;
    muestra.remove();
    return color;
  });
  await expect(panel.getByRole("button", { name: "Cerrar sesión" })).toHaveCSS("color", peligro);
  await panel.getByRole("button", { name: "Cerrar sesión" }).click();
  await expect(avisoDeCambios).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(avisoDeCambios).toHaveCount(0);
  await expect(panel).toBeVisible();
  await expect(panel.getByRole("button", { name: "Cerrar sesión" })).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(panel).toHaveCount(0);
  await expect(page.locator("button.account-trigger:visible")).toBeFocused();
  await page.getByRole("button", { name: /Añadir ejercicio/ }).click();
  const tactil = await page.evaluate(() => matchMedia("(pointer: coarse)").matches);
  await expect(
    tactil
      ? page.getByRole("dialog", { name: "Añadir ejercicio" }).getByRole("heading", { name: "Añadir ejercicio" })
      : page.getByLabel("Buscar ejercicio"),
  ).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("button", { name: /Añadir ejercicio/ })).toBeFocused();
  const recarga = page.waitForEvent("dialog");
  await page.evaluate(() => { setTimeout(() => window.location.reload(), 0); });
  const aviso = await recarga;
  expect(aviso.type()).toBe("beforeunload");
  await aviso.dismiss();
  await expect(page.getByLabel("Nombre")).toHaveValue("Borrador sin guardar");
  await page.getByRole("link", { name: "Cancelar" }).click();
  await avisoDeCambios.getByRole("button", { name: "Salir sin guardar" }).click();
  await expect(page).toHaveURL(/\/plan\/?$/);
});

test("revisión visual en cuatro anchos y ambos temas", async ({ page }, info) => {
  test.skip(info.project.name !== "escritorio", "la revisión visual ya cubre los cuatro anchos");
  test.setTimeout(420_000);
  const errores: string[] = [];
  page.on("pageerror", error => errores.push(error.message));
  for (const width of [375, 390, 768, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    for (const tema of ["dark", "light"] as const) {
      for (const [ruta, nombre] of [
        ["/", "inicio"],
        ["/plan/", "plan"],
        ["/rutinas/nueva/", "editor"],
        ["/entrenamientos/", "entrenar"],
        ["/progreso/", "progreso"],
        ["/peso/", "peso"],
        ["/ejercicios/", "ejercicios"],
        ["/perfil/", "perfil"],
        ["/notificaciones/", "avisos"],
        ["/ia/generar/", "generar"],
      ]) {
        await page.goto(ruta!);
        await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
        await page.evaluate(t => window.setTheme?.(t), tema);
        await page.waitForLoadState("networkidle");
        await page.screenshot({ path: info.outputPath(`${nombre}-${width}-${tema}.png`), fullPage: true, animations: "disabled" });
        expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), `${ruta} ${width} ${tema}`).toBe(true);
      }
      await page.locator("button.account-trigger:visible").click();
      await expect(page.getByRole("dialog").getByRole("button", { name: "Cerrar sesión" })).toBeInViewport();
      await page.screenshot({ path: info.outputPath(`cuenta-${width}-${tema}.png`), animations: "disabled" });
      await page.keyboard.press("Escape");
    }
  }
  expect(errores).toEqual([]);
});
