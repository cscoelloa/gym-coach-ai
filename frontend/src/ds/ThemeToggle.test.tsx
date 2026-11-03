import { render, screen, waitFor } from "@testing-library/react";
import { userEvent } from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ThemeToggle } from "./ThemeToggle";

afterEach(() => {
  document.documentElement.removeAttribute("data-theme");
  document.documentElement.removeAttribute("data-theme-pref");
  delete window.setTheme;
});

function pulsado(nombre: RegExp) {
  return screen.getByRole("button", { name: nombre });
}

describe("ThemeToggle", () => {
  it("marca la preferencia que dice el atributo de <html>", () => {
    document.documentElement.setAttribute("data-theme", "light");
    document.documentElement.setAttribute("data-theme-pref", "light");

    render(<ThemeToggle />);

    expect(pulsado(/claro/i)).toHaveAttribute("aria-pressed", "true");
    expect(pulsado(/oscuro/i)).toHaveAttribute("aria-pressed", "false");
    expect(pulsado(/sistema/i)).toHaveAttribute("aria-pressed", "false");
  });

  it("arranca siguiendo al sistema cuando no hay preferencia", () => {
    render(<ThemeToggle />);

    expect(pulsado(/sistema/i)).toHaveAttribute("aria-pressed", "true");
  });

  it("con «Sistema» y el teléfono en oscuro, marca «Sistema» y no «Oscuro»", () => {
    document.documentElement.setAttribute("data-theme", "dark");
    document.documentElement.setAttribute("data-theme-pref", "system");

    render(<ThemeToggle />);

    expect(pulsado(/sistema/i)).toHaveAttribute("aria-pressed", "true");
    expect(pulsado(/oscuro/i)).toHaveAttribute("aria-pressed", "false");
  });

  it("delega el cambio en theme.js, que es quien lo persiste", async () => {
    const setTheme = vi.fn();
    window.setTheme = setTheme;
    render(<ThemeToggle />);

    await userEvent.click(pulsado(/oscuro/i));

    expect(setTheme).toHaveBeenCalledWith("dark");
  });

  it("sigue conmutando aunque theme.js no esté", async () => {
    render(<ThemeToggle />);

    await userEvent.click(pulsado(/oscuro/i));

    expect(document.documentElement).toHaveAttribute("data-theme", "dark");
    expect(document.documentElement).toHaveAttribute("data-theme-pref", "dark");
  });

  it("sin theme.js, «Sistema» resuelve al claro si no se puede preguntar al teléfono", async () => {
    document.documentElement.setAttribute("data-theme", "dark");
    document.documentElement.setAttribute("data-theme-pref", "dark");
    render(<ThemeToggle />);

    await userEvent.click(pulsado(/sistema/i));

    expect(document.documentElement).toHaveAttribute("data-theme", "light");
    expect(document.documentElement).toHaveAttribute("data-theme-pref", "system");
  });

  it("se entera si la preferencia cambia por fuera", async () => {
    render(<ThemeToggle />);

    document.documentElement.setAttribute("data-theme-pref", "light");

    await waitFor(() => expect(pulsado(/claro/i)).toHaveAttribute("aria-pressed", "true"));
  });
});
