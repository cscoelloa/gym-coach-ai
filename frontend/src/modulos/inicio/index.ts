import type { RutaDeModulo } from "../tipos";

import { Inicio } from "./Inicio";

export const rutas: RutaDeModulo[] = [{ ruta: "/", pantalla: Inicio, acceso: "privada" }];

export { comoFecha, QueTocaHoy } from "./TarjetaDeHoy";
