import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { Panel } from "./Panel";

function hoja(onCerrar: () => void = () => {}) {
  return render(
    <Panel titulo="Añadir ejercicio" onCerrar={onCerrar}>
      <input aria-label="Buscar ejercicio" data-autofocus />
      <p>Lista</p>
    </Panel>,
  );
}

function medios(...activas: string[]) {
  vi.stubGlobal("matchMedia", (consulta: string) => ({
    matches: activas.includes(consulta),
    media: consulta,
  }));
}

const TACTIL = "(pointer: coarse)";
const MODO_HOJA = "(max-width: 47.99rem)";
const SIN_ANIMACION = "(prefers-reduced-motion: reduce)";

function arrastrar(desde: Element, bajada: number, lateral = 0) {
  fireEvent.touchStart(desde, { touches: [{ clientX: 100, clientY: 100 }] });
  fireEvent.touchMove(desde, { touches: [{ clientX: 100 + lateral / 2, clientY: 100 + bajada / 2 }] });
  fireEvent.touchMove(desde, { touches: [{ clientX: 100 + lateral, clientY: 100 + bajada }] });
  fireEvent.touchEnd(desde, { touches: [] });
}

function dialogo() {
  const elemento = screen.getByRole("dialog", { hidden: true });
  Object.defineProperty(elemento, "offsetHeight", { configurable: true, value: 800 });
  return elemento;
}

describe("Panel", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.useRealTimers();
  });

  it("con ratón abre con el foco en el campo marcado", () => {
    medios();
    hoja();
    expect(screen.getByLabelText("Buscar ejercicio")).toHaveFocus();
  });

  it("en una pantalla táctil no abre el teclado: el foco va al título", () => {
    medios(TACTIL);
    hoja();
    expect(screen.getByRole("heading", { name: "Añadir ejercicio" })).toHaveFocus();
    expect(screen.getByLabelText("Buscar ejercicio")).not.toHaveFocus();
  });

  it("se ajusta a la zona visible cuando aparece el teclado", () => {
    const visible = Object.assign(new EventTarget(), { height: 844, offsetTop: 0 });
    vi.stubGlobal("visualViewport", visible);
    const { unmount } = hoja();
    const elemento = screen.getByRole("dialog", { hidden: true });
    expect(elemento.style.getPropertyValue("--vv-alto")).toBe("844px");

    visible.height = 470;
    visible.offsetTop = 12;
    visible.dispatchEvent(new Event("resize"));
    expect(elemento.style.getPropertyValue("--vv-alto")).toBe("470px");
    expect(elemento.style.getPropertyValue("--vv-arriba")).toBe("12px");

    unmount();
    visible.height = 300;
    visible.dispatchEvent(new Event("resize"));
    expect(elemento.style.getPropertyValue("--vv-alto")).toBe("470px");
  });

  describe("arrastrar hacia abajo", () => {
    it("desde el título, más de un cuarto de la hoja, la cierra", () => {
      medios(TACTIL, MODO_HOJA, SIN_ANIMACION);
      const onCerrar = vi.fn();
      hoja(onCerrar);
      dialogo();

      arrastrar(screen.getByRole("heading", { name: "Añadir ejercicio" }), 260);
      expect(onCerrar).toHaveBeenCalledTimes(1);
    });

    it("con animación, la hoja baja y se cierra al terminar de salir", () => {
      vi.useFakeTimers();
      medios(TACTIL, MODO_HOJA);
      const onCerrar = vi.fn();
      hoja(onCerrar);
      const elemento = dialogo();

      arrastrar(screen.getByText("Lista"), 300);
      expect(elemento.style.translate).toBe("0 832px");
      expect(onCerrar).not.toHaveBeenCalled();

      act(() => vi.advanceTimersByTime(200));
      expect(onCerrar).toHaveBeenCalledTimes(1);
    });

    it("un arrastre corto, hacia arriba o de lado la deja en su sitio", () => {
      medios(TACTIL, MODO_HOJA, SIN_ANIMACION);
      const onCerrar = vi.fn();
      hoja(onCerrar);
      const elemento = dialogo();
      const titulo = screen.getByRole("heading", { name: "Añadir ejercicio" });

      arrastrar(titulo, 30);
      expect(elemento.style.translate).toBe("");
      arrastrar(titulo, -300);
      arrastrar(titulo, 120, 300);
      expect(onCerrar).not.toHaveBeenCalled();
    });

    it("desde la lista desplazada no cierra: es el desplazamiento de la lista", () => {
      medios(TACTIL, MODO_HOJA, SIN_ANIMACION);
      const onCerrar = vi.fn();
      hoja(onCerrar);
      dialogo();
      const cuerpo = screen.getByText("Lista").closest(".panel-body")!;
      Object.defineProperty(cuerpo, "scrollTop", { configurable: true, value: 120 });

      arrastrar(screen.getByText("Lista"), 400);
      expect(onCerrar).not.toHaveBeenCalled();
    });

    it("no empieza en un campo de texto ni en el diálogo centrado de escritorio", () => {
      medios(TACTIL, MODO_HOJA, SIN_ANIMACION);
      const onCerrar = vi.fn();
      const { unmount } = hoja(onCerrar);
      dialogo();
      arrastrar(screen.getByLabelText("Buscar ejercicio"), 400);
      expect(onCerrar).not.toHaveBeenCalled();
      unmount();

      medios(SIN_ANIMACION);
      hoja(onCerrar);
      dialogo();
      arrastrar(screen.getByRole("heading", { name: "Añadir ejercicio" }), 400);
      expect(onCerrar).not.toHaveBeenCalled();
    });
  });
});
