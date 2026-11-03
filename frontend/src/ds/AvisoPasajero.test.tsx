import { act, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { AvisoPasajero } from "./AvisoPasajero";

describe("AvisoPasajero", () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it("aparece al llegar la marca y se va sola a los 4 s", () => {
    const { rerender } = render(<AvisoPasajero marca={false}>Peso registrado.</AvisoPasajero>);
    expect(screen.queryByText("Peso registrado.")).not.toBeInTheDocument();

    rerender(<AvisoPasajero marca={1000}>Peso registrado.</AvisoPasajero>);
    expect(screen.getByRole("status")).toHaveTextContent("Peso registrado.");

    act(() => vi.advanceTimersByTime(3900));
    expect(screen.getByText("Peso registrado.")).toBeInTheDocument();

    act(() => vi.advanceTimersByTime(200));
    expect(screen.queryByText("Peso registrado.")).not.toBeInTheDocument();
  });

  it("un guardado nuevo la vuelve a enseñar y reinicia el tiempo", () => {
    const { rerender } = render(<AvisoPasajero marca={1000}>Guardado.</AvisoPasajero>);
    act(() => vi.advanceTimersByTime(5000));
    expect(screen.queryByText("Guardado.")).not.toBeInTheDocument();

    rerender(<AvisoPasajero marca={2000}>Guardado.</AvisoPasajero>);
    expect(screen.getByText("Guardado.")).toBeInTheDocument();
    act(() => vi.advanceTimersByTime(3000));
    expect(screen.getByText("Guardado.")).toBeInTheDocument();
  });

  it("se quita en el acto si arranca otro envío", () => {
    const { rerender } = render(<AvisoPasajero marca={1000}>Guardado.</AvisoPasajero>);
    rerender(<AvisoPasajero marca={false}>Guardado.</AvisoPasajero>);
    expect(screen.queryByText("Guardado.")).not.toBeInTheDocument();
  });

  it("respeta una duración más larga para lo que trae datos que leer", () => {
    render(
      <AvisoPasajero marca={1} duracion={10000}>
        Conexión correcta.
      </AvisoPasajero>,
    );
    act(() => vi.advanceTimersByTime(9000));
    expect(screen.getByText("Conexión correcta.")).toBeInTheDocument();
    act(() => vi.advanceTimersByTime(1100));
    expect(screen.queryByText("Conexión correcta.")).not.toBeInTheDocument();
  });
});
