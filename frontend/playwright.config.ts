import { defineConfig, devices } from "@playwright/test";

import { ESTADO_DE_SESION } from "./e2e/cuenta";

const CANAL = process.env.PLAYWRIGHT_CHANNEL || "chrome";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  reporter: [["list"]],

  use: {
    baseURL: "http://localhost:8000",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    colorScheme: "light",
  },

  projects: [
    {
      name: "acceso",
      testMatch: /acceso\.setup\.ts/,
      use: { ...devices["Desktop Chrome"], channel: CANAL },
    },
    {
      name: "escritorio",
      use: {
        ...devices["Desktop Chrome"],
        channel: CANAL,
        storageState: ESTADO_DE_SESION,
      },
      dependencies: ["acceso"],
    },
    {
      name: "movil",
      use: {
        ...devices["Pixel 7"],
        channel: CANAL,
        storageState: ESTADO_DE_SESION,
      },
      dependencies: ["acceso"],
    },
  ],

  webServer: {
    command:
      "python ../manage.py runserver 8000 --noreload --skip-checks",
    url: "http://localhost:8000/entrar/",
    reuseExistingServer: true,
    timeout: 60_000,
    env: {
      DJANGO_SETTINGS_MODULE: "config.settings.dev",
      VITE_DEV_SERVER_URL: "",
    },
  },
});
