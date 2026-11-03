import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router";

import { useEnLinea } from "@/lib/conexion";
import { useCuentaAtras } from "@/lib/cuentaAtras";

import {
  useAccionDeDescanso,
  useFinalizar,
  useFoco,
  useRegistrarSerie,
  type FilaDeSerie,
} from "../api";

const ALARGAR_SEGUNDOS = 30;

export function useEntrenar(sesionId: number) {
  const navegar = useNavigate();
  const cache = useQueryClient();
  const [params, setParams] = useSearchParams();
  const enUrl = params.get("ejercicio");
  const indice = enUrl === null ? null : Math.max(1, Number(enUrl) || 1);

  const foco = useFoco(sesionId, indice);
  const registrar = useRegistrarSerie(sesionId);
  const finalizar = useFinalizar(sesionId);
  const accionDeDescanso = useAccionDeDescanso(sesionId);
  const descanso = useCuentaAtras(sesionId);
  const enLinea = useEnLinea();

  const [peso, setPeso] = useState("");
  const [reps, setReps] = useState("");
  const [corrigiendo, setCorrigiendo] = useState<FilaDeSerie | null>(null);

  const datos = foco.data;
  const activa = datos?.filas.find((f) => f.activa);

  useEffect(() => {
    if (indice !== null || !datos) return;
    cache.setQueryData(["entrenar", sesionId, datos.indice], datos, {
      updatedAt: foco.dataUpdatedAt,
    });
    setParams(
      (previos) => {
        const nuevos = new URLSearchParams(previos);
        nuevos.set("ejercicio", String(datos.indice));
        return nuevos;
      },
      { replace: true },
    );
  }, [indice, datos]);

  useEffect(() => {
    if (datos) descanso.sincronizar(datos.descanso_en_curso, foco.dataUpdatedAt);
  }, [foco.dataUpdatedAt]);

  useEffect(() => {
    if (activa) {
      setPeso(activa.peso ?? "");
      setReps(activa.reps !== null ? String(activa.reps) : "");
    }
  }, [activa?.numero, datos?.actual?.id, activa?.peso, activa?.reps]);

  function irAEjercicio(siguiente: number) {
    const nuevos = new URLSearchParams(params);
    nuevos.set("ejercicio", String(siguiente));
    setParams(nuevos);
    window.scrollTo({ top: 0 });
  }

  function registrarSerie() {
    if (!datos?.actual) return;
    const yaEstabaCompleto = datos.actual.completo;

    registrar.mutate(
      {
        session: sesionId,
        exercise: datos.actual.ejercicio_id,
        ...(peso ? { weight_kg: peso } : {}),
        ...(reps ? { reps: Number(reps) } : {}),
      },
      {
        onSuccess: async (serie) => {
          descanso.sincronizar(serie.descanso);

          const { data: nuevo } = await foco.refetch();
          if (yaEstabaCompleto || !nuevo?.actual?.completo) return;
          if (nuevo.siguiente !== null) irAEjercicio(nuevo.siguiente);
        },
      },
    );
  }

  function alargarDescanso() {
    descanso.alargar(ALARGAR_SEGUNDOS);
    accionDeDescanso.mutate("alargar", {
      onSuccess: (respuesta) => descanso.sincronizar(respuesta.descanso),
      onError: () => void foco.refetch(),
    });
  }

  function saltarDescanso() {
    descanso.parar();
    accionDeDescanso.mutate("saltar", { onError: () => void foco.refetch() });
  }

  function terminar() {
    finalizar.mutate(undefined, {
      onSuccess: () => {
        descanso.parar();
        navegar(`/entrenamientos/${sesionId}/cierre/`, { replace: true });
      },
    });
  }

  const todoHecho = Boolean(datos?.actual?.completo) && datos?.siguiente === null;

  return {
    foco,
    datos,
    indice: datos?.indice ?? indice ?? 1,
    activa,
    peso,
    setPeso,
    reps,
    setReps,
    corrigiendo,
    setCorrigiendo,
    registrar,
    registrarSerie,
    finalizar,
    terminar,
    irAEjercicio,
    descanso,
    alargarDescanso,
    saltarDescanso,
    enLinea,
    todoHecho,
  };
}

export type Entreno = ReturnType<typeof useEntrenar>;
