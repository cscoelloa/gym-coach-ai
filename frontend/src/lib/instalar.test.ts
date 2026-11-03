import { act, renderHook } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { _reiniciar, esIos, escucharInstalacion, useInstalacion } from "./instalar";

afterEach(() => act(() => _reiniciar()));

describe("esIos", () => {
  it.each([
    ["Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15", "iPhone"],
    ["Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15", "iPhone"],
  ])("reconoce %s", (agente, plataforma) => {
    expect(esIos(agente, plataforma)).toBe(true);
  });

  it("no confunde un Android con un iPhone", () => {
    const android = "Mozilla/5.0 (Linux; Android 14; Pixel 7) AppleWebKit/537.36 Chrome/130";
    expect(esIos(android, "Linux armv8l")).toBe(false);
  });
});

describe("useInstalacion", () => {
  it("con el aviso de Chrome ofrece instalar, y al pulsar abre el diálogo del navegador", async () => {
    escucharInstalacion();
    const { result } = renderHook(() => useInstalacion());
    expect(result.current.modo).toBeNull();

    const prompt = vi.fn(async () => {});
    const aviso = Object.assign(new Event("beforeinstallprompt"), {
      prompt,
      userChoice: Promise.resolve({ outcome: "accepted" as const, platform: "web" }),
    });
    act(() => {
      window.dispatchEvent(aviso);
    });

    expect(result.current.modo).toBe("prompt");

    await act(() => result.current.instalar());

    expect(prompt).toHaveBeenCalledOnce();
    expect(result.current.modo).toBeNull();
  });

  it("una vez instalada, no se ofrece más", () => {
    escucharInstalacion();
    const { result } = renderHook(() => useInstalacion());
    act(() => {
      window.dispatchEvent(
        Object.assign(new Event("beforeinstallprompt"), {
          prompt: async () => {},
          userChoice: Promise.resolve({ outcome: "accepted" as const, platform: "web" }),
        }),
      );
    });

    act(() => {
      window.dispatchEvent(new Event("appinstalled"));
    });

    expect(result.current.modo).toBeNull();
  });
});
