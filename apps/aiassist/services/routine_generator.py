import logging
import re
import unicodedata
from collections import Counter, defaultdict
from itertools import zip_longest

from django.conf import settings
from django.db import transaction
from django.db.models import Count

from apps.metrics.services import for_ai as metrics_for_ai
from apps.workouts.models import (
    Exercise,
    Program,
    Routine,
    RoutineExercise,
    ScheduleEntry,
    Weekday,
)
from apps.workouts.taxonomy import BodyPart, muscle_label

from ..models import AIGeneration, GenerationKind, GenerationStatus, PromptKey, TrainingGoal
from ..providers import ProviderError, ProviderRefusal, get_provider
from ..providers.factory import active_vector_store_ids
from ..schemas import RoutinePlan
from . import programacion, prompts
from .limits import check_quota
from .split import (
    DIAS,
    SIN_ESPERA,
    DiaDelReparto,
    dias_consecutivos,
    format_split,
    musculos_del_reparto,
)

logger = logging.getLogger(__name__)

MAX_CANDIDATES = 260

PER_MUSCLE = 18
PER_EMPHASIS = 28

PER_MUSCLE_SIN_REPARTO = 8

EQUIPMENT_PRIORITY = [
    "barbell", "dumbbell", "cable", "leverage machine", "body weight",
    "smith machine", "olympic barbell", "ez barbell", "kettlebell", "band",
]

_PRIORIDAD = {code: index for index, code in enumerate(EQUIPMENT_PRIORITY)}

_LASTRE_DE_LO_RARO = len(EQUIPMENT_PRIORITY) + 2

_NO_ES_FUERZA = ("stretch",)

_VARIANTE_COSMETICA = re.compile(
    r"\s*\((?:male|female|back pov|side pov|front pov|version \d+)\)\s*$", re.IGNORECASE
)

MAX_ATTEMPTS = 3


class GenerationFailed(Exception):
    pass


class NoCandidates(GenerationFailed):
    pass


class ProviderUnavailable(GenerationFailed):
    pass


class UnusableOutput(GenerationFailed):
    pass


def _sin_variantes(exercises: list[Exercise]) -> list[Exercise]:
    vistos: dict[str, Exercise] = {}
    for exercise in sorted(exercises, key=lambda ex: (len(ex.name), ex.name)):
        clave = _VARIANTE_COSMETICA.sub("", exercise.name).strip().casefold()
        vistos.setdefault(clave, exercise)
    return list(vistos.values())


def _mejores(exercises: list[Exercise], cuota: int) -> list[Exercise]:
    por_material: dict[str, list[Exercise]] = defaultdict(list)
    for exercise in _sin_variantes(exercises):
        por_material[exercise.equipment].append(exercise)

    ordenados: list[tuple[int, int, str, Exercise]] = []
    for material, lista in por_material.items():
        lastre = _PRIORIDAD.get(material, _LASTRE_DE_LO_RARO)
        lista.sort(key=lambda ex: (-ex.n_secundarios, ex.name))
        for puesto, exercise in enumerate(lista):
            ordenados.append((puesto + lastre, lastre, exercise.name, exercise))

    ordenados.sort(key=lambda fila: fila[:3])
    return [exercise for *_clave, exercise in ordenados[:cuota]]


def select_candidates(
    user,
    *,
    muscles: list[str] | None = None,
    emphasis: list[str] | None = None,
    limit: int = MAX_CANDIDATES,
) -> list[Exercise]:
    queryset = (
        Exercise.objects.filter(is_global=True)
        .exclude(body_part=BodyPart.CARDIO)
        .exclude(target_muscle__isnull=True)
        .select_related("target_muscle")
        .annotate(n_secundarios=Count("secondary_muscles"))
    )
    for palabra in _NO_ES_FUERZA:
        queryset = queryset.exclude(name__icontains=palabra)

    if equipment := (user.available_equipment or []):
        queryset = queryset.filter(equipment__in=equipment)
    if muscles:
        queryset = queryset.filter(target_muscle__slug__in=list(muscles))

    por_musculo: dict[str, list[Exercise]] = defaultdict(list)
    for exercise in queryset:
        por_musculo[exercise.target_muscle.slug].append(exercise)

    con_enfasis = set(emphasis or ())
    cuota_base = PER_MUSCLE if muscles else PER_MUSCLE_SIN_REPARTO
    listas = [
        _mejores(por_musculo[slug], PER_EMPHASIS if slug in con_enfasis else cuota_base)
        for slug in sorted(por_musculo)
    ]

    rondas = zip_longest(*listas)
    return [ex for ronda in rondas for ex in ronda if ex is not None][:limit]


def generate_routine(
    user,
    *,
    notes: str = "",
    days_per_week: int | None = None,
    split: list[DiaDelReparto] | None = None,
    training_goal: str = TrainingGoal.HYPERTROPHY,
) -> AIGeneration:
    check_quota(user, GenerationKind.ROUTINE)
    reglas = programacion.reglas_de(training_goal)

    musculos, enfasis = musculos_del_reparto(split) if split else ([], [])
    candidates = select_candidates(user, muscles=musculos or None, emphasis=enfasis)
    if not candidates:
        raise NoCandidates(
            "No hay ejercicios que encajen con tu equipamiento. Revisa tu perfil."
        )

    catalogo = {exercise.external_id: exercise for exercise in candidates}
    prompt = prompts.get_prompt(PromptKey.ROUTINE_GENERATION)
    provider = get_provider()

    context = {
        "perfil": prompts.format_profile(user),
        "objetivo": user.get_goal_display(),
        "dias_disponibles": (
            len(split) if split else (days_per_week or user.available_days_per_week)
        ),
        "reparto": format_split(split) if split else "",
        "programacion": programacion.describir(reglas),
        "equipamiento": prompts.format_equipment(user),
        "lesiones": prompts.as_data(
            user.injuries_notes, "datos_usuario", max_chars=settings.PROMPT_MAX_INJURIES_CHARS
        ),
        "peticion": prompts.as_data(notes, "peticion_usuario"),
        "metricas": prompts.format_metrics(metrics_for_ai(user)),
        "candidatos": prompts.format_candidates(candidates),
    }
    system, user_message = prompts.render(prompt, context)

    vector_store_ids = active_vector_store_ids() if provider.supports_rag else []

    last_error = ""
    last_result = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            result = provider.generate_structured(
                system=system,
                user=user_message,
                schema=RoutinePlan,
                vector_store_ids=(vector_store_ids or None) if attempt == 1 else None,
            )
        except ProviderRefusal as exc:
            _log_failure(
                user, provider, system, GenerationStatus.REFUSED, str(exc),
                split=split, reglas=reglas,
            )
            raise ProviderUnavailable(f"El modelo rechazó la petición: {exc}") from exc
        except ProviderError as exc:
            _log_failure(
                user, provider, system, GenerationStatus.ERROR, str(exc),
                split=split, reglas=reglas,
            )
            raise ProviderUnavailable(f"Fallo al hablar con el proveedor: {exc}") from exc

        problems = validate_plan(result.parsed, catalogo, split=split, reglas=reglas)
        if not problems:
            return _log_success(
                user, provider, system, user_message, result, split=split, reglas=reglas
            )

        last_error = "; ".join(problems)
        last_result = result
        logger.info("Intento %s inválido: %s", attempt, last_error)
        if attempt < MAX_ATTEMPTS:
            user_message += (
                f"\n\nTu respuesta anterior no era válida: {last_error}\n"
                + _how_to_fix(problems, catalogo)
            )

    _log_failure(
        user, provider, system, GenerationStatus.ERROR, last_error,
        result=last_result, split=split, reglas=reglas,
    )
    raise UnusableOutput(
        f"El modelo no devolvió una rutina válida tras {MAX_ATTEMPTS} intentos: {last_error}"
    )


FIXES = {
    "identificadores": (
        "Usa ÚNICAMENTE identificadores que aparezcan literalmente en la lista de candidatos. "
        "No uses ninguno que recuerdes de otra fuente."
    ),
    "apuntan a rutinas": (
        "En cada día del calendario, copia el nombre de la rutina **exactamente** como lo "
        "escribiste en la lista de rutinas, carácter por carácter. Si un día es de descanso, "
        "deja el nombre vacío."
    ),
    "siete días": "Devuelve exactamente siete días, del 0 al 6, cada uno una sola vez.",
    "mismo nombre": "Ponle a cada rutina un nombre distinto.",
    "no tiene ejercicios": "Toda rutina tiene que llevar al menos un ejercicio.",
    "no coinciden con el reparto": (
        "Entrena EXACTAMENTE los días del reparto y deja el resto en descanso, con "
        "`routine_name` vacío. No añadas días ni quites ninguno."
    ),
    "ejercicios y el reparto pide": (
        "Cada día tiene que llevar el número EXACTO de ejercicios que pide el reparto: ni uno "
        "más ni uno menos."
    ),
    "sin ningún ejercicio de": (
        "Cada músculo que el reparto nombra para un día necesita al menos un ejercicio cuyo "
        "músculo OBJETIVO sea ese, no uno donde participe de refuerzo."
    ),
    "énfasis": (
        "El músculo con énfasis lleva al menos dos ejercicios con ese objetivo, y ningún otro "
        "músculo de ese día puede llevar más que él."
    ),
    "días seguidos": (
        "No repitas el mismo músculo objetivo en dos días consecutivos: necesita 48 h para "
        "recuperarse. Cambia los ejercicios de uno de los dos días por otros del reparto."
    ),
    "repetido": "No pongas dos veces el mismo ejercicio en la misma rutina.",
    "series y para": (
        "Ajusta las series de cada ejercicio al rango del objetivo. Una o dos series por "
        "ejercicio no es el estímulo que pide ese objetivo, por muchos ejercicios que pongas."
    ),
    "fuera del rango": (
        "Corrige las repeticiones: los ejercicios compuestos y los de aislamiento tienen rangos "
        "distintos, y los dos están escritos arriba."
    ),
    "descansa": (
        "Sube el descanso hasta el mínimo del objetivo. Con menos, la serie siguiente cae por "
        "fatiga acumulada y no por el estímulo que buscas."
    ),
    "corto de series": (
        "Reparte las series entre los músculos del día hasta llegar al mínimo de cada uno. Si "
        "hace falta, cambia un ejercicio por otro cuyo objetivo sea el músculo que se queda corto."
    ),
}


def _how_to_fix(problems: list[str], catalogo: dict[str, Exercise] | None = None) -> str:
    instrucciones = [
        texto for clave, texto in FIXES.items() if any(clave in p for p in problems)
    ]
    if catalogo and any("identificadores" in p for p in problems):
        instrucciones.append(
            "Los únicos identificadores válidos son estos, y no hay más: "
            + ", ".join(sorted(catalogo))
        )
    return "\n".join(instrucciones) or "Corrige la respuesta respetando el esquema."


def _normalize(name: str) -> str:
    descompuesto = unicodedata.normalize("NFKD", name)
    return " ".join(
        "".join(c for c in descompuesto if not unicodedata.combining(c)).casefold().split()
    )


def resolve_routine_name(name: str, defined: list[str]) -> str | None:
    if not name.strip():
        return None

    por_exacto = {d: d for d in defined}
    if name.strip() in por_exacto:
        return name.strip()

    objetivo = _normalize(name)
    normalizados = {d: _normalize(d) for d in defined}

    iguales = [d for d, n in normalizados.items() if n == objetivo]
    if len(iguales) == 1:
        return iguales[0]

    contenidos = [d for d, n in normalizados.items() if objetivo in n or n in objetivo]
    if len(contenidos) == 1:
        return contenidos[0]

    return None


def resolve_schedule(plan: RoutinePlan) -> tuple[dict[int, str | None], set[str]]:
    definidos = [routine.name.strip() for routine in plan.routines]

    asignado: dict[int, str | None] = {}
    sin_resolver: set[str] = set()
    for day in plan.schedule:
        canonico = resolve_routine_name(day.routine_name, definidos)
        asignado[day.weekday] = canonico
        if day.routine_name.strip() and canonico is None:
            sin_resolver.add(day.routine_name.strip())

    return asignado, sin_resolver


def validate_plan(
    plan: RoutinePlan,
    catalogo: dict[str, Exercise],
    *,
    split: list[DiaDelReparto] | None = None,
    reglas: programacion.Reglas | None = None,
) -> list[str]:
    problems = []

    weekdays = [day.weekday for day in plan.schedule]
    if sorted(weekdays) != list(range(7)):
        problems.append(
            f"deben ser los siete días de 0 a 6 sin repetir, y llegaron {sorted(weekdays)}"
        )

    if not plan.routines:
        problems.append("el programa no trae ninguna rutina")

    nombres = [routine.name.strip() for routine in plan.routines]
    repetidos = {n for n in nombres if nombres.count(n) > 1}
    if repetidos:
        problems.append(
            "hay rutinas con el mismo nombre y no se pueden distinguir: "
            + ", ".join(sorted(repetidos))
        )

    _, huerfanos = resolve_schedule(plan)
    if huerfanos:
        problems.append(
            "estos días apuntan a rutinas que no has definido: "
            + ", ".join(sorted(huerfanos))
            + ". Las definidas son: "
            + ", ".join(f"«{n}»" for n in nombres)
        )

    unknown = {
        item.external_id
        for routine in plan.routines
        for item in routine.exercises
        if item.external_id not in catalogo
    }
    if unknown:
        muestra = ", ".join(sorted(unknown)[:5])
        problems.append(f"estos identificadores no están en la lista de candidatos: {muestra}")

    for routine in plan.routines:
        if not routine.exercises:
            problems.append(f"la rutina «{routine.name}» no tiene ejercicios")
        ids = [item.external_id for item in routine.exercises]
        if duplicados := {i for i in ids if ids.count(i) > 1}:
            problems.append(
                f"la rutina «{routine.name}» trae el mismo ejercicio repetido: "
                + ", ".join(sorted(duplicados))
            )

    if split and not unknown:
        problems.extend(_problemas_del_reparto(plan, catalogo, split))

    if reglas is not None and not unknown:
        problems.extend(
            programacion.problemas(plan, catalogo, reglas, dias=_dias_con_rutina(plan, split))
        )

    return problems


def _dias_con_rutina(plan: RoutinePlan, split: list[DiaDelReparto] | None) -> list[tuple]:
    if not split:
        return []

    por_nombre = {rutina.name.strip(): rutina for rutina in plan.routines}
    asignado, _ = resolve_schedule(plan)

    pares = []
    for dia in split:
        nombre = asignado.get(dia.weekday)
        rutina = por_nombre.get(nombre) if nombre else None
        if rutina is not None:
            pares.append((dia, rutina))
    return pares


def _musculos_por_dia(
    plan: RoutinePlan, catalogo: dict[str, Exercise]
) -> dict[int, list[str]]:
    por_nombre = {routine.name.strip(): routine for routine in plan.routines}
    asignado, _ = resolve_schedule(plan)

    por_dia: dict[int, list[str]] = {}
    for weekday, nombre in asignado.items():
        routine = por_nombre.get(nombre) if nombre else None
        if routine is None:
            continue
        por_dia[weekday] = [
            catalogo[item.external_id].target_muscle.slug
            for item in routine.exercises
            if item.external_id in catalogo and catalogo[item.external_id].target_muscle_id
        ]
    return por_dia


def _problemas_del_reparto(
    plan: RoutinePlan, catalogo: dict[str, Exercise], split: list[DiaDelReparto]
) -> list[str]:
    problems: list[str] = []
    por_dia = _musculos_por_dia(plan, catalogo)
    pedido = {dia.weekday: dia for dia in split}

    entrenados = set(por_dia)
    if entrenados != set(pedido):
        faltan = sorted(set(pedido) - entrenados)
        sobran = sorted(entrenados - set(pedido))
        detalle = []
        if faltan:
            detalle.append("faltan " + ", ".join(str(DIAS[d]) for d in faltan))
        if sobran:
            detalle.append("sobran " + ", ".join(str(DIAS[d]) for d in sobran))
        problems.append("los días entrenados no coinciden con el reparto: " + " y ".join(detalle))

    for weekday, dia in sorted(pedido.items()):
        musculos = por_dia.get(weekday)
        if musculos is None:
            continue

        if len(musculos) != dia.exercises:
            problems.append(
                f"{DIAS[weekday]} trae {len(musculos)} ejercicios y el reparto pide "
                f"{dia.exercises}"
            )

        cuenta = Counter(musculos)
        if sin_cubrir := [m for m in dia.muscles if not cuenta[m]]:
            problems.append(
                f"{DIAS[weekday]} se queda sin ningún ejercicio de "
                + ", ".join(muscle_label(m) for m in sin_cubrir)
            )

        if dia.emphasis:
            suyos = cuenta[dia.emphasis]
            mayor = max(cuenta.values(), default=0)
            if suyos < 2 or suyos < mayor:
                problems.append(
                    f"{DIAS[weekday]} pide énfasis en {muscle_label(dia.emphasis)} y solo lleva "
                    f"{suyos} ejercicio(s) suyos"
                )

    for anterior, siguiente in dias_consecutivos(sorted(por_dia)):
        repetidos = sorted(
            {m for m in por_dia[anterior] if m in por_dia[siguiente] and m not in SIN_ESPERA}
        )
        if repetidos:
            problems.append(
                f"{DIAS[anterior]} y {DIAS[siguiente]} son días seguidos y repiten "
                + ", ".join(muscle_label(m) for m in repetidos)
            )

    return problems


@transaction.atomic
def apply_plan(generation: AIGeneration, *, activate: bool = True) -> Program:
    if generation.programs.exists():
        raise GenerationFailed("Esta generación ya se aplicó.")

    plan = RoutinePlan.model_validate(generation.parsed_output)

    program = Program.objects.create(
        user=generation.user,
        name=plan.name[:120],
        description=plan.description,
        source=Program.Source.AI,
        generation=generation,
        is_active=activate,
    )
    if activate:
        program.activate()

    by_external_id = {
        exercise.external_id: exercise
        for exercise in Exercise.objects.filter(
            external_id__in=[
                item.external_id for routine in plan.routines for item in routine.exercises
            ]
        )
    }

    creadas: dict[str, Routine] = {}
    for routine_plan in plan.routines:
        routine = Routine.objects.create(
            user=generation.user,
            name=routine_plan.name[:120],
            source=Routine.Source.AI,
            generation=generation,
        )
        creadas[routine_plan.name.strip()] = routine

        for order, item in enumerate(routine_plan.exercises):
            exercise = by_external_id.get(item.external_id)
            if exercise is None:
                continue
            RoutineExercise.objects.create(
                routine=routine,
                exercise=exercise,
                order=order,
                target_sets=max(1, min(item.sets, 20)),
                target_reps_min=max(1, min(item.reps_min, 100)),
                target_reps_max=max(item.reps_min, min(item.reps_max, 100)),
                rest_seconds=max(0, min(item.rest_seconds, 900)),
            )

    canonicos, _ = resolve_schedule(plan)
    asignado = {
        weekday: creadas.get(nombre) if nombre else None
        for weekday, nombre in canonicos.items()
    }
    ScheduleEntry.objects.bulk_create([
        ScheduleEntry(program=program, weekday=weekday, routine=asignado.get(weekday))
        for weekday, _label in Weekday.choices
    ])

    return program


def _request_params(split: list[DiaDelReparto] | None, reglas=None) -> dict:
    datos = {"objetivo_de_entreno": reglas.goal} if reglas is not None else {}
    if not split:
        return datos
    return datos | {
        "reparto": [
            {
                "weekday": dia.weekday,
                "muscles": list(dia.muscles),
                "emphasis": dia.emphasis,
                "exercises": dia.exercises,
            }
            for dia in split
        ]
    }


def _log_success(
    user, provider, system, user_message, result, *, split=None, reglas=None
) -> AIGeneration:
    return AIGeneration.objects.create(
        user=user,
        kind=GenerationKind.ROUTINE,
        provider=provider.config.provider,
        model=provider.model,
        prompt_rendered=f"{system}\n\n---\n\n{user_message}",
        raw_response=result.raw_text,
        parsed_output=result.parsed.model_dump(),
        request_params=_request_params(split, reglas),
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        latency_ms=result.latency_ms,
        status=GenerationStatus.OK,
    )


def _log_failure(
    user, provider, system, status, error, *, result=None, split=None, reglas=None
) -> AIGeneration:
    return AIGeneration.objects.create(
        user=user,
        kind=GenerationKind.ROUTINE,
        provider=provider.config.provider,
        model=provider.model,
        prompt_rendered=system,
        raw_response=getattr(result, "raw_text", "") or "",
        parsed_output=result.parsed.model_dump() if result is not None else None,
        request_params=_request_params(split, reglas),
        input_tokens=getattr(result, "input_tokens", 0) or 0,
        output_tokens=getattr(result, "output_tokens", 0) or 0,
        status=status,
        error=error[:2000],
    )
