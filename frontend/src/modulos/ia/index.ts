import { perezosa, type RutaDeModulo } from "../tipos";

const cargar = () => import("./PantallasDeIa");

export const rutas: RutaDeModulo[] = [
  { ruta: "/ia/generar", pantalla: perezosa(cargar, "GenerarRutina"), acceso: "privada" },
  { ruta: "/ia/propuestas/:id", pantalla: perezosa(cargar, "PropuestaDeRutina"), acceso: "privada" },
  { ruta: "/ia/analisis", pantalla: perezosa(cargar, "AnalisisDeProgreso"), acceso: "privada" },
];
