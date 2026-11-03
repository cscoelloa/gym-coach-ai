/// <reference types="vitest/config" />
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

const AQUI = dirname(fileURLToPath(import.meta.url));
const RAIZ = resolve(AQUI, "..");

export default defineConfig(({ command }) => ({
  root: AQUI,

  base: command === "build" ? "/static/spa/" : "/",

  plugins: [tailwindcss(), react()],

  resolve: {
    alias: { "@": resolve(AQUI, "src") },
  },

  server: {
    port: 5173,
    strictPort: true,
    origin: "http://localhost:5173",
    fs: { allow: [RAIZ] },
  },

  build: {
    outDir: resolve(AQUI, "dist"),
    emptyOutDir: true,
    manifest: true,
    rollupOptions: {
      input: resolve(AQUI, "src/main.tsx"),
    },
  },

  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: [resolve(AQUI, "vitest.setup.ts")],
    css: false,
    include: ["src/**/*.{test,spec}.{ts,tsx}"],
  },
}));
