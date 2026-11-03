import { useCallback, useId, useRef, type KeyboardEvent, type ReactNode } from "react";
import { useSearchParams } from "react-router";

import { Icono, type NombreDeIcono } from "./Icono";

export type Pestana<T extends string> = {
  valor: T;
  etiqueta: string;
  icono?: NombreDeIcono;
  marca?: ReactNode;
};

export function useVista<T extends string>(
  valores: readonly T[],
  parametro = "vista",
): [T, (valor: T) => void] {
  const [params, setParams] = useSearchParams();
  const pedida = params.get(parametro) as T | null;
  const vista = pedida !== null && valores.includes(pedida) ? pedida : valores[0]!;
  const primera = valores[0];

  const cambiar = useCallback(
    (valor: T) =>
      setParams(
        (previos) => {
          const nuevos = new URLSearchParams(previos);
          if (valor === primera) nuevos.delete(parametro);
          else nuevos.set(parametro, valor);
          return nuevos;
        },
        { replace: true },
      ),
    [setParams, parametro, primera],
  );

  return [vista, cambiar];
}

export function Pestanas<T extends string>({
  opciones,
  valor,
  onCambio,
  etiqueta,
  children,
  className = "",
}: {
  opciones: ReadonlyArray<Pestana<T>>;
  valor: T;
  onCambio: (valor: T) => void;
  etiqueta: string;
  children: ReactNode;
  className?: string;
}) {
  const id = useId();
  const botones = useRef(new Map<T, HTMLButtonElement>());

  function teclado(evento: KeyboardEvent, indice: number) {
    const total = opciones.length;
    const destinos: Record<string, number> = {
      ArrowRight: (indice + 1) % total,
      ArrowLeft: (indice - 1 + total) % total,
      Home: 0,
      End: total - 1,
    };
    const destino = destinos[evento.key];
    if (destino === undefined) return;
    evento.preventDefault();
    const siguiente = opciones[destino]!.valor;
    onCambio(siguiente);
    botones.current.get(siguiente)?.focus();
  }

  return (
    <>
      <div role="tablist" aria-label={etiqueta} className={`tabs ${className}`.trim()}>
        {opciones.map((opcion, indice) => {
          const activa = opcion.valor === valor;
          return (
            <button
              key={opcion.valor}
              ref={(nodo) => {
                if (nodo) botones.current.set(opcion.valor, nodo);
                else botones.current.delete(opcion.valor);
              }}
              type="button"
              role="tab"
              id={`${id}-pestana-${opcion.valor}`}
              aria-selected={activa}
              {...(activa ? { "aria-controls": `${id}-panel` } : {})}
              tabIndex={activa ? 0 : -1}
              className="tab"
              onClick={() => onCambio(opcion.valor)}
              onKeyDown={(evento) => teclado(evento, indice)}
            >
              {opcion.icono && <Icono nombre={opcion.icono} className="size-[18px] shrink-0" />}
              {opcion.etiqueta}
              {opcion.marca}
            </button>
          );
        })}
      </div>
      <div
        role="tabpanel"
        id={`${id}-panel`}
        aria-labelledby={`${id}-pestana-${valor}`}
        tabIndex={0}
        className="tab-panel"
        key={valor}
      >
        {children}
      </div>
    </>
  );
}
