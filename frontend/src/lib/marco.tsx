import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";

type Marco = {
  titulo: string | null;
  compacta: boolean;
  publicar: (titulo: string | null) => void;
  observar: (encabezado: HTMLElement | null) => void;
};

const SIN_MARCO: Marco = {
  titulo: null,
  compacta: false,
  publicar: () => {},
  observar: () => {},
};

const Contexto = createContext<Marco>(SIN_MARCO);

const ALTO_DE_LA_BARRA = 52;

export function ProveedorDeMarco({ children }: { children: ReactNode }) {
  const [titulo, setTitulo] = useState<string | null>(null);
  const [compacta, setCompacta] = useState(false);
  const observador = useRef<IntersectionObserver | null>(null);

  const observar = useCallback((encabezado: HTMLElement | null) => {
    observador.current?.disconnect();
    observador.current = null;
    setCompacta(false);

    if (!encabezado || typeof IntersectionObserver === "undefined") return;

    observador.current = new IntersectionObserver(
      ([entrada]) => {
        if (!entrada) return;
        setCompacta(!entrada.isIntersecting && entrada.boundingClientRect.top < ALTO_DE_LA_BARRA);
      },
      { rootMargin: `-${ALTO_DE_LA_BARRA}px 0px 0px 0px` },
    );
    observador.current.observe(encabezado);
  }, []);

  useEffect(() => () => observador.current?.disconnect(), []);

  const valor = useMemo(
    () => ({ titulo, compacta, publicar: setTitulo, observar }),
    [titulo, compacta, observar],
  );

  return <Contexto.Provider value={valor}>{children}</Contexto.Provider>;
}

export function useMarco(): Marco {
  return useContext(Contexto);
}

export function useTituloDeLaPantalla(titulo: string) {
  const { publicar, observar } = useMarco();

  useEffect(() => {
    publicar(titulo);
    return () => publicar(null);
  }, [titulo, publicar]);

  return observar;
}
