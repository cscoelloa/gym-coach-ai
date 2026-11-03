import { screen } from "@testing-library/react";
import { userEvent } from "@testing-library/user-event";
import { useLocation } from "react-router";
import { describe, expect, it } from "vitest";

import { montar } from "@/test/montar";

import { Pestanas, useVista } from "./Pestanas";

const VISTAS = ["actividad", "cuerpo", "metricas"] as const;

function Prueba() {
  const [vista, setVista] = useVista(VISTAS);
  const { search } = useLocation();

  return (
    <>
      <Pestanas
        etiqueta="Secciones de Progreso"
        valor={vista}
        onCambio={setVista}
        opciones={[
          { valor: "actividad", etiqueta: "Actividad" },
          { valor: "cuerpo", etiqueta: "Cuerpo" },
          { valor: "metricas", etiqueta: "Métricas" },
        ]}
      >
        <p>Panel de {vista}</p>
      </Pestanas>
      <output aria-label="Consulta">{search}</output>
    </>
  );
}

describe("Pestanas", () => {
  it("es un tablist con la primera elegida y su panel etiquetado por ella", () => {
    montar(<Prueba />);

    const lista = screen.getByRole("tablist", { name: "Secciones de Progreso" });
    expect(lista).toBeVisible();
    expect(screen.getByRole("tab", { name: "Actividad" })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByRole("tabpanel", { name: "Actividad" })).toHaveTextContent(
      "Panel de actividad",
    );
  });

  it("solo existe el panel activo", () => {
    montar(<Prueba />);

    expect(screen.getAllByRole("tabpanel")).toHaveLength(1);
    expect(screen.queryByText("Panel de cuerpo")).not.toBeInTheDocument();
  });

  it("al pulsar cambia el panel y lo apunta en la URL", async () => {
    montar(<Prueba />);

    await userEvent.click(screen.getByRole("tab", { name: "Cuerpo" }));

    expect(screen.getByRole("tabpanel", { name: "Cuerpo" })).toHaveTextContent("Panel de cuerpo");
    expect(screen.getByRole("status", { name: "Consulta" })).toHaveTextContent("?vista=cuerpo");
  });

  it("la URL abre la pestaña que dice", () => {
    montar(<Prueba />, { ruta: "/progreso/?vista=metricas" });

    expect(screen.getByRole("tab", { name: "Métricas" })).toHaveAttribute("aria-selected", "true");
  });

  it("una vista que no existe cae en la primera", () => {
    montar(<Prueba />, { ruta: "/progreso/?vista=inventada" });

    expect(screen.getByRole("tab", { name: "Actividad" })).toHaveAttribute("aria-selected", "true");
  });

  it("las flechas, Inicio y Fin se mueven entre pestañas; solo la activa se tabula", async () => {
    montar(<Prueba />);
    const actividad = screen.getByRole("tab", { name: "Actividad" });
    expect(actividad).toHaveAttribute("tabindex", "0");
    expect(screen.getByRole("tab", { name: "Cuerpo" })).toHaveAttribute("tabindex", "-1");

    actividad.focus();
    await userEvent.keyboard("{ArrowRight}");
    expect(screen.getByRole("tab", { name: "Cuerpo" })).toHaveFocus();
    expect(screen.getByRole("tab", { name: "Cuerpo" })).toHaveAttribute("aria-selected", "true");

    await userEvent.keyboard("{End}");
    expect(screen.getByRole("tab", { name: "Métricas" })).toHaveFocus();

    await userEvent.keyboard("{ArrowRight}");
    expect(screen.getByRole("tab", { name: "Actividad" })).toHaveFocus();

    await userEvent.keyboard("{ArrowLeft}");
    expect(screen.getByRole("tab", { name: "Métricas" })).toHaveFocus();

    await userEvent.keyboard("{Home}");
    expect(screen.getByRole("tab", { name: "Actividad" })).toHaveAttribute("aria-selected", "true");
  });

  it("volver a la primera deja la URL limpia", async () => {
    montar(<Prueba />, { ruta: "/progreso/?vista=cuerpo" });

    await userEvent.click(screen.getByRole("tab", { name: "Actividad" }));

    expect(screen.getByRole("status", { name: "Consulta" })).toHaveTextContent(/^$/);
  });
});
