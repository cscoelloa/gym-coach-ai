import { lazy, type ComponentType, type LazyExoticComponent } from "react";

export type Acceso = "publica" | "privada" | "foco" | "staff";

export type RutaDeModulo = {
  ruta: string;
  pantalla: ComponentType | LazyExoticComponent<ComponentType>;
  acceso: Acceso;
};

export function perezosa<M>(
  cargar: () => Promise<M>,
  nombre: keyof M,
): LazyExoticComponent<ComponentType> {
  return lazy(() => cargar().then((modulo) => ({ default: modulo[nombre] as ComponentType })));
}
