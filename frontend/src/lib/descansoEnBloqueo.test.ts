import { act, cleanup, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { _reiniciar, armar, mostrar, ocultar, useDescansoEnBloqueo } from "./descansoEnBloqueo";

type Metadatos = { title: string; artist: string; artwork: unknown[] };

function navegador() {
  const sesion = {
    metadata: null as Metadatos | null,
    playbackState: "none",
    setActionHandler: vi.fn(),
    setPositionState: vi.fn(),
  };
  Object.defineProperty(navigator, "mediaSession", { value: sesion, configurable: true });
  vi.stubGlobal(
    "MediaMetadata",
    class {
      title: string;
      artist: string;
      artwork: unknown[];
      constructor(datos: Metadatos) {
        this.title = datos.title;
        this.artist = datos.artist;
        this.artwork = datos.artwork;
      }
    },
  );
  const play = vi.spyOn(HTMLMediaElement.prototype, "play").mockResolvedValue(undefined);
  const pause = vi.spyOn(HTMLMediaElement.prototype, "pause").mockImplementation(() => {});
  return { sesion, play, pause };
}

function almacen() {
  const datos = new Map<string, string>();
  vi.stubGlobal("localStorage", {
    getItem: (clave: string) => datos.get(clave) ?? null,
    setItem: (clave: string, valor: string) => void datos.set(clave, valor),
    removeItem: (clave: string) => void datos.delete(clave),
    clear: () => datos.clear(),
  });
}

beforeEach(() => {
  _reiniciar();
  almacen();
});

afterEach(() => {
  cleanup();
  vi.useRealTimers();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  Reflect.deleteProperty(navigator, "mediaSession");
});

describe("el descanso en la pantalla de bloqueo", () => {
  it("donde no hay Media Session no hace nada ni rompe", () => {
    expect(() => {
      armar();
      mostrar(60, 90);
      ocultar();
    }).not.toThrow();

    const { result } = renderHook(() => useDescansoEnBloqueo(60, 90));
    expect(result.current.disponible).toBe(false);
  });

  it("tras armarlo con un toque, el descanso sale en «Reproduciendo ahora» con su progreso", () => {
    const { sesion, play } = navegador();

    armar();
    mostrar(88, 90);

    expect(play).toHaveBeenCalled();
    expect(sesion.metadata).toMatchObject({ title: "Descanso · 1:28", artist: "FitUp" });
    expect(sesion.playbackState).toBe("playing");
    expect(sesion.setPositionState).toHaveBeenLastCalledWith({
      duration: 90,
      position: 2,
      playbackRate: 1,
    });
  });

  it("sin un toque antes no publica nada: iOS no deja sonar sin gesto", () => {
    const { sesion } = navegador();

    mostrar(88, 90);

    expect(sesion.metadata).toBeNull();
  });

  it("si el navegador no deja sonar, no publica una tarjeta muda", async () => {
    const { sesion, play } = navegador();
    play.mockRejectedValue(new DOMException("sin gesto", "NotAllowedError"));

    armar();
    await new Promise((listo) => setTimeout(listo, 0));
    mostrar(60, 90);

    expect(sesion.metadata).toBeNull();
  });

  it("cada segundo cambia el título sin rehacer la carátula", () => {
    const { sesion } = navegador();

    armar();
    mostrar(88, 90);
    const primera = sesion.metadata;
    mostrar(87, 90);

    expect(sesion.metadata).toBe(primera);
    expect(sesion.metadata?.title).toBe("Descanso · 1:27");
  });

  it("al acabar el descanso se va de la pantalla de bloqueo y deja de sonar", () => {
    const { sesion, pause } = navegador();

    armar();
    mostrar(5, 90);
    ocultar();

    expect(pause).toHaveBeenCalled();
    expect(sesion.metadata).toBeNull();
    expect(sesion.playbackState).toBe("none");
  });

  it("si tras el toque no llega descanso (última serie, un error), el audio se apaga solo", () => {
    vi.useFakeTimers();
    const { pause } = navegador();

    armar();
    vi.advanceTimersByTime(5000);

    expect(pause).toHaveBeenCalled();
  });

  it("apagado, el descanso no sale aunque esté corriendo", () => {
    const { sesion } = navegador();

    renderHook(() => useDescansoEnBloqueo(60, 90));

    expect(sesion.metadata).toBeNull();
  });

  it("el interruptor se recuerda; encenderlo en pleno descanso lo muestra y apagarlo lo quita", () => {
    const { sesion } = navegador();
    const { result } = renderHook(() => useDescansoEnBloqueo(60, 90));

    act(() => result.current.cambiar());

    expect(result.current.activo).toBe(true);
    expect(localStorage.getItem("gym-descanso-bloqueo")).toBe("1");
    expect(sesion.metadata?.title).toBe("Descanso · 1:00");

    act(() => result.current.cambiar());

    expect(result.current.activo).toBe(false);
    expect(localStorage.getItem("gym-descanso-bloqueo")).toBe("0");
    expect(sesion.metadata).toBeNull();
  });

  it("encendido, sigue el descanso en vivo y desaparece cuando acaba", () => {
    localStorage.setItem("gym-descanso-bloqueo", "1");
    const { sesion } = navegador();
    const { result, rerender } = renderHook(
      ({ restante }) => useDescansoEnBloqueo(restante, 90),
      { initialProps: { restante: null as number | null } },
    );

    act(() => result.current.armar());
    rerender({ restante: 90 });
    expect(sesion.metadata?.title).toBe("Descanso · 1:30");

    rerender({ restante: 89 });
    expect(sesion.metadata?.title).toBe("Descanso · 1:29");

    rerender({ restante: null });
    expect(sesion.metadata).toBeNull();
  });
});
