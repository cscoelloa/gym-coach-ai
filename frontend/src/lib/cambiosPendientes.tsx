import { createContext, useContext, useEffect, useRef, useState, type ReactNode } from "react";
import { useBlocker } from "react-router";
import { Confirmacion } from "@/ds/Confirmacion";

const TITULO = "Cambios sin guardar";
const MENSAJE = "Si sales ahora se descartan los cambios que todavía no has guardado.";

type Guardia = {
  marcar: (valor: boolean) => void;
  confirmar: () => Promise<boolean>;
  limpiar: () => void;
};

const Contexto = createContext<Guardia>({
  marcar: () => {},
  confirmar: () => Promise.resolve(true),
  limpiar: () => {},
});

export function CambiosPendientes({ children }: { children: ReactNode }) {
  const pendiente = useRef(false);
  const [preguntando, setPreguntando] = useState(false);
  const enCurso = useRef<{ espera: Promise<boolean>; responder: (salir: boolean) => void } | null>(null);
  const guardia = useRef<Guardia>({
    marcar: (nuevo: boolean) => { pendiente.current = nuevo; },
    limpiar: () => { pendiente.current = false; },
    confirmar: () => {
      if (!pendiente.current) return Promise.resolve(true);
      if (!enCurso.current) {
        let responder!: (salir: boolean) => void;
        const espera = new Promise<boolean>(resolver => { responder = resolver; });
        enCurso.current = { espera, responder };
        setPreguntando(true);
      }
      return enCurso.current.espera;
    },
  });
  function responder(salir: boolean) {
    const pregunta = enCurso.current;
    enCurso.current = null;
    setPreguntando(false);
    pregunta?.responder(salir);
  }
  return <Contexto.Provider value={guardia.current}>
    {children}
    {preguntando && <Confirmacion titulo={TITULO} mensaje={MENSAJE}
      confirmar="Salir sin guardar" cancelar="Seguir editando"
      onConfirmar={() => responder(true)} onCancelar={() => responder(false)} />}
  </Contexto.Provider>;
}

export const useConfirmarSalida = () => useContext(Contexto);

export function useCambiosPendientes(pendiente: boolean) {
  const contexto = useConfirmarSalida();
  useEffect(() => {
    contexto.marcar(pendiente);
    const antesDeSalir = (e: BeforeUnloadEvent) => {
      if (pendiente) { e.preventDefault(); e.returnValue = ""; }
    };
    window.addEventListener("beforeunload", antesDeSalir);
    return () => { contexto.limpiar(); window.removeEventListener("beforeunload", antesDeSalir); };
  }, [pendiente, contexto]);
  const bloqueo = useBlocker(({ currentLocation, nextLocation }) =>
    pendiente && currentLocation.pathname !== nextLocation.pathname,
  );
  const actual = useRef(bloqueo);
  actual.current = bloqueo;
  useEffect(() => {
    if (bloqueo.state !== "blocked") return;
    let vivo = true;
    void contexto.confirmar().then(salir => {
      if (!vivo || actual.current.state !== "blocked") return;
      if (salir) actual.current.proceed(); else actual.current.reset();
    });
    return () => { vivo = false; };
  }, [bloqueo.state, contexto]);
  return contexto;
}
