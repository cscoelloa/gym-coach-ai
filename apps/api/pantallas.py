from django.db.models import Count, Prefetch
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.bodyweight.models import BodyWeightEntry
from apps.metrics.summary import (
    WEEKDAY_INITIALS,
    activity_calendar,
    headline_tiles,
    muscle_map,
    sessions_by_weekday,
    streak,
    week_strip,
)
from apps.workouts import bodymap
from apps.workouts.models import (
    Program,
    Routine,
    RoutineExercise,
    ScheduleEntry,
    Weekday,
    WorkoutSession,
)

PUNTOS_DE_PESO_EN_INICIO = 60
PORTADA_MAXIMA = 4

MESES_CORTOS = (
    "ene", "feb", "mar", "abr", "may", "jun",
    "jul", "ago", "sep", "oct", "nov", "dic",
)


def etiqueta_de_fecha(fecha) -> str:
    return f"{fecha.day} {MESES_CORTOS[fecha.month - 1]}"


def _portada(rutina) -> list[str]:
    urls = []
    for item in rutina.exercises.all():
        if item.exercise.image:
            urls.append(item.exercise.image.url)
        if len(urls) == PORTADA_MAXIMA:
            break
    return urls


def serie_de_peso(usuario, limite: int | None = None) -> dict:
    consulta = BodyWeightEntry.objects.filter(user=usuario).order_by("-date")
    filas = consulta.values_list("date", "weight_kg")
    filas = list(filas[:limite] if limite else filas)
    filas.reverse()

    return {
        "labels": [etiqueta_de_fecha(fecha) for fecha, _peso in filas],
        "values": [float(peso) for _fecha, peso in filas],
        "goal": float(usuario.target_weight_kg) if usuario.target_weight_kg else None,
    }


def _hoy_toca(usuario, hoy) -> dict:
    sesion_abierta = (
        WorkoutSession.objects.filter(user=usuario, finished_at__isnull=True)
        .order_by("-date", "-pk")
        .first()
    )
    if sesion_abierta:
        return {
            "estado": "sesion_abierta",
            "sesion": {"id": sesion_abierta.pk, "fecha": sesion_abierta.date.isoformat()},
            "rutina": None,
        }

    entrada = (
        ScheduleEntry.objects.filter(
            program__user=usuario, program__is_active=True, weekday=hoy.weekday()
        )
        .select_related("routine")
        .prefetch_related("routine__exercises__exercise")
        .first()
    )

    if entrada is None:
        return {"estado": "sin_programa", "sesion": None, "rutina": None}

    if entrada.routine is None:
        return {"estado": "descanso", "sesion": None, "rutina": None}

    ejercicios = [
        {
            "id": item.exercise_id,
            "name": item.exercise.name,
            "image": item.exercise.image.url if item.exercise.image else None,
        }
        for item in entrada.routine.exercises.all()
    ]
    return {
        "estado": "rutina",
        "sesion": None,
        "rutina": {
            "id": entrada.routine.pk,
            "nombre": entrada.routine.name,
            "ejercicios": ejercicios,
        },
    }


class InicioView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        hoy = timezone.localdate()
        usuario = request.user

        pesos = BodyWeightEntry.objects.filter(user=usuario)
        ultimo = pesos.first()
        anterior = pesos.exclude(pk=ultimo.pk).first() if ultimo else None

        racha = streak(usuario, on_date=hoy)
        serie = serie_de_peso(usuario, limite=PUNTOS_DE_PESO_EN_INICIO)

        return Response({
            "hoy": hoy.isoformat(),
            "semana": [
                {
                    "fecha": dia.date.isoformat(),
                    "inicial": dia.initial,
                    "numero": dia.date.day,
                    "hoy": dia.is_today,
                    "futuro": dia.is_future,
                    "entrenado": dia.trained,
                    "planificado": dia.planned,
                }
                for dia in week_strip(usuario, on_date=hoy)
            ],
            "hoy_toca": _hoy_toca(usuario, hoy),
            "peso": {
                "ultimo": (
                    {"fecha": ultimo.date.isoformat(), "kg": float(ultimo.weight_kg)}
                    if ultimo
                    else None
                ),
                "cambio": (
                    float(ultimo.weight_kg - anterior.weight_kg) if ultimo and anterior else None
                ),
                "objetivo": usuario.get_goal_display(),
                "meta_kg": float(usuario.target_weight_kg) if usuario.target_weight_kg else None,
                "serie": serie if len(serie["values"]) >= 2 else None,
            },
            "racha": {
                "semanas": racha.weeks,
                "hechas_esta_semana": racha.this_week_done,
                "planificadas_esta_semana": racha.this_week_planned,
                "total_sesiones": racha.total_sessions,
            },
            "mapa_corporal": muscle_map(usuario, on_date=hoy)["levels"],
        })


class PlanView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        usuario = request.user

        activo = (
            Program.objects.filter(user=usuario, is_active=True)
            .prefetch_related(
                Prefetch(
                    "schedule",
                    queryset=ScheduleEntry.objects.select_related("routine").order_by("weekday"),
                )
            )
            .order_by("-created_at")
            .first()
        )

        por_dia = {entrada.weekday: entrada for entrada in activo.schedule.all()} if activo else {}

        rutinas = list(
            Routine.objects.filter(user=usuario)
            .annotate(n_ejercicios=Count("exercises", distinct=True))
            .prefetch_related(
                Prefetch(
                    "exercises",
                    queryset=RoutineExercise.objects.select_related("exercise").order_by("order"),
                ),
                "scheduled_on__program",
            )
            .order_by("name", "pk")
        )
        conteos = {r.pk: r.n_ejercicios for r in rutinas}
        portadas = {r.pk: _portada(r) for r in rutinas}

        semana = [
            {
                "weekday": weekday,
                "etiqueta": etiqueta,
                "entrada_id": por_dia[weekday].pk if weekday in por_dia else None,
                "rutina": (
                    {
                        "id": por_dia[weekday].routine.pk,
                        "nombre": por_dia[weekday].routine.name,
                        "n_ejercicios": conteos.get(por_dia[weekday].routine.pk, 0),
                        "imagenes": portadas.get(por_dia[weekday].routine.pk, []),
                    }
                    if weekday in por_dia and por_dia[weekday].routine
                    else None
                ),
            }
            for weekday, etiqueta in Weekday.choices
        ]

        return Response({
            "hoy_weekday": timezone.localdate().weekday(),
            "programa": (
                {"id": activo.pk, "nombre": activo.name, "descripcion": activo.description}
                if activo
                else None
            ),
            "programas": [
                {"id": p.pk, "nombre": p.name, "activo": p.is_active}
                for p in Program.objects.filter(user=usuario).order_by("-is_active", "name")
            ],
            "semana": semana,
            "rutinas": [
                {
                    "id": rutina.pk,
                    "nombre": rutina.name,
                    "descripcion": rutina.description,
                    "n_ejercicios": rutina.n_ejercicios,
                    "imagenes": portadas.get(rutina.pk, []),
                    "dias": [
                        entrada.get_weekday_display()
                        for entrada in rutina.scheduled_on.all()
                        if entrada.program.is_active
                    ],
                }
                for rutina in rutinas
            ],
        })


class MapaCorporalView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        vistas = bodymap.painted()

        return Response({
            "vistas": [
                {
                    "nombre": vista.name,
                    "titulo": vista.caption,
                    "viewbox": vista.viewbox,
                    "regiones": [
                        {
                            "id": region.id,
                            "musculo": region.muscle,
                            "etiqueta": region.label,
                            "d": region.d,
                        }
                        for region in vista.regions
                    ],
                }
                for vista in vistas
            ],
            "musculos": list(bodymap.PAINTED_MUSCLES),
        })


SEMANAS_POR_DIA = 12


class ProgresoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        hoy = timezone.localdate()
        usuario = request.user

        calendario = activity_calendar(usuario, on_date=hoy)
        mapa = muscle_map(usuario, on_date=hoy)
        cifras = headline_tiles(usuario, on_date=hoy)
        por_dia = sessions_by_weekday(usuario, weeks=SEMANAS_POR_DIA, on_date=hoy)
        serie = serie_de_peso(usuario)

        return Response({
            "hoy": hoy.isoformat(),
            "cifras": {
                "total_sesiones": cifras["total_sessions"],
                "sesiones_este_mes": cifras["sessions_this_month"],
                "racha_semanas": cifras["streak_weeks"],
                "peso_30_dias": (
                    float(cifras["weight_delta"]) if cifras["weight_delta"] is not None else None
                ),
            },
            "calendario": {
                "semanas": [
                    {
                        "etiqueta": semana.label,
                        "dias": [
                            (
                                {
                                    "fecha": dia.date.isoformat(),
                                    "nivel": dia.level,
                                    "minutos": dia.minutes,
                                    "sesiones": dia.sessions,
                                }
                                if dia
                                else None
                            )
                            for dia in semana.days
                        ],
                    }
                    for semana in calendario["weeks"]
                ],
                "niveles": calendario["levels"],
            },
            "peso": {
                "serie": serie if len(serie["values"]) >= 2 else None,
            },
            "mapa_corporal": {
                "niveles": mapa["levels"],
                "series": mapa["sets"],
                "total_series": mapa["total_sets"],
                "desde": mapa["since"].isoformat(),
            },
            "por_dia_de_semana": [
                {"weekday": weekday, "inicial": WEEKDAY_INITIALS[weekday],
                 "sesiones": por_dia.get(weekday, 0)}
                for weekday in range(7)
            ],
            "semanas_por_dia": SEMANAS_POR_DIA,
        })
