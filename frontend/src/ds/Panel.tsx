import { useEffect, useId, useRef, type ReactNode } from "react";

import { Icono } from "./Icono";
import { useArrastreParaCerrar } from "./useArrastreParaCerrar";

export function Panel({
  titulo,
  onCerrar,
  children,
}: {
  titulo: string;
  onCerrar: () => void;
  children: ReactNode;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const id = useId();
  useArrastreParaCerrar(ref, onCerrar);

  useEffect(() => {
    const dialogo = ref.current!;
    const previo = document.activeElement as HTMLElement | null;
    const overflow = document.body.style.overflow;
    const visible = window.visualViewport;
    const ajustar = () => {
      if (!visible) return;
      dialogo.style.setProperty("--vv-arriba", `${visible.offsetTop}px`);
      dialogo.style.setProperty("--vv-alto", `${visible.height}px`);
    };
    const tactil = window.matchMedia?.("(pointer: coarse)")?.matches === true;
    ajustar();
    visible?.addEventListener("resize", ajustar);
    visible?.addEventListener("scroll", ajustar);
    dialogo.showModal();
    (
      (tactil ? null : dialogo.querySelector<HTMLElement>("[data-autofocus]")) ??
      dialogo.querySelector<HTMLElement>(".panel-head h2")
    )?.focus();
    document.body.style.overflow = "hidden";
    return () => {
      visible?.removeEventListener("resize", ajustar);
      visible?.removeEventListener("scroll", ajustar);
      dialogo.close();
      document.body.style.overflow = overflow;
      if (previo?.isConnected) previo.focus();
    };
  }, []);

  return (
    <dialog
      ref={ref}
      className="app-panel"
      aria-labelledby={id}
      onCancel={(evento) => {
        evento.preventDefault();
        onCerrar();
      }}
      onClick={(evento) => {
        if (evento.target !== evento.currentTarget) return;
        const caja = evento.currentTarget.getBoundingClientRect();
        const fuera =
          evento.clientX < caja.left ||
          evento.clientX > caja.right ||
          evento.clientY < caja.top ||
          evento.clientY > caja.bottom;
        if (fuera) onCerrar();
      }}
    >
      <header className="panel-head">
        <h2 id={id} tabIndex={-1}>
          {titulo}
        </h2>
        <button
          type="button"
          className="icon-button size-9 bg-surface-200 text-ink-muted"
          onClick={onCerrar}
          aria-label="Cerrar panel"
        >
          <Icono nombre="cerrar" className="size-4" />
        </button>
      </header>
      <div className="panel-body">{children}</div>
    </dialog>
  );
}
