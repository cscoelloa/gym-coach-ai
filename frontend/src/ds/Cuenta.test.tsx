import { screen, waitFor } from "@testing-library/react";
import { userEvent } from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";
import { Route, Routes } from "react-router";
import { useCambiosPendientes } from "@/lib/cambiosPendientes";
import { montar } from "@/test/montar";
import { servidor } from "@/test/servidor";
import { Cuenta } from "./Cuenta";

const usuario = { id: 1, username: "ana", first_name: "Ana", is_staff: false };
describe("Cuenta", () => {
  it("ofrece perfil, tema y cierre de sesión sin gestión para usuarios normales", async () => {
    montar(<Cuenta usuario={usuario} />);
    await userEvent.click(screen.getByRole("button", { name: "Cuenta" }));
    expect(screen.getByRole("dialog", { name: "Tu cuenta" })).toBeVisible();
    expect(screen.getByRole("button", { name: /Perfil/ })).toBeVisible();
    expect(screen.getByRole("button", { name: "Cerrar sesión" })).toBeVisible();
    expect(screen.queryByRole("button", { name: /Gestión/ })).not.toBeInTheDocument();
  });

  it("un error deja la cuenta abierta y se puede reintentar", async () => {
    let peticiones = 0;
    servidor.use(http.delete("/api/auth/session/", () => {
      peticiones++;
      return peticiones === 1 ? HttpResponse.json({ detail: "Error" }, { status: 500 }) : new HttpResponse(null, { status: 204 });
    }));
    montar(<Routes><Route path="/" element={<Cuenta usuario={usuario} />} /><Route path="/sesion-cerrada" element={<p>Sesión cerrada</p>} /></Routes>);
    await userEvent.click(screen.getByRole("button", { name: "Cuenta" }));
    await userEvent.click(screen.getByRole("button", { name: "Cerrar sesión" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("No se pudo cerrar sesión");
    await userEvent.click(screen.getByRole("button", { name: "Cerrar sesión" }));
    await waitFor(() => expect(peticiones).toBe(2));
    expect(await screen.findByText("Sesión cerrada")).toBeVisible();
  });

  it("avisa de los cambios sin guardar antes de cerrar sesión", async () => {
    let peticiones = 0;
    servidor.use(http.delete("/api/auth/session/", () => { peticiones++; return new HttpResponse(null, { status: 204 }); }));
    function ConCambios() { useCambiosPendientes(true); return <Cuenta usuario={usuario} />; }
    montar(<Routes><Route path="/" element={<ConCambios />} /><Route path="/sesion-cerrada" element={<p>Sesión cerrada</p>} /></Routes>);
    await userEvent.click(screen.getByRole("button", { name: "Cuenta" }));
    await userEvent.click(screen.getByRole("button", { name: "Cerrar sesión" }));
    await userEvent.click(await screen.findByRole("button", { name: "Seguir editando" }));
    expect(peticiones).toBe(0);
    expect(screen.getByRole("dialog", { name: "Tu cuenta" })).toBeVisible();
    await userEvent.click(screen.getByRole("button", { name: "Cerrar sesión" }));
    await userEvent.click(await screen.findByRole("button", { name: "Salir sin guardar" }));
    expect(await screen.findByText("Sesión cerrada")).toBeVisible();
    expect(peticiones).toBe(1);
  });
});
