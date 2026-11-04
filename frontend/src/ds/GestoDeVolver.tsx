import { useEffect, useRef } from "react";

import { Icono } from "./Icono";
import { useVolver } from "./useVolver";

const BORDE = 24;
const DECIDIR = 10;
const UMBRAL = 0.3;
const VELOCIDAD = 0.5;
const MINIMO_RAPIDO = 40;
const RECORRIDO = 96;
const ANCHO_FLECHA = 44;

function margenIzquierdo() {
  const valor = getComputedStyle(document.documentElement).getPropertyValue("--borde-izq");
  return Number.parseFloat(valor) || 0;
}

export function GestoDeVolver() {
  const { volver } = useVolver();
  const volverRef = useRef(volver);
  const flecha = useRef<HTMLDivElement>(null);

  useEffect(() => {
    volverRef.current = volver;
  });

  useEffect(() => {
    if (window.matchMedia?.("(display-mode: standalone)")?.matches !== true) return;
    const indicador = flecha.current!;
    let inicio: { x: number; y: number; t: number } | null = null;
    let arrastrando = false;
    let avance = 0;

    const ocultar = () => {
      indicador.hidden = true;
      indicador.style.translate = "";
      indicador.style.opacity = "";
    };

    const alTocar = (evento: TouchEvent) => {
      inicio = null;
      arrastrando = false;
      avance = 0;
      if (evento.touches.length !== 1 || document.querySelector("dialog[open]")) return;
      const toque = evento.touches[0]!;
      if (toque.clientX > BORDE + margenIzquierdo()) return;
      inicio = { x: toque.clientX, y: toque.clientY, t: evento.timeStamp };
    };

    const alMover = (evento: TouchEvent) => {
      if (!inicio) return;
      const toque = evento.touches[0]!;
      const dx = toque.clientX - inicio.x;
      const dy = toque.clientY - inicio.y;
      if (!arrastrando) {
        if (Math.abs(dx) < DECIDIR && Math.abs(dy) < DECIDIR) return;
        if (dx < DECIDIR || dx < Math.abs(dy) * 1.5) {
          inicio = null;
          return;
        }
        arrastrando = true;
      }
      evento.preventDefault();
      avance = Math.max(0, dx);
      indicador.hidden = false;
      indicador.style.top = `${toque.clientY}px`;
      indicador.style.translate = `${Math.min(avance, RECORRIDO) * 0.6 - ANCHO_FLECHA}px -50%`;
      indicador.style.opacity = String(Math.min(1, avance / 48));
      indicador.dataset.listo = String(avance >= window.innerWidth * UMBRAL);
    };

    const alSoltar = (evento: TouchEvent) => {
      if (!inicio || !arrastrando) {
        inicio = null;
        return;
      }
      const rapido =
        avance > MINIMO_RAPIDO && avance / Math.max(1, evento.timeStamp - inicio.t) > VELOCIDAD;
      const lejos = avance >= window.innerWidth * UMBRAL;
      inicio = null;
      arrastrando = false;
      ocultar();
      if (lejos || rapido) volverRef.current();
    };

    const alCancelar = () => {
      inicio = null;
      arrastrando = false;
      ocultar();
    };

    document.addEventListener("touchstart", alTocar, { passive: true });
    document.addEventListener("touchmove", alMover, { passive: false });
    document.addEventListener("touchend", alSoltar);
    document.addEventListener("touchcancel", alCancelar);
    return () => {
      document.removeEventListener("touchstart", alTocar);
      document.removeEventListener("touchmove", alMover);
      document.removeEventListener("touchend", alSoltar);
      document.removeEventListener("touchcancel", alCancelar);
    };
  }, []);

  return (
    <div ref={flecha} className="gesto-volver" aria-hidden="true" hidden>
      <Icono nombre="chevronIzquierda" className="size-6" />
    </div>
  );
}
