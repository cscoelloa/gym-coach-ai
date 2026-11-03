import type { RutaDeModulo } from "../tipos";

import { Metricas } from "./Metricas";
import { Progreso } from "./Progreso";

export const rutas: RutaDeModulo[] = [
  { ruta: "/progreso", pantalla: Progreso, acceso: "privada" },
  { ruta: "/metricas", pantalla: Metricas, acceso: "privada" },
];
