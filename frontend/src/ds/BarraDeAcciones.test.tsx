import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { BarraDeAcciones } from "./BarraDeAcciones";

describe("BarraDeAcciones", () => {
  afterEach(() => vi.restoreAllMocks());

  it("deja su altura en --acciones-h para que el contenido no quede debajo, y la quita al irse", () => {
    vi.spyOn(HTMLElement.prototype, "offsetHeight", "get").mockReturnValue(92);
    const { unmount } = render(
      <BarraDeAcciones>
        <span role="status">Cambios sin guardar</span>
        <button type="button">Guardar rutina</button>
      </BarraDeAcciones>,
    );

    expect(screen.getByRole("status").parentElement).toHaveClass("editor-actions");
    expect(document.documentElement.style.getPropertyValue("--acciones-h")).toBe("92px");

    unmount();
    expect(document.documentElement.style.getPropertyValue("--acciones-h")).toBe("");
  });
});
