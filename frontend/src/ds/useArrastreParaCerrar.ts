import { useEffect, useRef, type RefObject } from "react";

const MODO_HOJA = "(max-width: 47.99rem)";
const SIN_ARRASTRE = "input, textarea, select, [contenteditable]";
const DECIDIR = 8;
const UMBRAL = 0.25;
const VELOCIDAD = 0.6;
const MINIMO_RAPIDO = 40;
const SALIDA_MS = 200;

function conMovimiento() {
  return window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches !== true;
}

export function useArrastreParaCerrar(
  ref: RefObject<HTMLDialogElement | null>,
  cerrar: () => void,
) {
  const cerrarRef = useRef(cerrar);

  useEffect(() => {
    cerrarRef.current = cerrar;
  });

  useEffect(() => {
    const hoja = ref.current;
    if (!hoja) return;
    let inicio: { x: number; y: number; t: number } | null = null;
    let arrastrando = false;
    let bajada = 0;

    const devolver = () => {
      hoja.style.transition = conMovimiento() ? "translate .25s cubic-bezier(.2, .8, .2, 1)" : "";
      hoja.style.translate = "";
    };

    const terminar = () => {
      cerrarRef.current();
      window.setTimeout(() => {
        if (hoja.isConnected && hoja.open) devolver();
      }, 50);
    };

    const alTocar = (evento: TouchEvent) => {
      inicio = null;
      arrastrando = false;
      bajada = 0;
      if (evento.touches.length !== 1) return;
      if (window.matchMedia?.(MODO_HOJA)?.matches !== true) return;
      const objetivo = evento.target instanceof Element ? evento.target : null;
      if (!objetivo || objetivo.closest(SIN_ARRASTRE)) return;
      const cuerpo = objetivo.closest(".panel-body");
      if (cuerpo && cuerpo.scrollTop > 0) return;
      const toque = evento.touches[0]!;
      inicio = { x: toque.clientX, y: toque.clientY, t: evento.timeStamp };
    };

    const alMover = (evento: TouchEvent) => {
      if (!inicio) return;
      const toque = evento.touches[0]!;
      const dy = toque.clientY - inicio.y;
      const dx = toque.clientX - inicio.x;
      if (!arrastrando) {
        if (Math.abs(dy) < DECIDIR && Math.abs(dx) < DECIDIR) return;
        if (dy <= 0 || Math.abs(dx) > dy) {
          inicio = null;
          return;
        }
        arrastrando = true;
        hoja.style.transition = "none";
      }
      evento.preventDefault();
      bajada = Math.max(0, dy);
      hoja.style.translate = `0 ${bajada}px`;
    };

    const alSoltar = (evento: TouchEvent) => {
      if (!inicio || !arrastrando) {
        inicio = null;
        return;
      }
      const rapido =
        bajada > MINIMO_RAPIDO && bajada / Math.max(1, evento.timeStamp - inicio.t) > VELOCIDAD;
      const lejos = bajada >= hoja.offsetHeight * UMBRAL;
      inicio = null;
      arrastrando = false;
      if (!lejos && !rapido) {
        devolver();
        return;
      }
      if (!conMovimiento()) {
        terminar();
        return;
      }
      hoja.style.transition = `translate ${SALIDA_MS}ms ease-in`;
      hoja.style.translate = `0 ${hoja.offsetHeight + 32}px`;
      window.setTimeout(terminar, SALIDA_MS);
    };

    const alCancelar = () => {
      if (arrastrando) devolver();
      inicio = null;
      arrastrando = false;
    };

    hoja.addEventListener("touchstart", alTocar, { passive: true });
    hoja.addEventListener("touchmove", alMover, { passive: false });
    hoja.addEventListener("touchend", alSoltar);
    hoja.addEventListener("touchcancel", alCancelar);
    return () => {
      hoja.removeEventListener("touchstart", alTocar);
      hoja.removeEventListener("touchmove", alMover);
      hoja.removeEventListener("touchend", alSoltar);
      hoja.removeEventListener("touchcancel", alCancelar);
    };
  }, [ref]);
}
