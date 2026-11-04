import { render, screen } from "@testing-library/react";
import { userEvent } from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { Paginacion } from "./Paginacion";

describe("Paginacion", () => {
  it("dice en qué página está y cuántas hay", () => {
    render(<Paginacion pagina={2} total={53} hayAnterior haySiguiente onCambio={() => {}} />);

    expect(screen.getByRole("navigation", { name: "Paginación" })).toHaveTextContent(
      "Página 2 de 53",
    );
  });

  it("avanza y retrocede, y en los extremos no deja seguir", async () => {
    const onCambio = vi.fn();
    const { rerender } = render(
      <Paginacion pagina={1} total={3} hayAnterior={false} haySiguiente onCambio={onCambio} />,
    );

    expect(screen.getByRole("button", { name: "Anterior" })).toBeDisabled();
    await userEvent.click(screen.getByRole("button", { name: "Siguiente" }));
    expect(onCambio).toHaveBeenLastCalledWith(2);

    rerender(<Paginacion pagina={3} total={3} hayAnterior haySiguiente={false} onCambio={onCambio} />);
    expect(screen.getByRole("button", { name: "Siguiente" })).toBeDisabled();
    await userEvent.click(screen.getByRole("button", { name: "Anterior" }));
    expect(onCambio).toHaveBeenLastCalledWith(2);
  });

  it("mientras carga no deja cambiar de página", () => {
    render(<Paginacion pagina={2} total={3} hayAnterior haySiguiente ocupado onCambio={() => {}} />);

    expect(screen.getByRole("button", { name: "Anterior" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Siguiente" })).toBeDisabled();
  });

  it("con una sola página no se pinta", () => {
    render(
      <Paginacion pagina={1} total={1} hayAnterior={false} haySiguiente={false} onCambio={() => {}} />,
    );

    expect(screen.queryByRole("navigation", { name: "Paginación" })).not.toBeInTheDocument();
  });
});
