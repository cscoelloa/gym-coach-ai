import type { RutaDeModulo } from "../tipos";
import { CierreDeEntrenamiento } from "./CierreDeEntrenamiento";
import { Entrenamientos } from "./Entrenamientos";
import { Entrenar } from "./foco/Entrenar";

export const rutas: RutaDeModulo[] = [
  { ruta: "/entrenamientos", pantalla: Entrenamientos, acceso: "privada" },
  { ruta: "/entrenamientos/:id/cierre", pantalla: CierreDeEntrenamiento, acceso: "privada" },
  { ruta: "/entrenamientos/:id", pantalla: Entrenar, acceso: "foco" },
];
