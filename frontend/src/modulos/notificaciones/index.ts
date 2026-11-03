import type { RutaDeModulo } from "../tipos";

import { Notificaciones } from "./Notificaciones";

export const rutas: RutaDeModulo[] = [
  { ruta: "/notificaciones", pantalla: Notificaciones, acceso: "privada" },
];
