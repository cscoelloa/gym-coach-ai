import { useCallback, useEffect, useState } from "react";

export type Tema = "dark" | "light";
export type PreferenciaDeTema = "system" | Tema;

function leerTema(): Tema {
  return document.documentElement.getAttribute("data-theme") === "dark" ? "dark" : "light";
}

function leerPreferencia(): PreferenciaDeTema {
  const valor = document.documentElement.getAttribute("data-theme-pref");
  return valor === "light" || valor === "dark" ? valor : "system";
}

function resolver(preferencia: PreferenciaDeTema): Tema {
  if (preferencia !== "system") return preferencia;
  return window.matchMedia?.("(prefers-color-scheme: dark)")?.matches ? "dark" : "light";
}

export function useTema(): {
  tema: Tema;
  preferencia: PreferenciaDeTema;
  cambiar: (preferencia: PreferenciaDeTema) => void;
} {
  const [tema, setTema] = useState<Tema>(leerTema);
  const [preferencia, setPreferencia] = useState<PreferenciaDeTema>(leerPreferencia);

  useEffect(() => {
    const observador = new MutationObserver(() => {
      setTema(leerTema());
      setPreferencia(leerPreferencia());
    });
    observador.observe(document.documentElement, {
      attributeFilter: ["data-theme", "data-theme-pref"],
    });
    return () => observador.disconnect();
  }, []);

  const cambiar = useCallback((siguiente: PreferenciaDeTema) => {
    if (window.setTheme) {
      window.setTheme(siguiente);
    } else {
      document.documentElement.setAttribute("data-theme", resolver(siguiente));
      document.documentElement.setAttribute("data-theme-pref", siguiente);
    }
  }, []);

  return { tema, preferencia, cambiar };
}
