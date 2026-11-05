import type { RutaDeModulo } from "../tipos";
import { DetalleDelDia } from "./DetalleDelDia";
import { EditorDeRutina } from "./EditorDeRutina";
import { Plan } from "./Plan";
import { ProgramaNuevo, RutinaNueva } from "./RutinaNueva";

export const rutas: RutaDeModulo[] = [
  { ruta: "/plan", pantalla: Plan, acceso: "privada" },
  { ruta: "/plan/dia/:weekday", pantalla: DetalleDelDia, acceso: "privada" },
  { ruta: "/programas/nuevo", pantalla: ProgramaNuevo, acceso: "privada" },
  { ruta: "/rutinas/nueva", pantalla: RutinaNueva, acceso: "privada" },
  { ruta: "/rutinas/:id", pantalla: EditorDeRutina, acceso: "privada" },
];
