import { useSyncExternalStore } from "react";

export type DescansoDelServidor = { restante: number; total: number };

export type DescansoEnCurso = {
  sesionId: number | null;
  restante: number;
  total: number;
};

const MARGEN_PARA_AVISAR_MS = 2000;

const TOLERANCIA_MS = 1500;

type Interno = { sesionId: number | null; fin: number; total: number };

let actual: Interno | null = null;
let instantanea: DescansoEnCurso | null = null;
let vigenteDesde: { sesionId: number | null; instante: number } = { sesionId: null, instante: 0 };
let reloj: ReturnType<typeof setInterval> | null = null;
const oyentes = new Set<() => void>();

function avisar() {
  for (const oyente of oyentes) oyente();
}

function publicar(restante: number | null) {
  const siguiente =
    actual && restante !== null
      ? { sesionId: actual.sesionId, restante, total: actual.total }
      : null;
  const igual =
    siguiente === instantanea ||
    (siguiente !== null &&
      instantanea !== null &&
      siguiente.sesionId === instantanea.sesionId &&
      siguiente.restante === instantanea.restante &&
      siguiente.total === instantanea.total);
  if (igual) return;
  instantanea = siguiente;
  avisar();
}

function parar() {
  if (reloj !== null) clearInterval(reloj);
  reloj = null;
}

function tic() {
  if (!actual) return parar();
  const ahora = Date.now();
  const quedan = Math.ceil((actual.fin - ahora) / 1000);
  if (quedan > 0) return publicar(quedan);

  const fin = actual.fin;
  actual = null;
  parar();
  publicar(null);
  if (ahora - fin < MARGEN_PARA_AVISAR_MS) navigator.vibrate?.([200, 100, 200]);
}

function marcar(sesionId: number | null, instante: number) {
  vigenteDesde = { sesionId, instante };
}

function esViejo(sesionId: number | null, instante: number): boolean {
  return vigenteDesde.sesionId === sesionId && instante < vigenteDesde.instante;
}

export function poner(
  sesionId: number | null,
  segundos: number,
  total: number = segundos,
  desde: number = Date.now(),
) {
  marcar(sesionId, desde);
  const fin = desde + segundos * 1000;
  if (segundos <= 0 || fin <= Date.now()) return quitar(sesionId, desde);

  actual = { sesionId, fin, total };
  publicar(Math.ceil((fin - Date.now()) / 1000));
  if (reloj === null) reloj = setInterval(tic, 250);
}

export function quitar(sesionId: number | null = actual?.sesionId ?? null, desde = Date.now()) {
  marcar(sesionId, desde);
  if (actual && actual.sesionId !== sesionId) return;
  actual = null;
  parar();
  publicar(null);
}

export function alargar(segundos: number) {
  if (!actual) return;
  marcar(actual.sesionId, Date.now());
  actual = { ...actual, fin: actual.fin + segundos * 1000, total: actual.total + segundos };
  publicar(Math.ceil((actual.fin - Date.now()) / 1000));
}

export function sincronizar(
  sesionId: number | null,
  servidor: DescansoDelServidor | null,
  desde: number = Date.now(),
) {
  if (esViejo(sesionId, desde)) return;
  if (!servidor) return quitar(sesionId, desde);

  const fin = desde + servidor.restante * 1000;
  if (
    actual &&
    actual.sesionId === sesionId &&
    actual.total === servidor.total &&
    Math.abs(actual.fin - fin) < TOLERANCIA_MS
  ) {
    return marcar(sesionId, desde);
  }
  poner(sesionId, servidor.restante, servidor.total, desde);
}

function suscribir(avisame: () => void) {
  oyentes.add(avisame);
  return () => oyentes.delete(avisame);
}

export function useDescanso(): DescansoEnCurso | null {
  return useSyncExternalStore(suscribir, () => instantanea, () => instantanea);
}

export function _reiniciar() {
  actual = null;
  parar();
  vigenteDesde = { sesionId: null, instante: 0 };
  instantanea = null;
  avisar();
}
