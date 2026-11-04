import { fireEvent, screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { useLocation } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { UsuarioDeSesion } from "@/api/sesion";
import { montar } from "@/test/montar";
import { servidor } from "@/test/servidor";

import { AppShell } from "./AppShell";

const ANA: UsuarioDeSesion = { id: 1, username: "ana", first_name: "Ana", is_staff: false };

function Donde() {
  return <p data-testid="donde">{useLocation().pathname}</p>;
}

function instalada(si: boolean) {
  vi.stubGlobal("matchMedia", (consulta: string) => ({
    matches: si && consulta === "(display-mode: standalone)",
    media: consulta,
  }));
}

function deslizar(desdeX: number, hastaX: number, deltaY = 0) {
  const pagina = screen.getByTestId("donde");
  fireEvent.touchStart(pagina, { touches: [{ clientX: desdeX, clientY: 300 }] });
  fireEvent.touchMove(pagina, {
    touches: [{ clientX: (desdeX + hastaX) / 2, clientY: 300 + deltaY / 2 }],
  });
  fireEvent.touchMove(pagina, { touches: [{ clientX: hastaX, clientY: 300 + deltaY }] });
  fireEvent.touchEnd(pagina, { touches: [] });
}

function enUnaRutina() {
  montar(
    <AppShell usuario={ANA}>
      <Donde />
    </AppShell>,
    { ruta: "/rutinas/3/" },
  );
}

beforeEach(() =>
  servidor.use(
    http.get("/api/notificaciones/", () =>
      HttpResponse.json({ count: 0, next: null, previous: null, results: [] }),
    ),
  ),
);
afterEach(() => vi.unstubAllGlobals());

describe("GestoDeVolver", () => {
  it("en la app instalada, deslizar desde el borde izquierdo vuelve atrás", () => {
    instalada(true);
    enUnaRutina();

    deslizar(4, 420);
    expect(screen.getByTestId("donde")).toHaveTextContent("/plan/");
  });

  it("no hace nada desde el centro, en vertical o con poco recorrido", () => {
    instalada(true);
    enUnaRutina();

    deslizar(300, 900);
    deslizar(4, 30, 400);
    deslizar(4, 30);
    expect(screen.getByTestId("donde")).toHaveTextContent("/rutinas/3/");
  });

  it("en Safari no se activa: ahí el gesto es del sistema", () => {
    instalada(false);
    enUnaRutina();

    deslizar(4, 420);
    expect(screen.getByTestId("donde")).toHaveTextContent("/rutinas/3/");
  });

  it("con una hoja abierta no se activa", () => {
    instalada(true);
    enUnaRutina();
    const hoja = document.createElement("dialog");
    hoja.setAttribute("open", "");
    document.body.append(hoja);

    deslizar(4, 420);
    expect(screen.getByTestId("donde")).toHaveTextContent("/rutinas/3/");
    hoja.remove();
  });

  it("en las pantallas principales no existe", () => {
    instalada(true);
    montar(
      <AppShell usuario={ANA}>
        <Donde />
      </AppShell>,
      { ruta: "/plan/" },
    );

    expect(document.querySelector(".gesto-volver")).toBeNull();
  });
});
