import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { Panel } from "./Panel";

function hoja() {
  return render(
    <Panel titulo="Añadir ejercicio" onCerrar={() => {}}>
      <input aria-label="Buscar ejercicio" data-autofocus />
    </Panel>,
  );
}

function pantallaTactil(tactil: boolean) {
  vi.stubGlobal(
    "matchMedia",
    (consulta: string) => ({ matches: tactil && consulta === "(pointer: coarse)", media: consulta }),
  );
}

describe("Panel", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("con ratón abre con el foco en el campo marcado", () => {
    pantallaTactil(false);
    hoja();
    expect(screen.getByLabelText("Buscar ejercicio")).toHaveFocus();
  });

  it("en una pantalla táctil no abre el teclado: el foco va al título", () => {
    pantallaTactil(true);
    hoja();
    expect(screen.getByRole("heading", { name: "Añadir ejercicio" })).toHaveFocus();
    expect(screen.getByLabelText("Buscar ejercicio")).not.toHaveFocus();
  });

  it("se ajusta a la zona visible cuando aparece el teclado", () => {
    const visible = Object.assign(new EventTarget(), { height: 844, offsetTop: 0 });
    vi.stubGlobal("visualViewport", visible);
    const { unmount } = hoja();
    const dialogo = screen.getByRole("dialog", { hidden: true });
    expect(dialogo.style.getPropertyValue("--vv-alto")).toBe("844px");

    visible.height = 470;
    visible.offsetTop = 12;
    visible.dispatchEvent(new Event("resize"));
    expect(dialogo.style.getPropertyValue("--vv-alto")).toBe("470px");
    expect(dialogo.style.getPropertyValue("--vv-arriba")).toBe("12px");

    unmount();
    visible.height = 300;
    visible.dispatchEvent(new Event("resize"));
    expect(dialogo.style.getPropertyValue("--vv-alto")).toBe("470px");
  });
});
