from urllib.parse import urlsplit

from django.db import transaction

from apps.aiassist.models import AIGeneration
from apps.bodyweight.models import BodyWeightEntry
from apps.notifications.models import Notification, SuscripcionPush
from apps.workouts.models import (
    Exercise,
    Program,
    Routine,
    RoutineExercise,
    SetLog,
    WorkoutSession,
)

SCRUBBED = "[borrado a petición del usuario]"


def export_data(user) -> dict:
    return {
        "perfil": _profile(user),
        "rutinas": _routines(user),
        "programas": _programs(user),
        "entrenamientos": _sessions(user),
        "peso_corporal": _weights(user),
        "notificaciones": _notifications(user),
        "avisos_push": [
            {"servicio": urlsplit(s.endpoint).hostname, "creada": s.creada.isoformat()}
            for s in SuscripcionPush.objects.filter(user=user)
        ],
    }


def _profile(user) -> dict:
    return {
        "usuario": user.username,
        "correo": user.email,
        "nombre": user.first_name,
        "apellidos": user.last_name,
        "alta": user.date_joined.isoformat(),
        "objetivo": user.get_goal_display(),
        "nivel": user.get_experience_level_display(),
        "fecha_nacimiento": user.birth_date.isoformat() if user.birth_date else None,
        "sexo": user.get_sex_display() if user.sex else None,
        "altura_cm": user.height_cm,
        "peso_objetivo_kg": _num(user.target_weight_kg),
        "cambio_semanal_objetivo_kg": _num(user.weekly_weight_change_target_kg),
        "dias_disponibles": user.available_days_per_week,
        "equipamiento": user.available_equipment,
        "lesiones": user.injuries_notes,
    }


def _routines(user) -> list[dict]:
    routines = Routine.objects.filter(user=user).prefetch_related("exercises__exercise")
    return [
        {
            "nombre": routine.name,
            "descripcion": routine.description,
            "origen": routine.get_source_display(),
            "creada": routine.created_at.isoformat(),
            "ejercicios": [
                {
                    "ejercicio": item.exercise.name,
                    "series": item.target_sets,
                    "repeticiones": f"{item.target_reps_min}-{item.target_reps_max}",
                    "descanso_s": item.rest_seconds,
                }
                for item in routine.exercises.all()
            ],
        }
        for routine in routines
    ]


def _programs(user) -> list[dict]:
    programs = Program.objects.filter(user=user).prefetch_related("schedule__routine")
    return [
        {
            "nombre": program.name,
            "descripcion": program.description,
            "activo": program.is_active,
            "origen": program.get_source_display(),
            "creado": program.created_at.isoformat(),
            "semana": [
                {
                    "dia": entrada.get_weekday_display(),
                    "rutina": entrada.routine.name if entrada.routine else None,
                    "descanso": entrada.routine_id is None,
                }
                for entrada in program.schedule.all()
            ],
        }
        for program in programs
    ]


def _sessions(user) -> list[dict]:
    sessions = WorkoutSession.objects.filter(user=user).prefetch_related("sets__exercise")
    return [
        {
            "fecha": session.date.isoformat(),
            "inicio": session.started_at.isoformat() if session.started_at else None,
            "fin": session.finished_at.isoformat() if session.finished_at else None,
            "notas": session.notes,
            "series": [
                {
                    "ejercicio": s.exercise.name,
                    "serie": s.set_number,
                    "peso_kg": _num(s.weight_kg),
                    "repeticiones": s.reps,
                    "rpe": _num(s.rpe),
                    "calentamiento": s.is_warmup,
                }
                for s in session.sets.all()
            ],
        }
        for session in sessions
    ]


def _weights(user) -> list[dict]:
    return [
        {
            "fecha": entry.date.isoformat(),
            "peso_kg": _num(entry.weight_kg),
            "grasa_pct": _num(entry.body_fat_pct),
            "notas": entry.notes,
        }
        for entry in BodyWeightEntry.objects.filter(user=user)
    ]


def _notifications(user) -> list[dict]:
    return [
        {
            "fecha": n.created_at.isoformat(),
            "tipo": n.get_kind_display(),
            "titulo": n.title,
            "contenido": n.body,
        }
        for n in Notification.objects.filter(user=user)
    ]


@transaction.atomic
def delete_account(user) -> dict:
    generaciones = AIGeneration.objects.filter(user=user)
    scrubbed = generaciones.update(
        prompt_rendered=SCRUBBED,
        raw_response=SCRUBBED,
        parsed_output=None,
        error="",
    )

    resumen = {
        "generaciones_anonimizadas": scrubbed,
        "rutinas": Routine.objects.filter(user=user).count(),
        "programas": Program.objects.filter(user=user).count(),
        "entrenamientos": WorkoutSession.objects.filter(user=user).count(),
        "registros_de_peso": BodyWeightEntry.objects.filter(user=user).count(),
        "notificaciones": Notification.objects.filter(user=user).count(),
        "avisos_push": SuscripcionPush.objects.filter(user=user).count(),
        "ejercicios_propios": Exercise.objects.filter(created_by=user).count(),
    }

    _release_custom_exercises(user)
    user.delete()
    return resumen


def _release_custom_exercises(user) -> None:
    propios = list(Exercise.objects.filter(created_by=user).values_list("pk", flat=True))
    if not propios:
        return

    SetLog.objects.filter(session__user=user).delete()
    WorkoutSession.objects.filter(user=user).delete()
    RoutineExercise.objects.filter(routine__user=user).delete()
    Routine.objects.filter(user=user).delete()

    for pk in propios:
        sigue_en_uso = (
            RoutineExercise.objects.filter(exercise_id=pk).exists()
            or SetLog.objects.filter(exercise_id=pk).exists()
        )
        if sigue_en_uso:
            Exercise.objects.filter(pk=pk).update(created_by=None)
        else:
            Exercise.objects.filter(pk=pk).delete()


def _num(value):
    return float(value) if value is not None else None
