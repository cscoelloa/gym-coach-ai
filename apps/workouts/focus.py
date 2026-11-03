import math
from dataclasses import dataclass
from decimal import Decimal

from django.db.models import Count
from django.utils import timezone

from apps.metrics.loads import is_working_set, muscle_names, total_work

from . import history
from .models import SetLog


def contexto_de_foco(user, session, indice: int | None = None, ahora=None) -> dict:
    planificados = list(
        session.routine.exercises.select_related(
            "exercise", "exercise__target_muscle"
        ).order_by("order", "pk")
        if session.routine
        else []
    )

    if indice is None:
        indice = primer_pendiente(session) or 1
    indice = max(1, min(indice, len(planificados))) if planificados else 1
    actual = planificados[indice - 1] if planificados else None

    hechas: list[SetLog] = []
    filas: list[dict] = []
    ultima = mejor = sugerencia = None

    if actual:
        hechas = list(
            session.sets.filter(exercise=actual.exercise).order_by("set_number", "pk")
        )
        ultima = history.last_performance(user, actual.exercise, before_session=session)
        mejor = history.best_set(user, actual.exercise)
        sugerencia = history.progression_hint(
            user, actual.exercise, actual.target_reps_max, before_session=session
        )

        if hechas:
            peso_sugerido, reps_sugeridas = hechas[-1].weight_kg, hechas[-1].reps
        elif ultima and ultima.sets:
            peso_sugerido, reps_sugeridas = ultima.sets[-1]
        else:
            peso_sugerido, reps_sugeridas = None, None

        filas_totales = max(actual.target_sets or len(hechas) + 1, len(hechas))
        for numero in range(1, filas_totales + 1):
            registrada = hechas[numero - 1] if numero <= len(hechas) else None
            peso = registrada.weight_kg if registrada else peso_sugerido
            filas.append({
                "numero": numero,
                "serie_id": registrada.pk if registrada else None,
                "activa": registrada is None and numero == len(hechas) + 1,
                "peso": history.format_kg(peso),
                "reps": (
                    registrada.reps if registrada else (reps_sugeridas or actual.target_reps_min)
                ),
                "rpe": float(registrada.rpe) if registrada and registrada.rpe else None,
            })

    objetivo_total = sum(item.target_sets or 0 for item in planificados)
    hechas_total = session.sets.count()

    hechas_por_item = _repartir(planificados, _por_ejercicio(session))

    return {
        "sesion": {
            "id": session.pk,
            "fecha": session.date.isoformat(),
            "notas": session.notes,
            "terminada": session.finished_at is not None,
            "rutina": (
                {"id": session.routine.pk, "nombre": session.routine.name}
                if session.routine
                else None
            ),
        },
        "indice": indice,
        "total_ejercicios": len(planificados),
        "planificados": [
            {
                "id": item.pk,
                "nombre": item.exercise.name,
                "series": item.target_sets,
                "hechas": hechas,
            }
            for item, hechas in zip(planificados, hechas_por_item, strict=True)
        ],
        "siguiente": _siguiente_pendiente(planificados, hechas_por_item, indice),
        "actual": (
            {
                "id": actual.pk,
                "ejercicio_id": actual.exercise.pk,
                "nombre": actual.exercise.name,
                "slug": actual.exercise.slug,
                "imagen": actual.exercise.image.url if actual.exercise.image else None,
                "animacion": (
                    actual.exercise.animation.url if actual.exercise.animation else None
                ),
                "atribucion": actual.exercise.attribution,
                "series": actual.target_sets,
                "reps_min": actual.target_reps_min,
                "reps_max": actual.target_reps_max,
                "descanso": actual.rest_seconds,
                "unilateral": actual.exercise.is_unilateral,
                "completo": _completo(actual, len(hechas)),
            }
            if actual
            else None
        ),
        "filas": filas,
        "ultima_vez": (
            {
                "fecha": ultima.date.isoformat(),
                "series": [
                    [history.format_kg(peso), reps] for peso, reps in ultima.sets
                ],
                "por_lado": ultima.per_side,
            }
            if ultima
            else None
        ),
        "mejor": history.format_kg(mejor) if mejor else None,
        "sugerencia": sugerencia,
        "avance": {
            "hechas": hechas_total,
            "objetivo": objetivo_total,
        },
        "descanso_en_curso": estado_del_descanso(session, ahora or timezone.now()),
    }


def _completo(planificado, hechas: int) -> bool:
    return bool(planificado.target_sets) and hechas >= planificado.target_sets


def _planificados(session) -> list:
    if not session.routine:
        return []
    return list(session.routine.exercises.select_related("exercise").order_by("order", "pk"))


def _por_ejercicio(session) -> dict[int, int]:
    return dict(
        session.sets.values("exercise").annotate(n=Count("pk")).values_list("exercise", "n")
    )


def _repartir(planificados, por_ejercicio: dict[int, int]) -> list[int]:
    quedan = dict(por_ejercicio)
    ultima = {item.exercise_id: posicion for posicion, item in enumerate(planificados)}
    reparto = []
    for posicion, item in enumerate(planificados):
        disponibles = quedan.get(item.exercise_id, 0)
        if ultima[item.exercise_id] == posicion:
            tomadas = disponibles
        else:
            tomadas = min(disponibles, item.target_sets or 0)
        quedan[item.exercise_id] = disponibles - tomadas
        reparto.append(tomadas)
    return reparto


def _pendientes(planificados, hechas_por_item: list[int]) -> int:
    return sum(
        max((item.target_sets or 0) - hechas, 0)
        for item, hechas in zip(planificados, hechas_por_item, strict=True)
    )


def primer_pendiente(session) -> int | None:
    planificados = _planificados(session)
    hechas = _repartir(planificados, _por_ejercicio(session))
    for posicion, (item, n) in enumerate(zip(planificados, hechas, strict=True), start=1):
        if not _completo(item, n):
            return posicion
    return None


def _fila_de_la_serie(planificados, exercise_id: int, set_number: int):
    filas = [item for item in planificados if item.exercise_id == exercise_id]
    acumulado = 0
    for item in filas:
        acumulado += item.target_sets or 0
        if set_number <= acumulado:
            return item
    return filas[-1] if filas else None


def descanso_tras_registrar(session, serie) -> int | None:
    if session.finished_at:
        return None

    planificados = _planificados(session)
    if planificados:
        por_ejercicio = _por_ejercicio(session)
        despues = _pendientes(planificados, _repartir(planificados, por_ejercicio))
        antes_por_ejercicio = dict(por_ejercicio)
        antes_por_ejercicio[serie.exercise_id] = antes_por_ejercicio.get(serie.exercise_id, 1) - 1
        antes = _pendientes(planificados, _repartir(planificados, antes_por_ejercicio))
        if antes > 0 and despues == 0:
            return None

    fila = _fila_de_la_serie(planificados, serie.exercise_id, serie.set_number)
    segundos = fila.rest_seconds if fila else serie.exercise.default_rest
    return segundos or None


def estado_del_descanso(session, ahora) -> dict | None:
    if session.finished_at or not session.rest_ends_at:
        return None
    restante = (session.rest_ends_at - ahora).total_seconds()
    if restante <= 0:
        return None
    return {"restante": round(restante, 1), "total": session.rest_seconds or math.ceil(restante)}


def _siguiente_pendiente(planificados, hechas_por_item: list[int], indice: int) -> int | None:
    total = len(planificados)
    for paso in range(1, total):
        posicion = (indice - 1 + paso) % total
        if not _completo(planificados[posicion], hechas_por_item[posicion]):
            return posicion + 1
    return None


@dataclass(frozen=True)
class Record:
    ejercicio: str
    kg: str


def resumen_de_cierre(user, session) -> dict:
    series = list(
        session.sets.select_related("exercise", "exercise__target_muscle")
        .prefetch_related("exercise__secondary_muscles")
        .order_by("exercise__name", "set_number")
    )

    peso_corporal = _peso_corporal(user, session)

    tonelaje = Decimal("0")
    sin_cobertura = 0
    for serie in series:
        trabajo = total_work(serie, peso_corporal)
        if trabajo is None or serie.reps is None:
            sin_cobertura += 1
            continue
        tonelaje += trabajo * serie.reps

    musculos: dict[str, str] = {}
    for serie in series:
        musculos.update(muscle_names(serie.exercise))

    return {
        "sesion": {
            "id": session.pk,
            "fecha": session.date.isoformat(),
            "rutina": session.routine.name if session.routine else None,
            "notas": session.notes,
        },
        "duracion_minutos": _duracion(session),
        "series": len(series),
        "ejercicios": len({serie.exercise_id for serie in series}),
        "tonelaje_kg": round(float(tonelaje)),
        "series_sin_cobertura": sin_cobertura,
        "records": [
            {"ejercicio": record.ejercicio, "kg": record.kg}
            for record in _records(user, session, series)
        ],
        "musculos": sorted(musculos.values()),
    }


def _duracion(session) -> int | None:
    if not session.started_at or not session.finished_at:
        return None
    return round((session.finished_at - session.started_at).total_seconds() / 60)


def _peso_corporal(user, session) -> Decimal | None:
    from apps.bodyweight.models import BodyWeightEntry

    entrada = (
        BodyWeightEntry.objects.filter(user=user, date__lte=session.date)
        .order_by("-date")
        .first()
    )
    return entrada.weight_kg if entrada else None


def _records(user, session, series) -> list[Record]:
    ejercicios = {serie.exercise_id: serie.exercise for serie in series}
    if not ejercicios:
        return []

    previas = (
        SetLog.objects.filter(session__user=user, exercise_id__in=ejercicios)
        .exclude(session=session)
        .select_related("exercise")
    )

    mejor_previo: dict[int, Decimal] = {}
    for serie in previas:
        if not is_working_set(serie) or serie.weight_kg is None:
            continue
        actual = mejor_previo.get(serie.exercise_id)
        if actual is None or serie.weight_kg > actual:
            mejor_previo[serie.exercise_id] = serie.weight_kg

    records: dict[int, Decimal] = {}
    for serie in series:
        if not is_working_set(serie) or serie.weight_kg is None:
            continue
        tope = mejor_previo.get(serie.exercise_id)
        if tope is not None and serie.weight_kg <= tope:
            continue
        if tope is None:
            continue
        if serie.weight_kg > records.get(serie.exercise_id, Decimal("0")):
            records[serie.exercise_id] = serie.weight_kg

    return [
        Record(ejercicio=ejercicios[ejercicio_id].name, kg=history.format_kg(peso))
        for ejercicio_id, peso in records.items()
    ]
