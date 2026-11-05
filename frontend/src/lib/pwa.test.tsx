import { act, render, screen } from "@testing-library/react";
import { userEvent } from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AvisoDeActualizacion } from "@/ds/AvisoDeActualizacion";

import { _anunciar, _reiniciar, borrarCachesDeLaApp, retenerActualizacion } from "./pwa";

afterEach(() => {
  act(() => _reiniciar());
  vi.unstubAllGlobals();
});

function montarAviso() {
  return render(<AvisoDeActualizacion />);
}

describe("El aviso de versión nueva", () => {
  it("no aparece mientras no haya una versión esperando", () => {
    montarAviso();

    expect(screen.queryByText(/versión nueva/)).not.toBeInTheDocument();
  });

  it("si no hay nada en marcha, se aplica sola", () => {
    const enEspera = { postMessage: vi.fn() } as unknown as ServiceWorker;
    montarAviso();

    act(() => _anunciar(enEspera));

    expect(enEspera.postMessage).toHaveBeenCalledWith({ tipo: "SALTAR_ESPERA" });
  });

  it("mientras se edita o se entrena, espera y solo aplica al pulsar o al terminar", async () => {
    const enEspera = { postMessage: vi.fn() } as unknown as ServiceWorker;
    const liberar = retenerActualizacion();
    montarAviso();

    act(() => _anunciar(enEspera));

    expect(await screen.findByText(/Hay una versión nueva/)).toBeVisible();
    expect(enEspera.postMessage).not.toHaveBeenCalled();

    await userEvent.click(screen.getByRole("button", { name: "Actualizar" }));
    expect(enEspera.postMessage).toHaveBeenCalledWith({ tipo: "SALTAR_ESPERA" });

    act(() => liberar());
  });

  it("al terminar la edición aplica la que estaba esperando", () => {
    const enEspera = { postMessage: vi.fn() } as unknown as ServiceWorker;
    const liberar = retenerActualizacion();

    act(() => _anunciar(enEspera));
    expect(enEspera.postMessage).not.toHaveBeenCalled();

    act(() => liberar());
    expect(enEspera.postMessage).toHaveBeenCalledWith({ tipo: "SALTAR_ESPERA" });
  });
});

describe("borrarCachesDeLaApp", () => {
  it("borra las de la aplicación y deja las ajenas", async () => {
    const borrar = vi.fn(async () => true);
    vi.stubGlobal("caches", {
      keys: async () => ["gym-abc123", "gym-def456", "otra-cosa"],
      delete: borrar,
    });

    await borrarCachesDeLaApp();

    expect(borrar).toHaveBeenCalledTimes(2);
    expect(borrar).toHaveBeenCalledWith("gym-abc123");
    expect(borrar).toHaveBeenCalledWith("gym-def456");
    expect(borrar).not.toHaveBeenCalledWith("otra-cosa");
  });

  it("no rompe en un navegador sin Cache Storage", async () => {
    vi.stubGlobal("caches", undefined);

    await expect(borrarCachesDeLaApp()).resolves.toBeUndefined();
  });
});
