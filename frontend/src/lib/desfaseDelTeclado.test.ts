import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { medirDesfase, vigilarElDesfaseDelTeclado } from "./desfaseDelTeclado";

class VistaFalsa extends EventTarget {
  offsetTop = 0;
  scale = 1;
}

let vista: VistaFalsa;
let parar: () => void;

function desfase() {
  return document.documentElement.style.getPropertyValue("--desfase-teclado");
}

function campo() {
  const entrada = document.createElement("input");
  document.body.append(entrada);
  return entrada;
}

beforeEach(() => {
  vi.useFakeTimers();
  vista = new VistaFalsa();
  Object.defineProperty(window, "visualViewport", { value: vista, configurable: true });
  parar = vigilarElDesfaseDelTeclado();
});

afterEach(() => {
  parar();
  document.body.replaceChildren();
  Object.defineProperty(window, "visualViewport", { value: undefined, configurable: true });
  vi.useRealTimers();
});

describe("el desfase que deja el teclado de iOS 26", () => {
  it("si el teclado se cierra y la vista se queda corrida, las barras se recolocan", () => {
    const entrada = campo();
    entrada.focus();
    vista.offsetTop = 266;
    vista.dispatchEvent(new Event("resize"));
    expect(desfase()).toBe("");

    entrada.blur();
    vi.advanceTimersByTime(350);

    expect(desfase()).toBe("266px");
  });

  it("con el teclado abierto no se toca nada: iOS ya coloca el campo", () => {
    const entrada = campo();
    vista.offsetTop = 120;
    vista.dispatchEvent(new Event("scroll"));
    expect(desfase()).toBe("120px");

    entrada.focus();

    expect(desfase()).toBe("0px");
  });

  it("cuando la vista vuelve a su sitio, el desfase vuelve a cero", () => {
    vista.offsetTop = 80;
    vista.dispatchEvent(new Event("scroll"));
    vista.offsetTop = 0;
    vista.dispatchEvent(new Event("scroll"));

    expect(desfase()).toBe("0px");
  });

  it("con zoom de pellizco el desfase es legítimo y no se compensa", () => {
    vista.scale = 2;
    vista.offsetTop = 300;
    vista.dispatchEvent(new Event("resize"));
    vi.advanceTimersByTime(350);

    expect(desfase()).toBe("");
  });

  it("al parar deja el documento como estaba", () => {
    vista.offsetTop = 40;
    vista.dispatchEvent(new Event("scroll"));
    parar();

    expect(desfase()).toBe("");
  });
});

describe("medirDesfase", () => {
  it("sin visualViewport no hay nada que medir", () => {
    expect(medirDesfase(undefined)).toBe(0);
  });

  it("nunca devuelve un desfase negativo", () => {
    expect(medirDesfase(Object.assign(new VistaFalsa(), { offsetTop: -12 }) as unknown as VisualViewport)).toBe(0);
  });
});
