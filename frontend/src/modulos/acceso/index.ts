import type { RutaDeModulo } from "../tipos";

import { Entrar } from "./Entrar";
import { Registro } from "./Registro";
import { SesionCerrada } from "./SesionCerrada";

export const rutas: RutaDeModulo[] = [
  { ruta: "/entrar", pantalla: Entrar, acceso: "publica" },
  { ruta: "/registro", pantalla: Registro, acceso: "publica" },
  { ruta: "/sesion-cerrada", pantalla: SesionCerrada, acceso: "publica" },
];
