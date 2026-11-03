import type { RutaDeModulo } from "../tipos";
import { EliminarCuenta } from "./EliminarCuenta";
import { Perfil } from "./Perfil";

export const rutas: RutaDeModulo[] = [
  { ruta: "/perfil", pantalla: Perfil, acceso: "privada" },
  { ruta: "/perfil/eliminar", pantalla: EliminarCuenta, acceso: "privada" },
];
