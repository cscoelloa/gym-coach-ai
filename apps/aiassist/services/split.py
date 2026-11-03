from dataclasses import dataclass

from apps.workouts.catalog import musculos_entrenables
from apps.workouts.models import Weekday
from apps.workouts.taxonomy import muscle_label

MIN_EJERCICIOS = 3
MAX_EJERCICIOS = 10

MAX_MUSCULOS_POR_DIA = 5

HORAS_DE_DESCANSO = 48

SIN_ESPERA = frozenset({"abs", "obliques", "calves", "forearms"})

DIAS = dict(Weekday.choices)


class RepartoInvalido(ValueError):
    pass


@dataclass(frozen=True)
class DiaDelReparto:
    weekday: int
    muscles: tuple[str, ...]
    emphasis: str | None
    exercises: int

    @property
    def etiqueta(self) -> str:
        return str(DIAS[self.weekday])

    @property
    def musculos_en_texto(self) -> str:
        return ", ".join(muscle_label(slug) for slug in self.muscles)


def parse_split(datos, *, user) -> list[DiaDelReparto]:
    if not isinstance(datos, list):
        raise RepartoInvalido("El reparto tiene que ser una lista de días.")

    permitidos = {slug for slug, _etiqueta, _n in musculos_entrenables(user)}
    dias: list[DiaDelReparto] = []
    vistos: set[int] = set()

    for entrada in datos:
        if not isinstance(entrada, dict):
            raise RepartoInvalido("Cada día del reparto tiene que ser un objeto.")

        try:
            weekday = int(entrada.get("weekday"))
        except (TypeError, ValueError) as exc:
            raise RepartoInvalido(
                "Cada día necesita su número de 0 (lunes) a 6 (domingo)."
            ) from exc
        if weekday not in DIAS:
            raise RepartoInvalido(f"«{weekday}» no es un día: van de 0 (lunes) a 6 (domingo).")
        if weekday in vistos:
            raise RepartoInvalido(f"{DIAS[weekday]} aparece dos veces en el reparto.")
        vistos.add(weekday)

        musculos = entrada.get("muscles") or []
        if not isinstance(musculos, list):
            raise RepartoInvalido(f"Los músculos de {DIAS[weekday]} tienen que ser una lista.")
        musculos = list(dict.fromkeys(str(m).strip() for m in musculos if str(m).strip()))

        if not musculos:
            continue

        if len(musculos) > MAX_MUSCULOS_POR_DIA:
            raise RepartoInvalido(
                f"{DIAS[weekday]} tiene {len(musculos)} músculos: como mucho "
                f"{MAX_MUSCULOS_POR_DIA}, o ninguno tendrá series suficientes."
            )

        desconocidos = [m for m in musculos if m not in permitidos]
        if desconocidos:
            raise RepartoInvalido(
                f"En {DIAS[weekday]} no se puede entrenar "
                + ", ".join(muscle_label(m) for m in desconocidos)
                + " con tu equipamiento. Elige otro músculo o completa el equipamiento"
                " de tu perfil."
            )

        emphasis = (entrada.get("emphasis") or "").strip() or None
        if emphasis and emphasis not in musculos:
            raise RepartoInvalido(
                f"El énfasis de {DIAS[weekday]} ({muscle_label(emphasis)}) no está entre los "
                "músculos de ese día."
            )

        try:
            ejercicios = int(entrada.get("exercises"))
        except (TypeError, ValueError) as exc:
            raise RepartoInvalido(
                f"Falta cuántos ejercicios quieres el {DIAS[weekday]}."
            ) from exc
        if not MIN_EJERCICIOS <= ejercicios <= MAX_EJERCICIOS:
            raise RepartoInvalido(
                f"Los ejercicios de {DIAS[weekday]} van de {MIN_EJERCICIOS} a {MAX_EJERCICIOS}."
            )
        if ejercicios < len(musculos):
            raise RepartoInvalido(
                f"{DIAS[weekday]} tiene {len(musculos)} músculos y solo {ejercicios} ejercicios: "
                "alguno se quedaría sin ninguno."
            )

        dias.append(DiaDelReparto(weekday, tuple(musculos), emphasis, ejercicios))

    if not dias:
        raise RepartoInvalido("Marca al menos un día de entrenamiento.")

    return sorted(dias, key=lambda dia: dia.weekday)


def format_split(split: list[DiaDelReparto]) -> str:
    por_dia = {dia.weekday: dia for dia in split}
    lineas = []
    for weekday, etiqueta in Weekday.choices:
        dia = por_dia.get(weekday)
        if dia is None:
            lineas.append(f"- {etiqueta}: DESCANSO (sin rutina)")
            continue
        linea = f"- {etiqueta}: {dia.musculos_en_texto} — exactamente {dia.exercises} ejercicios"
        if dia.emphasis:
            linea += f", con énfasis en {muscle_label(dia.emphasis)}"
        lineas.append(linea)
    return "\n".join(lineas)


DIAS_SUGERIDOS = {
    1: [0],
    2: [0, 3],
    3: [0, 2, 4],
    4: [0, 1, 3, 4],
    5: [0, 1, 2, 4, 5],
    6: [0, 1, 2, 3, 4, 5],
    7: [0, 1, 2, 3, 4, 5, 6],
}


def dias_sugeridos(cuantos: int | None) -> list[int]:
    return DIAS_SUGERIDOS.get(max(1, min(int(cuantos or 3), 7)), [0, 2, 4])


def musculos_del_reparto(split: list[DiaDelReparto]) -> tuple[list[str], list[str]]:
    todos = list(dict.fromkeys(m for dia in split for m in dia.muscles))
    enfasis = list(dict.fromkeys(dia.emphasis for dia in split if dia.emphasis))
    return todos, enfasis


def dias_consecutivos(dias: list[int]) -> list[tuple[int, int]]:
    if len(dias) < 2:
        return []
    pares = [(a, b) for a, b in zip(dias, dias[1:], strict=False) if b - a == 1]
    if len(dias) > 1 and dias[0] == 0 and dias[-1] == 6:
        pares.append((6, 0))
    return pares


def conflictos_de_recuperacion(split: list[DiaDelReparto]) -> list[str]:
    por_dia = {dia.weekday: dia for dia in split}
    problemas = []
    for anterior, siguiente in dias_consecutivos(sorted(por_dia)):
        repetidos = [
            m
            for m in por_dia[anterior].muscles
            if m in por_dia[siguiente].muscles and m not in SIN_ESPERA
        ]
        if repetidos:
            problemas.append(
                f"{DIAS[anterior]} y {DIAS[siguiente]} repiten "
                + ", ".join(muscle_label(m) for m in repetidos)
                + f". Un músculo necesita {HORAS_DE_DESCANSO} h para recuperarse: repártelos en "
                "esos dos días en vez de entrenarlos seguidos."
            )
    return problemas
