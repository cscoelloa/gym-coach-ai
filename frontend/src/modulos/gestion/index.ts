import { perezosa, type RutaDeModulo } from "../tipos";

const cargar = () => import("./PantallasDeGestion");

export const rutas: RutaDeModulo[] = [
  { ruta: "/gestion", pantalla: perezosa(cargar, "Resumen"), acceso: "staff" },
  { ruta: "/gestion/ia", pantalla: perezosa(cargar, "Ia"), acceso: "staff" },
  { ruta: "/gestion/generaciones", pantalla: perezosa(cargar, "Generaciones"), acceso: "staff" },
  { ruta: "/gestion/usuarios", pantalla: perezosa(cargar, "Cuentas"), acceso: "staff" },
  { ruta: "/gestion/catalogo", pantalla: perezosa(cargar, "Catalogo"), acceso: "staff" },
];
