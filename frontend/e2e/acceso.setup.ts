import { expect, test as setup } from "@playwright/test";

import { CLAVE, ESTADO_DE_SESION, USUARIO } from "./cuenta";

setup("entrar una vez y guardar la sesión", async ({ page }) => {
  await page.goto("/entrar/");
  await page.getByLabel("Usuario").fill(USUARIO);
  await page.getByLabel("Contraseña").fill(CLAVE);
  await page.getByRole("button", { name: "Entrar" }).click();

  await page.waitForURL("http://localhost:8000/");
  await expect(page.getByRole("heading", { name: "Tu semana", level: 1 })).toBeVisible();

  await page.context().storageState({ path: ESTADO_DE_SESION });
});
