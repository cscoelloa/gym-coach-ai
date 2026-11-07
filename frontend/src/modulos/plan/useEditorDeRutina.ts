import { useState } from "react";
import { useLocation, useNavigate } from "react-router";

import { ErrorDeApi } from "@/api/cliente";
import { useCambiosPendientes } from "@/lib/cambiosPendientes";
import type { Ejercicio } from "@/modulos/ejercicios/api";
import { useEmpezar } from "@/modulos/entrenar/api";

import {
  useBorrarRutina,
  useGuardarRutinaCompleta,
  usePlan,
  type ConfigDeEjercicio,
  type Rutina,
} from "./api";

export type Fila = ConfigDeEjercicio & {
  id?: number;
  clave: string;
  exercise: number;
  exercise_detail: Ejercicio;
};
export type Borrador = { name: string; description: string; exercises: Fila[] };
export type HojaDelEditor = "buscar" | "configurar" | "borrar" | null;

export function desdeRutina(rutina?: Rutina): Borrador {
  return {
    name: rutina?.name ?? "",
    description: rutina?.description ?? "",
    exercises: (rutina?.exercises ?? []).map((e) => ({ ...e, clave: String(e.id) })),
  };
}

function descansoPorDefecto(ejercicio: Ejercicio): number {
  return ["barbell", "olympic barbell"].includes(ejercicio.equipment) ? 180 : 90;
}

export function useEditorDeRutina(rutina?: Rutina) {
  const [borrador, setBorrador] = useState(() => desdeRutina(rutina));
  const [base, setBase] = useState(() => JSON.stringify(desdeRutina(rutina)));
  const [rutinaId, setRutinaId] = useState(rutina?.id);
  const [hoja, setHoja] = useState<HojaDelEditor>(null);
  const [elegido, setElegido] = useState<Fila | null>(null);
  const [origen, setOrigen] = useState<"buscar" | "lista">("buscar");
  const ubicacion = useLocation();
  const [exitoEn, setExitoEn] = useState<number | null>(() =>
    ubicacion.state?.guardada ? Date.now() : null,
  );
  const [errorLocal, setErrorLocal] = useState("");

  const guardar = useGuardarRutinaCompleta();
  const borrar = useBorrarRutina();
  const empezar = useEmpezar();
  const navegar = useNavigate();
  const plan = usePlan();

  const pendiente = JSON.stringify(borrador) !== base;
  const guardia = useCambiosPendientes(pendiente);
  const dias = plan.data?.rutinas.find((r) => r.id === rutinaId)?.dias ?? [];
  const campos = guardar.error instanceof ErrorDeApi ? guardar.error.porCampo : {};

  function cambiar(nuevo: Borrador) {
    setBorrador(nuevo);
    setExitoEn(null);
    setErrorLocal("");
    guardar.reset();
  }

  function seleccionar(ejercicio: Ejercicio) {
    const existente = borrador.exercises.find((e) => e.exercise === ejercicio.id);
    setElegido(
      existente ?? {
        clave: crypto.randomUUID(),
        exercise: ejercicio.id,
        exercise_detail: ejercicio,
        target_sets: 3,
        target_reps_min: 8,
        target_reps_max: 12,
        rest_seconds: descansoPorDefecto(ejercicio),
      },
    );
    setOrigen("buscar");
    setHoja("configurar");
  }

  function editar(fila: Fila) {
    setElegido(fila);
    setOrigen("lista");
    setHoja("configurar");
  }

  function mover(indice: number, delta: number) {
    const lista = [...borrador.exercises];
    [lista[indice], lista[indice + delta]] = [lista[indice + delta]!, lista[indice]!];
    cambiar({ ...borrador, exercises: lista });
  }

  function cerrarFicha() {
    setHoja(origen === "buscar" ? "buscar" : null);
  }

  function aplicar(fila: Fila) {
    const existe = borrador.exercises.some((e) => e.clave === fila.clave);
    cambiar({
      ...borrador,
      exercises: existe
        ? borrador.exercises.map((e) => (e.clave === fila.clave ? fila : e))
        : [...borrador.exercises, fila],
    });
    cerrarFicha();
  }

  function quitar(clave: string) {
    cambiar({ ...borrador, exercises: borrador.exercises.filter((e) => e.clave !== clave) });
    cerrarFicha();
  }

  function enviar() {
    if (!borrador.name.trim()) {
      setErrorLocal("Escribe un nombre para la rutina.");
      return;
    }
    if (!borrador.exercises.length) {
      setErrorLocal("Añade al menos un ejercicio antes de guardar.");
      return;
    }
    setErrorLocal("");
    guardar.mutate(
      {
        id: rutinaId,
        datos: {
          name: borrador.name.trim(),
          description: borrador.description,
          exercises: borrador.exercises.map(
            ({ id, exercise, target_sets, target_reps_min, target_reps_max, rest_seconds }) => ({
              ...(id ? { id } : {}),
              exercise,
              target_sets,
              target_reps_min,
              target_reps_max,
              rest_seconds,
            }),
          ),
        },
      },
      {
        onSuccess: (guardada) => {
          const nuevo = desdeRutina(guardada);
          guardia.limpiar();
          setBorrador(nuevo);
          setBase(JSON.stringify(nuevo));
          setRutinaId(guardada.id);
          setExitoEn(Date.now());
          if (!rutinaId) {
            navegar(`/rutinas/${guardada.id}/`, { replace: true, state: { guardada: true } });
          }
        },
      },
    );
  }

  function eliminar() {
    if (!rutinaId) return;
    borrar.mutate(rutinaId, {
      onSuccess: () => {
        guardia.limpiar();
        navegar("/plan/", { replace: true });
      },
    });
  }

  function entrenar() {
    if (!rutinaId) return;
    empezar.mutate(rutinaId, { onSuccess: (s) => navegar(`/entrenamientos/${s.id}/`) });
  }

  return {
    borrador,
    cambiar,
    rutinaId,
    pendiente,
    dias,
    campos,
    exitoEn,
    errorLocal,
    hoja,
    setHoja,
    elegido,
    seleccionar,
    editar,
    cerrarFicha,
    mover,
    aplicar,
    quitar,
    enviar,
    eliminar,
    entrenar,
    guardar,
    borrar,
    empezar,
  };
}

export type ControlDelEditor = ReturnType<typeof useEditorDeRutina>;
