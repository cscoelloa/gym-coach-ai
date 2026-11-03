import { useEffect, useState } from "react";

const CLAVE = "gym-pantalla-encendida";

function leer(): boolean {
  try {
    return localStorage.getItem(CLAVE) === "1";
  } catch {
    return false;
  }
}

export function usePantallaEncendida() {
  const disponible = typeof navigator !== "undefined" && "wakeLock" in navigator;
  const [activa, setActiva] = useState(() => disponible && leer());

  useEffect(() => {
    if (!activa) return;
    let bloqueo: WakeLockSentinel | null = null;
    let vivo = true;

    async function pedir() {
      if (document.visibilityState !== "visible") return;
      try {
        const nuevo = await navigator.wakeLock.request("screen");
        if (vivo) bloqueo = nuevo;
        else void nuevo.release();
      } catch {
      }
    }

    void pedir();
    const alVolver = () => void pedir();
    document.addEventListener("visibilitychange", alVolver);
    return () => {
      vivo = false;
      document.removeEventListener("visibilitychange", alVolver);
      void bloqueo?.release().catch(() => {});
    };
  }, [activa]);

  function cambiar() {
    const siguiente = !activa;
    setActiva(siguiente);
    try {
      localStorage.setItem(CLAVE, siguiente ? "1" : "0");
    } catch {
    }
  }

  return { disponible, activa, cambiar };
}
