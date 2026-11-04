import { useEffect, useRef, type ReactNode } from "react";

export function BarraDeAcciones({ children }: { children: ReactNode }) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const barra = ref.current!;
    const raiz = document.documentElement;
    const medir = () => raiz.style.setProperty("--acciones-h", `${barra.offsetHeight}px`);
    medir();
    const observador = typeof ResizeObserver === "undefined" ? null : new ResizeObserver(medir);
    observador?.observe(barra);
    return () => {
      observador?.disconnect();
      raiz.style.removeProperty("--acciones-h");
    };
  }, []);

  return (
    <div ref={ref} className="editor-actions">
      {children}
    </div>
  );
}
