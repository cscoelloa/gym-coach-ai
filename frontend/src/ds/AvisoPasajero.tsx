import { useEffect, useState, type CSSProperties, type ReactNode } from "react";

import { Aviso, type TonoDeAviso } from "./Aviso";

export function useUnRato(marca: unknown, duracion = 4000): boolean {
  const [visible, setVisible] = useState(Boolean(marca));

  useEffect(() => {
    if (!marca) {
      setVisible(false);
      return;
    }
    setVisible(true);
    const temporizador = window.setTimeout(() => setVisible(false), duracion);
    return () => window.clearTimeout(temporizador);
  }, [marca, duracion]);

  return visible && Boolean(marca);
}

export function AvisoPasajero({
  marca,
  tono = "exito",
  duracion = 4000,
  children,
}: {
  marca: unknown;
  tono?: TonoDeAviso;
  duracion?: number;
  children: ReactNode;
}) {
  const visible = useUnRato(marca, duracion);
  if (!visible) return null;
  return (
    <div
      key={String(marca)}
      className="aviso-pasajero"
      style={{ "--aviso-duracion": `${duracion}ms` } as CSSProperties}
    >
      <Aviso tono={tono}>{children}</Aviso>
    </div>
  );
}
