import * as acceso from "./acceso";
import * as ejercicios from "./ejercicios";
import * as entrenar from "./entrenar";
import * as estilos from "./estilos";
import * as gestion from "./gestion";
import * as ia from "./ia";
import * as inicio from "./inicio";
import * as notificaciones from "./notificaciones";
import * as perfil from "./perfil";
import * as peso from "./peso";
import * as plan from "./plan";
import * as progreso from "./progreso";
import type { RutaDeModulo } from "./tipos";

export const RUTAS: RutaDeModulo[] = [
  ...acceso.rutas,
  ...inicio.rutas,
  ...entrenar.rutas,
  ...plan.rutas,
  ...ejercicios.rutas,
  ...progreso.rutas,
  ...peso.rutas,
  ...perfil.rutas,
  ...notificaciones.rutas,
  ...ia.rutas,
  ...gestion.rutas,
  ...estilos.rutas,
];

export type { Acceso, RutaDeModulo } from "./tipos";
