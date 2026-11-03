import { render, screen, within } from "@testing-library/react";
import { userEvent } from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { montar } from "@/test/montar";

import { Anillo } from "./Anillo";
import { Badge } from "./Badge";
import { Button, EnlaceBoton } from "./Button";
import { Campo } from "./Campo";
import { EmptyState } from "./EmptyState";
import { ProgressBar } from "./ProgressBar";
import { formatearCuenta, RestTimer } from "./RestTimer";
import { RoutineCard } from "./RoutineCard";
import { SetRow } from "./SetRow";
import { StatTile } from "./StatTile";
import { Stepper } from "./Stepper";

describe("Button", () => {
  it("no envía el formulario por defecto", async () => {
    const enviar = vi.fn((evento: React.FormEvent) => evento.preventDefault());
    render(
      <form onSubmit={enviar}>
        <Button>Cancelar</Button>
      </form>,
    );

    await userEvent.click(screen.getByRole("button", { name: "Cancelar" }));

    expect(enviar).not.toHaveBeenCalled();
  });

  it("envía cuando se le pide explícitamente", async () => {
    const enviar = vi.fn((evento: React.FormEvent) => evento.preventDefault());
    render(
      <form onSubmit={enviar}>
        <Button type="submit">Guardar</Button>
      </form>,
    );

    await userEvent.click(screen.getByRole("button", { name: "Guardar" }));

    expect(enviar).toHaveBeenCalledOnce();
  });

  it("un destino que aún sirve Django se enlaza con una carga completa", () => {
    montar(<EnlaceBoton a="/plan/">Plan</EnlaceBoton>);

    expect(screen.getByRole("link", { name: "Plan" })).toHaveAttribute("href", "/plan/");
  });
});

describe("ProgressBar", () => {
  it("no divide por cero", () => {
    render(<ProgressBar etiqueta="Series" hecho={0} total={0} />);

    const barra = screen.getByRole("progressbar", { name: "Series" });
    expect(barra.firstElementChild).toHaveStyle({ "--avance": "0%" });
  });

  it("no pasa del 100 % aunque se hagan series de más", () => {
    render(<ProgressBar etiqueta="Series" hecho={6} total={4} />);

    const barra = screen.getByRole("progressbar", { name: "Series" });
    expect(barra.firstElementChild).toHaveStyle({ "--avance": "100%" });
  });
});

describe("Anillo", () => {
  it("dice lo que pinta: para un lector de pantalla no es un círculo", () => {
    render(<Anillo hecho={2} total={4} etiqueta="2 de 4 entrenamientos esta semana" />);

    expect(screen.getByRole("img", { name: "2 de 4 entrenamientos esta semana" })).toBeVisible();
  });

  it("al llegar al objetivo se cierra en verde, y pasarse no da otra vuelta", () => {
    const { container } = render(<Anillo hecho={5} total={4} etiqueta="5 de 4" />);

    const arco = container.querySelector(".goal-ring-arc")!;
    expect(arco).toHaveAttribute("data-tono", "success");
    expect((arco as SVGElement).style.getPropertyValue("--resto")).toBe("0");
  });

  it("sin objetivo se queda vacío, no lleno", () => {
    const { container } = render(<Anillo hecho={3} total={0} etiqueta="3 esta semana" />);

    const arco = container.querySelector(".goal-ring-arc")!;
    expect(arco).toHaveAttribute("data-tono", "primary");
    expect(Number((arco as SVGElement).style.getPropertyValue("--resto"))).toBeGreaterThan(0);
  });
});

describe("StatTile", () => {
  it("sin datos enseña un guion, no un cero", () => {
    render(<StatTile etiqueta="Cardio" valor={null} vacio="Sin registros." />);

    expect(screen.getByText("—")).toBeVisible();
    expect(screen.getByText("Sin registros.")).toBeVisible();
  });

  it("un cero de verdad sí se enseña", () => {
    render(<StatTile etiqueta="Series" valor={0} />);

    expect(screen.getByText("0")).toBeVisible();
  });

  it("estando vacío no pinta además el pie", () => {
    render(
      <StatTile etiqueta="Cardio" valor={null} vacio="Sin registros.">
        <Badge tono="done">+6 %</Badge>
      </StatTile>,
    );

    expect(screen.queryByText("+6 %")).not.toBeInTheDocument();
  });
});

describe("Campo", () => {
  it("asocia la etiqueta, la ayuda y el error al control", () => {
    render(<Campo etiqueta="Carga" ayuda="La última vez: 80" errores={["Escribe al menos 1."]} />);

    const control = screen.getByLabelText("Carga");
    expect(control).toHaveAttribute("aria-invalid", "true");
    expect(control).toHaveAccessibleDescription(/Escribe al menos 1\..*La última vez: 80/s);
  });

  it("sin errores no se declara inválido", () => {
    render(<Campo etiqueta="Carga" />);

    expect(screen.getByLabelText("Carga")).not.toHaveAttribute("aria-invalid");
  });
});

describe("SetRow", () => {
  it("reserva la columna del tic aunque la serie no esté hecha", () => {
    const { container } = render(<SetRow numero={4} peso="82.5" reps={8} />);

    expect(container.querySelector(".set-row-check")).toBeInTheDocument();
  });

  it("una serie sin datos no enseña un cero", () => {
    render(<SetRow numero={1} peso={null} reps={null} />);

    expect(screen.getAllByText("—")).toHaveLength(2);
  });
});

describe("Stepper", () => {
  it("sube y baja con el paso que le toca", async () => {
    const cambiar = vi.fn();
    render(<Stepper etiqueta="kg" valor="82.5" onCambio={cambiar} paso={2.5} decimal />);

    await userEvent.click(screen.getByRole("button", { name: "Subir kg" }));

    expect(cambiar).toHaveBeenCalledWith("85");
  });

  it("no baja del mínimo", async () => {
    const cambiar = vi.fn();
    render(<Stepper etiqueta="Reps" valor="1" onCambio={cambiar} minimo={1} />);

    await userEvent.click(screen.getByRole("button", { name: "Bajar Reps" }));

    expect(cambiar).toHaveBeenCalledWith("1");
  });

  it("deja escribir a mano", async () => {
    const cambiar = vi.fn();
    render(<Stepper etiqueta="kg" valor="" onCambio={cambiar} decimal />);

    await userEvent.type(screen.getByLabelText("kg"), "9");

    expect(cambiar).toHaveBeenCalledWith("9");
  });
});

describe("RestTimer", () => {
  it.each([
    [95, "1:35"],
    [62, "1:02"],
    [5, "0:05"],
    [0, "0:00"],
    [-3, "0:00"],
  ])("formatea %i segundos como %s", (segundos, esperado) => {
    expect(formatearCuenta(segundos)).toBe(esperado);
  });

  it("no anuncia cada segundo por el lector de pantalla", () => {
    render(<RestTimer restante={62} total={90} />);

    expect(screen.getByRole("timer")).toHaveAttribute("aria-live", "off");
  });
});

describe("RoutineCard", () => {
  it("resume lo que no cabe en vez de crecer sin límite", () => {
    const ejercicios = Array.from({ length: 7 }, (_, i) => ({ nombre: `Ejercicio ${i + 1}` }));
    render(<RoutineCard nombre="Pierna" ejercicios={ejercicios} />);

    expect(screen.getByText("+4 ejercicios")).toBeVisible();
    expect(screen.queryByText("Ejercicio 5")).not.toBeInTheDocument();
  });

  it("singulariza cuando sobra uno solo", () => {
    const ejercicios = Array.from({ length: 4 }, (_, i) => ({ nombre: `Ejercicio ${i + 1}` }));
    render(<RoutineCard nombre="Pierna" ejercicios={ejercicios} />);

    expect(screen.getByText("+1 ejercicio")).toBeVisible();
  });

  it("una rutina vacía lo dice", () => {
    render(<RoutineCard nombre="Nueva" ejercicios={[]} />);

    expect(screen.getByText("Sin ejercicios todavía")).toBeVisible();
  });
});

describe("EmptyState", () => {
  it("ofrece una salida, no solo el aviso de que está vacío", () => {
    montar(
      <EmptyState titulo="Aún no tienes rutinas" acciones={<Button>Crear rutina</Button>}>
        Arma una con los ejercicios que ya haces.
      </EmptyState>,
    );

    const estado = screen.getByText("Aún no tienes rutinas").parentElement!;
    expect(within(estado).getByRole("button", { name: "Crear rutina" })).toBeVisible();
  });
});
