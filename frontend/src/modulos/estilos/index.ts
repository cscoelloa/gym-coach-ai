import { perezosa, type RutaDeModulo } from "../tipos";

export const rutas: RutaDeModulo[] = [
  {
    ruta: "/estilos",
    pantalla: perezosa(() => import("./GuiaDeEstilos"), "GuiaDeEstilos"),
    acceso: "privada",
  },
];
