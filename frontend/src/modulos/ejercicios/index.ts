import type { RutaDeModulo } from "../tipos";
import { EjercicioNuevo } from "./EjercicioNuevo";
import { Ejercicios } from "./Ejercicios";
import { FichaDeEjercicio } from "./FichaDeEjercicio";

export const rutas: RutaDeModulo[] = [
  { ruta: "/ejercicios", pantalla: Ejercicios, acceso: "privada" },
  { ruta: "/ejercicios/nuevo", pantalla: EjercicioNuevo, acceso: "privada" },
  { ruta: "/ejercicios/:slug", pantalla: FichaDeEjercicio, acceso: "privada" },
];
