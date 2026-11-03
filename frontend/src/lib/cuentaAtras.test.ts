import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { useCuentaAtras } from "./cuentaAtras";

let vibrar: ReturnType<typeof vi.fn>;

beforeEach(() => {
  vi.useFakeTimers();
  vibrar = vi.fn();
  Object.defineProperty(navigator, "vibrate", { value: vibrar, configurable: true });
});

afterEach(() => {
  vi.useRealTimers();
});

describe("useCuentaAtras", () => {
  it("cuenta hacia abajo desde lo configurado", () => {
    const { result } = renderHook(() => useCuentaAtras());

    act(() => result.current.arrancar(60));
    expect(result.current.restante).toBe(60);

    act(() => vi.advanceTimersByTime(10_000));
    expect(result.current.restante).toBe(50);
  });

  it("al llegar a cero se acaba y vibra, sin contar de más", () => {
    const { result } = renderHook(() => useCuentaAtras());
    act(() => result.current.arrancar(60));

    act(() => vi.advanceTimersByTime(60_000));

    expect(result.current.restante).toBeNull();
    expect(vibrar).toHaveBeenCalledOnce();

    act(() => vi.advanceTimersByTime(30_000));
    expect(result.current.restante).toBeNull();
    expect(vibrar).toHaveBeenCalledOnce();
  });

  it("si el fin pasó hace rato —pantalla bloqueada— se quita sin vibrar", () => {
    const { result } = renderHook(() => useCuentaAtras());
    act(() => result.current.arrancar(60));

    act(() => {
      vi.setSystemTime(Date.now() + 180_000);
      vi.advanceTimersByTime(250);
    });

    expect(result.current.restante).toBeNull();
    expect(vibrar).not.toHaveBeenCalled();
  });

  it("«+30 s» alarga el final", () => {
    const { result } = renderHook(() => useCuentaAtras());
    act(() => result.current.arrancar(60));
    act(() => vi.advanceTimersByTime(50_000));

    act(() => result.current.alargar(30));
    act(() => vi.advanceTimersByTime(20_000));

    expect(result.current.restante).toBe(20);
    expect(result.current.total).toBe(90);
  });

  it("un ejercicio sin descanso no enseña un «0:00»", () => {
    const { result } = renderHook(() => useCuentaAtras());

    act(() => result.current.arrancar(0));

    expect(result.current.restante).toBeNull();
  });
});
