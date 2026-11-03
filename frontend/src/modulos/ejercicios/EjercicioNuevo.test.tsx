import { screen, waitFor, within } from "@testing-library/react";
import { userEvent } from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { montar } from "@/test/montar";
import { servidor } from "@/test/servidor";

import { EjercicioNuevo } from "./EjercicioNuevo";

const navegar = vi.fn();
vi.mock("react-router", async () => ({
  ...(await vi.importActual<typeof import("react-router")>("react-router")),
  useNavigate: () => navegar,
}));

const TAXONOMIA = {
  body_part: [
    { valor: "chest", etiqueta: "Pecho" },
    { valor: "back", etiqueta: "Espalda" },
  ],
  equipment: [{ valor: "band", etiqueta: "Banda" }],
};

beforeEach(() => {
  servidor.use(http.get("/api/ejercicios/taxonomia/", () => HttpResponse.json(TAXONOMIA)));
});

afterEach(() => vi.clearAllMocks());

async function rellenar() {
  await userEvent.type(await screen.findByLabelText("Nombre"), "Remo con banda");
  await userEvent.selectOptions(screen.getByLabelText("Zona del cuerpo"), "back");
  await userEvent.selectOptions(screen.getByLabelText("Equipamiento"), "band");
}

describe("EjercicioNuevo", () => {
  it("crea el ejercicio y lleva a su ficha", async () => {
    servidor.use(
      http.post("/api/ejercicios/", () =>
        HttpResponse.json({ slug: "remo-con-banda" }, { status: 201 }),
      ),
    );
    montar(<EjercicioNuevo />);

    await rellenar();
    await userEvent.click(screen.getByRole("button", { name: "Crear ejercicio" }));

    await waitFor(() => expect(navegar).toHaveBeenCalledWith("/ejercicios/remo-con-banda/"));
  });

  it("ofrece todas las zonas, no solo las que tienen ejercicios", async () => {
    montar(<EjercicioNuevo />);

    const zona = await screen.findByLabelText("Zona del cuerpo");
    expect(within(zona).getByRole("option", { name: "Espalda" })).toBeInTheDocument();
  });

  it("el error de nombre repetido se pinta en su campo", async () => {
    servidor.use(
      http.post("/api/ejercicios/", () =>
        HttpResponse.json(
          { name: ["Ya tienes un ejercicio con ese nombre, o está en el catálogo."] },
          { status: 400 },
        ),
      ),
    );
    montar(<EjercicioNuevo />);

    await rellenar();
    await userEvent.click(screen.getByRole("button", { name: "Crear ejercicio" }));

    const campo = screen.getByLabelText("Nombre");
    await waitFor(() => expect(campo).toHaveAttribute("aria-invalid", "true"));
    expect(campo).toHaveAccessibleDescription(/ya tienes un ejercicio/i);
    expect(navegar).not.toHaveBeenCalled();
  });

  it("dice por qué no se puede subir una imagen", async () => {
    montar(<EjercicioNuevo />);

    expect(await screen.findByText(/Gym Visual/)).toBeVisible();
    expect(screen.queryByLabelText(/imagen/i)).not.toBeInTheDocument();
  });

  it("las casillas explican para qué sirven", async () => {
    montar(<EjercicioNuevo />);

    expect(await screen.findByText(/el tonelaje contará los dos/)).toBeVisible();
    expect(screen.getByText(/se calcula con tu peso corporal/)).toBeVisible();
  });
});
