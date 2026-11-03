import type { ErroresPorCampo } from "@/api/cliente";

import type { OpcionesDePerfil, Perfil as DatosDePerfil } from "./api";

export type Cambiar = <C extends keyof DatosDePerfil>(campo: C, valor: DatosDePerfil[C]) => void;

export type PropsDeSeccion = {
  actual: DatosDePerfil;
  cambiar: Cambiar;
  porCampo: ErroresPorCampo;
};

export type { OpcionesDePerfil };
