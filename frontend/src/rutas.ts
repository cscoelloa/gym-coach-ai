export const RUTAS_DE_LA_SPA = [
  "/",
  "/estilos/",
  "/peso/",
  "/notificaciones/",
  "/ejercicios/",
  "/ejercicios/nuevo/",
  "/ejercicios/:slug/",
  "/plan/",
  "/plan/dia/:weekday/",
  "/programas/nuevo/",
  "/rutinas/nueva/",
  "/rutinas/:pk/",
  "/entrenamientos/",
  "/entrenamientos/:pk/",
  "/entrenamientos/:pk/cierre/",
  "/progreso/",
  "/metricas/",
  "/ia/generar/",
  "/ia/propuestas/:pk/",
  "/ia/analisis/",
  "/gestion/",
  "/gestion/ia/",
  "/gestion/generaciones/",
  "/gestion/usuarios/",
  "/gestion/catalogo/",
  "/perfil/",
  "/perfil/eliminar/",
  "/entrar/",
  "/registro/",
  "/sesion-cerrada/",
] as const;

function segmentos(camino: string): string[] {
  return camino.split("/").filter(Boolean);
}

export function esRutaDeLaSpa(url: string): boolean {
  const camino = segmentos(url.split("?")[0]!.split("#")[0]!);

  return RUTAS_DE_LA_SPA.some((ruta) => {
    const patron = segmentos(ruta);
    if (patron.length !== camino.length) return false;
    return patron.every(
      (trozo, indice) => trozo.startsWith(":") || trozo === camino[indice],
    );
  });
}
