const CAMPOS = "input, textarea, select, [contenteditable]";
const ESPERA_MS = 350;

function hayCampoActivo(): boolean {
  const activo = document.activeElement;
  return activo instanceof HTMLElement && activo.matches(CAMPOS);
}

export function medirDesfase(vista: VisualViewport | null | undefined): number {
  if (!vista || hayCampoActivo() || Math.abs(vista.scale - 1) > 0.01) return 0;
  return Math.max(0, Math.round(vista.offsetTop));
}

export function vigilarElDesfaseDelTeclado(raiz: HTMLElement = document.documentElement) {
  const vista = window.visualViewport;
  if (!vista) return () => {};

  let actual = 0;
  let espera: ReturnType<typeof setTimeout> | undefined;

  const aplicar = () => {
    const nuevo = medirDesfase(vista);
    if (nuevo === actual) return;
    actual = nuevo;
    raiz.style.setProperty("--desfase-teclado", `${nuevo}px`);
  };

  const aplicarAhoraYLuego = () => {
    aplicar();
    clearTimeout(espera);
    espera = setTimeout(aplicar, ESPERA_MS);
  };

  vista.addEventListener("resize", aplicarAhoraYLuego);
  vista.addEventListener("scroll", aplicar);
  document.addEventListener("focusin", aplicar);
  document.addEventListener("focusout", aplicarAhoraYLuego);
  document.addEventListener("visibilitychange", aplicarAhoraYLuego);

  return () => {
    clearTimeout(espera);
    vista.removeEventListener("resize", aplicarAhoraYLuego);
    vista.removeEventListener("scroll", aplicar);
    document.removeEventListener("focusin", aplicar);
    document.removeEventListener("focusout", aplicarAhoraYLuego);
    document.removeEventListener("visibilitychange", aplicarAhoraYLuego);
    raiz.style.removeProperty("--desfase-teclado");
  };
}
