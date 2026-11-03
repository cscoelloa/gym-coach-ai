import random
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.bodyweight.models import BodyWeightEntry
from apps.workouts.models import (
    Exercise,
    Program,
    Routine,
    RoutineExercise,
    ScheduleEntry,
    SetLog,
    Weekday,
    WorkoutSession,
)

USERNAME = "demo"
PASSWORD = "DemoGym-2026-Segura"  # noqa: S105  # nosec B105
WEEKS = 12

RUTINAS = {
    "Empuje": [
        "barbell bench press",
        "barbell incline bench press",
        "cable shoulder press",
        "cable lateral raise",
        "cable pushdown",
    ],
    "Tirón": [
        "barbell bent over row",
        "alternate lateral pulldown",
        "barbell curl",
    ],
    "Pierna": [
        "barbell full squat",
        "lever leg extension",
        "lever lying leg curl",
    ],
}

SEMANA = {
    0: "Empuje",
    1: "Tirón",
    2: None,
    3: "Empuje",
    4: "Pierna",
    5: None,
    6: None,
}

ESTANCADO = "barbell bench press"


class Command(BaseCommand):
    help = "Crea un usuario de demostración con doce semanas de historial."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset", action="store_true", help="Borra el usuario de demostración y lo recrea."
        )

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()

        if options["reset"]:
            User.objects.filter(username=USERNAME).delete()
        elif User.objects.filter(username=USERNAME).exists():
            raise CommandError(
                f"El usuario «{USERNAME}» ya existe. Usa --reset para recrearlo."
            )

        if not Exercise.objects.exists():
            raise CommandError(
                "El catálogo está vacío. Ejecuta primero `import_catalog`. "
                "Ver el README"
            )

        rng = random.Random(20260914)  # noqa: S311  # nosec B311

        user = self._crear_usuario(User)
        program, rutinas = self._crear_rutina(user)
        sesiones = self._crear_historial(user, program, rng)
        pesos = self._crear_pesos(user, rng)

        entrenables = sum(1 for nombre in SEMANA.values() if nombre)
        self.stdout.write(
            self.style.SUCCESS(
                f"Usuario «{USERNAME}» creado (contraseña: {PASSWORD}).\n"
                f"  {sesiones} entrenamientos, {pesos} registros de peso, "
                f"{len(rutinas)} rutinas asignadas a {entrenables} días "
                f"en el programa «{program.name}»."
            )
        )
        self.stdout.write(
            "  «Empuje» está asignada a dos días a propósito: es la misma rutina, así que "
            "editarla cambia los dos."
        )
        self.stdout.write(
            "  Historial preparado con un ejercicio estancado y un peso que se aparta del "
            "objetivo, para que el análisis tenga algo que decir."
        )


    def _crear_usuario(self, User):
        return User.objects.create_user(
            username=USERNAME,
            password=PASSWORD,
            email="demo@project-gym.local",
            first_name="Demo",
            goal="bulk",
            experience_level="intermediate",
            sex="undisclosed",
            birth_date=date(1996, 5, 20),
            height_cm=176,
            target_weight_kg=Decimal("80"),
            weekly_weight_change_target_kg=Decimal("0.25"),
            available_days_per_week=4,
            available_equipment=["barbell", "dumbbell", "cable", "leverage machine"],
            injuries_notes=(
                "Molestia ocasional en el hombro derecho con press por encima de la cabeza."
            ),
        )

    def _crear_rutina(self, user):
        rutinas = {}
        for nombre, nombres_ejercicio in RUTINAS.items():
            rutina = Routine.objects.create(user=user, name=nombre)
            rutinas[nombre] = rutina

            for orden, nombre_ejercicio in enumerate(nombres_ejercicio):
                exercise = Exercise.objects.filter(name__iexact=nombre_ejercicio).first()
                if exercise is None:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  «{nombre_ejercicio}» no está en el catálogo; ese hueco queda "
                            "vacío en la rutina de demostración."
                        )
                    )
                    continue

                RoutineExercise.objects.create(
                    routine=rutina,
                    exercise=exercise,
                    order=orden,
                    target_sets=4 if orden == 0 else 3,
                    target_reps_min=6 if orden == 0 else 10,
                    target_reps_max=8 if orden == 0 else 12,
                    rest_seconds=180 if "barbell" in exercise.equipment else 90,
                )

        program = Program.objects.create(
            user=user,
            name="Empuje / Tirón / Pierna",
            description="Cuatro días por semana, orientada a hipertrofia.",
            is_active=True,
        )
        ScheduleEntry.objects.bulk_create([
            ScheduleEntry(
                program=program,
                weekday=weekday,
                routine=rutinas.get(SEMANA[weekday]) if SEMANA[weekday] else None,
            )
            for weekday, _label in Weekday.choices
        ])

        return program, rutinas

    def _crear_historial(self, user, program, rng):
        hoy = timezone.localdate()
        creadas = 0

        for semana in range(WEEKS):
            lunes = hoy - timedelta(days=hoy.weekday() + 7 * (WEEKS - 1 - semana))

            for entrada in program.schedule.filter(routine__isnull=False).select_related("routine"):
                if rng.random() < 0.12:
                    continue

                fecha = lunes + timedelta(days=entrada.weekday)
                if fecha > hoy:
                    continue

                inicio = timezone.make_aware(
                    timezone.datetime.combine(fecha, timezone.datetime.min.time())
                ) + timedelta(hours=18)
                sin_cerrar = rng.random() < 0.17
                session = WorkoutSession.objects.create(
                    user=user,
                    routine=entrada.routine,
                    date=fecha,
                    started_at=inicio,
                    finished_at=(
                        None if sin_cerrar else inicio + timedelta(minutes=rng.randint(55, 80))
                    ),
                )
                creadas += 1

                for item in entrada.routine.exercises.select_related("exercise"):
                    self._registrar_series(session, item, semana, rng)

        return creadas

    def _registrar_series(self, session, item, semana, rng):
        exercise = item.exercise
        base = 60 if "barbell" in exercise.equipment else 20

        if exercise.name.lower() == ESTANCADO:
            peso = base + 20 + min(semana, 3) * 2.5
        else:
            peso = base + semana * 2.5

        SetLog.objects.bulk_create([
            SetLog(
                session=session,
                exercise=exercise,
                set_number=serie + 1,
                weight_kg=Decimal(str(round(peso, 1))),
                reps=rng.randint(item.target_reps_min, item.target_reps_max),
                rpe=Decimal(str(rng.choice([7, 7.5, 8, 8.5]))) if rng.random() < 0.6 else None,
            )
            for serie in range(item.target_sets)
        ])

    def _crear_pesos(self, user, rng):
        hoy = timezone.localdate()
        peso = 78.0
        entradas = []

        for dia in range(WEEKS * 7, 0, -1):
            fecha = hoy - timedelta(days=dia)
            if rng.random() < 0.35:
                continue

            peso -= 0.035
            entradas.append(
                BodyWeightEntry(
                    user=user,
                    date=fecha,
                    weight_kg=Decimal(str(round(peso + rng.uniform(-0.4, 0.4), 2))),
                )
            )

        BodyWeightEntry.objects.bulk_create(entradas)
        return len(entradas)
