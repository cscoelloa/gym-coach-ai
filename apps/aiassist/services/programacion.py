from dataclasses import dataclass

from apps.workouts.models import Exercise
from apps.workouts.taxonomy import muscle_label

from ..models import PROGRAMACION_POR_DEFECTO, ProgrammingRules, TrainingGoal
from .split import DIAS

SECUNDARIOS_DE_UN_COMPUESTO = 2


@dataclass(frozen=True)
class Reglas:
    goal: str
    sets_min: int
    sets_max: int
    reps_min: int
    reps_max: int
    rest_min_compound: int
    rest_min_isolation: int
    sets_min_per_muscle_day: int

    @property
    def etiqueta(self) -> str:
        return TrainingGoal(self.goal).label

    def descanso(self, compuesto: bool) -> int:
        return self.rest_min_compound if compuesto else self.rest_min_isolation


_CAMPOS = tuple(PROGRAMACION_POR_DEFECTO[TrainingGoal.HYPERTROPHY])


def reglas_de(goal: str) -> Reglas:
    goal = goal if goal in TrainingGoal.values else TrainingGoal.HYPERTROPHY

    fila = ProgrammingRules.objects.filter(goal=goal).first()
    if fila is not None:
        return Reglas(goal=goal, **{campo: getattr(fila, campo) for campo in _CAMPOS})
    return Reglas(goal=goal, **PROGRAMACION_POR_DEFECTO[goal])


def resumen(reglas: Reglas) -> str:
    return (
        f"{reglas.sets_min}-{reglas.sets_max} series · "
        f"{reglas.reps_min}-{reglas.reps_max} repeticiones · "
        f"{reglas.rest_min_compound} s de descanso"
    )


def describir(reglas: Reglas) -> str:
    return "\n".join([
        f"Objetivo del entrenamiento: {reglas.etiqueta}.",
        f"- Series por ejercicio: entre {reglas.sets_min} y {reglas.sets_max}.",
        f"- Repeticiones: dentro de la banda {reglas.reps_min}-{reglas.reps_max}. Es una banda, "
        "no un número: lo pesado va abajo y el aislamiento arriba.",
        f"- Descanso: al menos {reglas.rest_min_compound} s en los compuestos y "
        f"{reglas.rest_min_isolation} s en los de aislamiento.",
        f"- Cada músculo que toque ese día necesita al menos {reglas.sets_min_per_muscle_day} "
        "series sumando todos sus ejercicios. Reparte: no gastes el día entero en un músculo.",
    ])


def es_compuesto(exercise: Exercise) -> bool:
    cuantos = getattr(exercise, "n_secundarios", None)
    if cuantos is None:
        cuantos = exercise.secondary_muscles.count()
    return cuantos >= SECUNDARIOS_DE_UN_COMPUESTO


def objetivo_por_musculo(reglas: Reglas, ejercicios: int, musculos: int) -> int:
    if musculos <= 0:
        return 0
    alcanzable = (ejercicios // musculos) * reglas.sets_min
    return max(1, min(reglas.sets_min_per_muscle_day, alcanzable))


def problemas(
    plan,
    catalogo: dict[str, Exercise],
    reglas: Reglas,
    *,
    dias: list[tuple] | None = None,
) -> list[str]:
    fallos: list[str] = []

    for rutina in plan.routines:
        for item in rutina.exercises:
            ejercicio = catalogo.get(item.external_id)
            if ejercicio is None:
                continue
            fallos.extend(_de_un_ejercicio(rutina.name, item, ejercicio, reglas))

    for dia, rutina in dias or []:
        fallos.extend(_de_volumen(dia, rutina, catalogo, reglas))
    return fallos


def _de_un_ejercicio(rutina: str, item, ejercicio: Exercise, reglas: Reglas) -> list[str]:
    compuesto = es_compuesto(ejercicio)
    nombre = ejercicio.name
    fallos = []

    if not reglas.sets_min <= item.sets <= reglas.sets_max:
        fallos.append(
            f"«{nombre}» ({rutina}) lleva {item.sets} series y para "
            f"{reglas.etiqueta.lower()} van de {reglas.sets_min} a {reglas.sets_max}"
        )

    if item.reps_min < reglas.reps_min or item.reps_max > reglas.reps_max:
        fallos.append(
            f"«{nombre}» ({rutina}) pide {item.reps_min}-{item.reps_max} repeticiones, "
            f"fuera del rango {reglas.reps_min}-{reglas.reps_max}"
        )

    descanso = reglas.descanso(compuesto)
    if item.rest_seconds < descanso:
        fallos.append(
            f"«{nombre}» ({rutina}) descansa {item.rest_seconds} s y necesita al menos {descanso}"
        )

    return fallos


def _de_volumen(dia, rutina, catalogo, reglas: Reglas) -> list[str]:
    series = dict.fromkeys(dia.muscles, 0)
    for item in rutina.exercises:
        ejercicio = catalogo.get(item.external_id)
        if ejercicio is None or not ejercicio.target_muscle_id:
            continue
        slug = ejercicio.target_muscle.slug
        if slug in series:
            series[slug] += item.sets

    objetivo = objetivo_por_musculo(reglas, dia.exercises, len(dia.muscles))
    flojos = [(musculo, cuantas) for musculo, cuantas in series.items() if cuantas < objetivo]
    if not flojos:
        return []

    detalle = ", ".join(f"{muscle_label(musculo)} ({cuantas})" for musculo, cuantas in flojos)
    return [
        f"{DIAS[dia.weekday]} se queda corto de series: {detalle}, y hacen falta {objetivo} "
        "por músculo"
    ]
