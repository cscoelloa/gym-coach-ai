import { useCallback } from "react";

import * as descanso from "./descanso";

export function useCuentaAtras(sesionId: number | null = null) {
  const enCurso = descanso.useDescanso();
  const mio = enCurso && enCurso.sesionId === sesionId ? enCurso : null;

  const arrancar = useCallback(
    (segundos: number) => descanso.poner(sesionId, segundos),
    [sesionId],
  );
  const alargar = useCallback((segundos: number) => descanso.alargar(segundos), []);
  const parar = useCallback(() => descanso.quitar(sesionId), [sesionId]);
  const sincronizar = useCallback(
    (servidor: descanso.DescansoDelServidor | null, desde?: number) =>
      descanso.sincronizar(sesionId, servidor, desde),
    [sesionId],
  );

  return {
    restante: mio?.restante ?? null,
    total: mio?.total ?? 0,
    arrancar,
    alargar,
    parar,
    sincronizar,
  };
}
