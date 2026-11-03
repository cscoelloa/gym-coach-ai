import { screen, within } from "@testing-library/react";
import { userEvent } from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { act } from "react";
import { beforeEach, describe, expect, it } from "vitest";

import type { UsuarioDeSesion } from "@/api/sesion";
import { poner, quitar } from "@/lib/descanso";
import { montar } from "@/test/montar";
import { servidor } from "@/test/servidor";

import { AppShell } from "./AppShell";
import { Cabecera } from "./Cabecera";
import { DESTINOS, padreDe } from "./navegacion";

const ANA: UsuarioDeSesion = { id: 1, username: "ana", first_name: "Ana", is_staff: false };
const STAFF: UsuarioDeSesion = { ...ANA, username: "admin", is_staff: true };

function barras() {
  const [lateral, pestanas] = screen.getAllByRole("navigation", { name: "Principal" });
  return { lateral: lateral!, pestanas: pestanas! };
}

function conAvisosSinLeer(cuantos: number) {
  servidor.use(
    http.get("/api/notificaciones/", () =>
      HttpResponse.json({ count: cuantos, next: null, previous: null, results: [] }),
    ),
  );
}

beforeEach(() => conAvisosSinLeer(0));

describe("AppShell", () => {
  it("pinta los cinco destinos en las dos barras", () => {
    montar(
      <AppShell usuario={ANA}>
        <p>contenido</p>
      </AppShell>,
    );

    const { lateral, pestanas } = barras();
    for (const destino of DESTINOS) {
      expect(within(lateral).getByRole("link", { name: destino.etiqueta })).toBeVisible();
      expect(within(pestanas).getByRole("link", { name: destino.etiqueta })).toBeVisible();
    }
  });

  it("marca el destino actual, y solo ese", () => {
    montar(
      <AppShell usuario={ANA}>
        <p>contenido</p>
      </AppShell>,
      { ruta: "/plan/" },
    );

    const actuales = screen
      .getAllByRole("link")
      .filter((enlace) => enlace.getAttribute("aria-current") === "page");

    expect(actuales).toHaveLength(2);
    expect(actuales.every((enlace) => enlace.textContent?.includes("Plan"))).toBe(true);
  });

  it("Inicio no se queda encendido en todas las pantallas", () => {
    montar(
      <AppShell usuario={ANA}>
        <p>contenido</p>
      </AppShell>,
      { ruta: "/ejercicios/" },
    );

    const { lateral } = barras();
    expect(within(lateral).getByRole("link", { name: "Inicio" })).not.toHaveAttribute(
      "aria-current",
    );
  });

  it("las secciones del equipo no salen para quien no es staff", () => {
    montar(
      <AppShell usuario={ANA}>
        <p>contenido</p>
      </AppShell>,
    );

    expect(screen.queryByRole("link", { name: "Gestión" })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /Admin/ })).not.toBeInTheDocument();
  });

  it("y sí cuando lo es: el panel y el admin de Django, que se conserva", () => {
    montar(
      <AppShell usuario={STAFF}>
        <p>contenido</p>
      </AppShell>,
    );

    expect(screen.getByRole("link", { name: "Gestión" })).toHaveAttribute("href", "/gestion/");
    expect(screen.getByRole("link", { name: "Admin de Django" })).toBeVisible();
  });

  it("enseña cuántos avisos hay sin leer", async () => {
    conAvisosSinLeer(3);

    montar(
      <AppShell usuario={ANA}>
        <p>contenido</p>
      </AppShell>,
    );

    const insignias = await screen.findAllByText("3");
    expect(insignias).toHaveLength(2);

    const avisos = screen.getAllByRole("link", { name: /Avisos/ });
    expect(avisos).toHaveLength(2);
    for (const enlace of avisos) expect(enlace).toHaveAccessibleName(/3 sin leer/);
  });

  it("sin avisos pendientes no hay insignia", () => {
    montar(
      <AppShell usuario={ANA}>
        <p>contenido</p>
      </AppShell>,
    );

    for (const enlace of screen.getAllByRole("link", { name: "Avisos" })) {
      expect(enlace).not.toHaveTextContent(/\d/);
    }
  });

  it("salir es un botón, no un enlace", () => {
    montar(
      <AppShell usuario={ANA}>
        <p>contenido</p>
      </AppShell>,
    );

    expect(screen.getAllByRole("button", { name: "Cuenta" })).toHaveLength(2);
    expect(screen.queryByRole("link", { name: "Salir" })).not.toBeInTheDocument();
  });
});

describe("La barra superior", () => {
  it("no tiene «atrás» en los cinco destinos: a esos se llega por la barra", () => {
    for (const destino of DESTINOS) {
      const { unmount } = montar(
        <AppShell usuario={ANA}>
          <p>contenido</p>
        </AppShell>,
        { ruta: destino.url },
      );
      expect(screen.queryByRole("button", { name: /Atrás|Inicio|Plan/ })).not.toBeInTheDocument();
      unmount();
    }
  });

  it("en una pantalla de segundo nivel sin historial, vuelve al padre", async () => {
    montar(
      <AppShell usuario={ANA}>
        <p>contenido</p>
      </AppShell>,
      { ruta: "/rutinas/4/" },
    );

    const atras = screen.getByRole("button", { name: "Plan" });
    await userEvent.click(atras);

    const actuales = screen
      .getAllByRole("link")
      .filter((enlace) => enlace.getAttribute("aria-current") === "page");
    expect(actuales.every((enlace) => enlace.textContent?.includes("Plan"))).toBe(true);
  });

  it("no repite el título como encabezado", () => {
    const { container } = montar(
      <AppShell usuario={ANA}>
        <Cabecera titulo="Tu plan" />
      </AppShell>,
      { ruta: "/plan/" },
    );

    expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
    const barra = container.querySelector<HTMLElement>(".app-bar")!;
    expect(within(barra).queryByRole("heading")).not.toBeInTheDocument();
  });

  it("en gestión no hay barra de pestañas: de ahí no se salta a entrenar, se sale", () => {
    montar(
      <AppShell usuario={STAFF} contexto="gestion">
        <p>contenido</p>
      </AppShell>,
      { ruta: "/gestion/ia/" },
    );

    expect(screen.getAllByRole("navigation", { name: "Principal" })).toHaveLength(1);
    expect(screen.getByRole("button", { name: "Gestión" })).toBeVisible();
  });
});

describe("El descanso fuera del modo foco", () => {
  it("la barra lo enseña y un toque vuelve a ese entrenamiento", () => {
    act(() => poner(5, 72));

    montar(
      <AppShell usuario={ANA}>
        <p>contenido</p>
      </AppShell>,
    );

    const volver = screen.getByRole("link", { name: /Descanso: quedan 1:12/ });
    expect(volver).toHaveAttribute("href", "/entrenamientos/5/");
  });

  it("sin descanso no hay nada", () => {
    montar(
      <AppShell usuario={ANA}>
        <p>contenido</p>
      </AppShell>,
    );

    expect(screen.queryByRole("link", { name: /Descanso/ })).not.toBeInTheDocument();
  });

  it("al saltarlo o acabarse, se va", () => {
    act(() => poner(5, 72));
    montar(
      <AppShell usuario={ANA}>
        <p>contenido</p>
      </AppShell>,
    );

    act(() => quitar(5));

    expect(screen.queryByRole("link", { name: /Descanso/ })).not.toBeInTheDocument();
  });
});

describe("padreDe", () => {
  it.each([
    ["/rutinas/4/", "/plan/"],
    ["/plan/dia/1/", "/plan/"],
    ["/entrenamientos/9/cierre/", "/entrenamientos/"],
    ["/ejercicios/press-banca/", "/ejercicios/"],
    ["/perfil/eliminar/", "/perfil/"],
    ["/metricas/", "/progreso/"],
    ["/gestion/usuarios/", "/gestion/"],
    ["/gestion/", "/"],
    ["/peso/", "/"],
  ])("%s cuelga de %s", (camino, padre) => {
    expect(padreDe(camino).url).toBe(padre);
  });
});
