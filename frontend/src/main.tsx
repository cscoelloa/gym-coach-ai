import { onlineManager, QueryClientProvider } from "@tanstack/react-query";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { createBrowserRouter, RouterProvider } from "react-router";

import "../../assets/app.css";

import { App } from "./App";
import { LimiteDeError } from "./ds/LimiteDeError";
import { crearCache } from "./lib/cache";
import { vigilarElDesfaseDelTeclado } from "./lib/desfaseDelTeclado";
import { escucharInstalacion } from "./lib/instalar";
import { registrarServiceWorker } from "./lib/pwa";

const cache = crearCache();

const raiz = document.getElementById("root");

if (!raiz) {
  throw new Error("No existe #root: ¿está sirviéndose templates/spa.html?");
}

escucharInstalacion();
registrarServiceWorker();
vigilarElDesfaseDelTeclado();

onlineManager.setOnline(navigator.onLine);

createRoot(raiz).render(
  <StrictMode>
    <LimiteDeError>
      <QueryClientProvider client={cache}>
        <RouterProvider router={createBrowserRouter([{ path: "*", element: <App /> }])} />
      </QueryClientProvider>
    </LimiteDeError>
  </StrictMode>,
);
