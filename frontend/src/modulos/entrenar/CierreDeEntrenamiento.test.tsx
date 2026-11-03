import { screen, waitFor } from "@testing-library/react";
import { userEvent } from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { Route, Routes } from "react-router";
import { describe, expect, it } from "vitest";

import { montar } from "@/test/montar";
import { servidor } from "@/test/servidor";

import type { ResumenDeCierre } from "./api";
import { CierreDeEntrenamiento } from "./CierreDeEntrenamiento";

const RESUMEN: ResumenDeCierre = {
  sesion: { id: 5, fecha: "2026-09-14", rutina: "Empuje A", notas: "" },
  duracion_minutos: 52,
  series: 12,
  ejercicios: 4,
  tonelaje_kg: 12450,
  series_sin_cobertura: 0,
  records: [{ ejercicio: "Press de banca", kg: "85" }],
  musculos: ["Pectorales", "Tríceps"],
};

function montarCierre(datos: ResumenDeCierre = RESUMEN) {
  servidor.use(
    http.get("/api/entrenamientos/:id/resumen/", () => HttpResponse.json(datos)),
  );
  return montar(
    <Routes>
      <Route path="/entrenamientos/:id/cierre" element={<CierreDeEntrenamiento />} />
    </Routes>,
    { ruta: "/entrenamientos/5/cierre" },
  );
}

describe("CierreDeEntrenamiento", () => {
  it("enseña las cifras tal como llegan, sin sumar nada", async () => {
    montarCierre();

    expect(await screen.findByText("52")).toBeVisible();
    expect(screen.getByText("12")).toBeVisible();
    expect(screen.getByText("12.450")).toBeVisible();
  });

  it("los récords van primero: es lo único que no se sabía al entrar", async () => {
    montarCierre();

    const titulo = await screen.findByText("Récord personal");
    const duracion = screen.getByText("Duración");
    expect(titulo.compareDocumentPosition(duracion)).toBe(Node.DOCUMENT_POSITION_FOLLOWING);
    expect(screen.getByText("Press de banca")).toBeVisible();
  });

  it("sin récords no enseña un bloque vacío", async () => {
    montarCierre({ ...RESUMEN, records: [] });

    await screen.findByText("52");
    expect(screen.queryByText(/Récord(s)? personal/)).not.toBeInTheDocument();
    expect(screen.getByText("Ninguno hoy.")).toBeVisible();
  });

  it("sin hora de arranque dice por qué, en vez de poner un cero", async () => {
    montarCierre({ ...RESUMEN, duracion_minutos: null });

    expect(await screen.findByText("Sin hora de inicio.")).toBeVisible();
  });

  it("dice cuántas series se quedaron fuera del tonelaje", async () => {
    montarCierre({ ...RESUMEN, series_sin_cobertura: 3 });

    expect(await screen.findByText(/3 series sin peso corporal registrado/)).toBeVisible();
  });

  it("guarda las notas sobre la sesión", async () => {
    let recibido: unknown = null;
    servidor.use(
      http.patch("/api/entrenamientos/:id/", async ({ request }) => {
        recibido = await request.json();
        return HttpResponse.json({});
      }),
    );
    montarCierre();

    await userEvent.type(await screen.findByLabelText("Cómo ha ido"), "Bien");
    await userEvent.click(screen.getByRole("button", { name: "Guardar notas" }));

    await waitFor(() => expect(recibido).toEqual({ notes: "Bien" }));
  });

  it("sin tocar nada no deja guardar", async () => {
    montarCierre();

    expect(await screen.findByRole("button", { name: "Guardar notas" })).toBeDisabled();
  });
});
