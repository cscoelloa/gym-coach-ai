import { screen, waitFor } from "@testing-library/react";
import { userEvent } from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { afterEach, describe, expect, it, vi } from "vitest";

import { montar } from "@/test/montar";
import { servidor } from "@/test/servidor";

vi.mock("@/lib/navegar", () => ({ salirDeLaSpa: vi.fn() }));

import { salirDeLaSpa } from "@/lib/navegar";

import { Entrar } from "./Entrar";

const ENDPOINT = "/api/auth/session/";

const irA = vi.mocked(salirDeLaSpa);

afterEach(() => vi.clearAllMocks());

describe("Entrar", () => {
  it("manda las credenciales y navega adonde diga el servidor", async () => {
    servidor.use(
      http.post(ENDPOINT, () =>
        HttpResponse.json({
          usuario: { id: 1, username: "ana", first_name: "Ana", is_staff: false },
          redirect: "/",
        }),
      ),
    );
    montar(<Entrar />, { ruta: "/entrar/" });

    await userEvent.type(screen.getByLabelText("Usuario"), "ana");
    await userEvent.type(screen.getByLabelText("Contraseña"), "Contrasena-Larga-1");
    await userEvent.click(screen.getByRole("button", { name: "Entrar" }));

    await waitFor(() => expect(irA).toHaveBeenCalledWith("/"));
  });

  it("arrastra el destino previo", async () => {
    let recibido: unknown = null;
    servidor.use(
      http.post(ENDPOINT, async ({ request }) => {
        recibido = await request.json();
        return HttpResponse.json({
          usuario: { id: 1, username: "ana", first_name: "Ana", is_staff: false },
          redirect: "/plan/",
        });
      }),
    );
    montar(<Entrar />, { ruta: "/entrar/?next=/plan/" });

    await userEvent.type(screen.getByLabelText("Usuario"), "ana");
    await userEvent.type(screen.getByLabelText("Contraseña"), "x");
    await userEvent.click(screen.getByRole("button", { name: "Entrar" }));

    await waitFor(() => expect(recibido).toMatchObject({ next: "/plan/" }));
  });

  it("enseña el mensaje del servidor cuando las credenciales no valen", async () => {
    servidor.use(
      http.post(ENDPOINT, () =>
        HttpResponse.json({ detail: "Usuario o contraseña incorrectos." }, { status: 400 }),
      ),
    );
    montar(<Entrar />, { ruta: "/entrar/" });

    await userEvent.type(screen.getByLabelText("Usuario"), "ana");
    await userEvent.type(screen.getByLabelText("Contraseña"), "la-que-no-es");
    await userEvent.click(screen.getByRole("button", { name: "Entrar" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Usuario o contraseña incorrectos.",
    );
  });

  it("el bloqueo por intentos se anuncia distinto que una contraseña mal", async () => {
    servidor.use(
      http.post(ENDPOINT, () =>
        HttpResponse.json(
          { detail: "Demasiados intentos fallidos. La cuenta queda bloqueada durante una hora." },
          { status: 403 },
        ),
      ),
    );
    montar(<Entrar />, { ruta: "/entrar/" });

    await userEvent.type(screen.getByLabelText("Usuario"), "ana");
    await userEvent.type(screen.getByLabelText("Contraseña"), "x");
    await userEvent.click(screen.getByRole("button", { name: "Entrar" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Demasiados intentos");
  });

  it("no valida las reglas de contraseña por su cuenta", async () => {
    let llego = false;
    servidor.use(
      http.post(ENDPOINT, () => {
        llego = true;
        return HttpResponse.json({ detail: "Usuario o contraseña incorrectos." }, { status: 400 });
      }),
    );
    montar(<Entrar />, { ruta: "/entrar/" });

    await userEvent.type(screen.getByLabelText("Usuario"), "ana");
    await userEvent.type(screen.getByLabelText("Contraseña"), "1");
    await userEvent.click(screen.getByRole("button", { name: "Entrar" }));

    await waitFor(() => expect(llego).toBe(true));
  });
});
