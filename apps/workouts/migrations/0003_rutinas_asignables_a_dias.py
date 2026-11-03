from django.db import migrations


def borrar_rutinas_viejas(apps, schema_editor):
    RoutineExercise = apps.get_model("workouts", "RoutineExercise")
    RoutineDay = apps.get_model("workouts", "RoutineDay")
    Routine = apps.get_model("workouts", "Routine")
    WorkoutSession = apps.get_model("workouts", "WorkoutSession")

    WorkoutSession.objects.update(routine_day=None)
    RoutineExercise.objects.all().delete()
    RoutineDay.objects.all().delete()
    Routine.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("workouts", "0002_routine_generation"),
    ]

    operations = [
        migrations.RunPython(borrar_rutinas_viejas, migrations.RunPython.noop),
    ]
