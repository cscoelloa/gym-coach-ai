import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("aiassist", "0001_initial"),
        ("workouts", "0003_rutinas_asignables_a_dias"),
    ]

    operations = [
        migrations.RemoveField(model_name="routineexercise", name="routine_day"),
        migrations.RemoveField(model_name="workoutsession", name="routine_day"),
        migrations.RemoveField(model_name="routineday", name="routine"),
        migrations.DeleteModel(name="RoutineDay"),

        migrations.RemoveField(model_name="routine", name="is_active"),
        migrations.AlterModelOptions(
            name="routine",
            options={
                "ordering": ["name", "pk"],
                "verbose_name": "rutina",
                "verbose_name_plural": "rutinas",
            },
        ),
        migrations.AlterField(
            model_name="routine",
            name="name",
            field=models.CharField(
                help_text="Ej.: Empuje, Tirón, Pierna", max_length=120, verbose_name="nombre"
            ),
        ),
        migrations.AddField(
            model_name="routineexercise",
            name="routine",
            field=models.ForeignKey(
                default=None,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="exercises",
                to="workouts.routine",
                verbose_name="rutina",
            ),
            preserve_default=False,
        ),
        migrations.AlterModelOptions(
            name="routineexercise",
            options={
                "ordering": ["routine", "order", "pk"],
                "verbose_name": "ejercicio de la rutina",
                "verbose_name_plural": "ejercicios de la rutina",
            },
        ),

        migrations.CreateModel(
            name="Program",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "name",
                    models.CharField(
                        help_text="Ej.: Volumen invierno", max_length=120, verbose_name="nombre"
                    ),
                ),
                ("description", models.TextField(blank=True, verbose_name="descripción")),
                (
                    "is_active",
                    models.BooleanField(db_index=True, default=True, verbose_name="activo"),
                ),
                (
                    "source",
                    models.CharField(
                        choices=[("manual", "Creada a mano"), ("ai", "Generada por IA")],
                        default="manual",
                        max_length=16,
                        verbose_name="origen",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="creado")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="actualizado")),
                (
                    "generation",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="programs",
                        to="aiassist.aigeneration",
                        verbose_name="generación",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="programs",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="usuario",
                    ),
                ),
            ],
            options={
                "verbose_name": "programa",
                "verbose_name_plural": "programas",
                "ordering": ["-is_active", "-created_at"],
            },
        ),

        migrations.CreateModel(
            name="ScheduleEntry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "weekday",
                    models.IntegerField(
                        choices=[
                            (0, "Lunes"), (1, "Martes"), (2, "Miércoles"), (3, "Jueves"),
                            (4, "Viernes"), (5, "Sábado"), (6, "Domingo"),
                        ],
                        verbose_name="día",
                    ),
                ),
                ("notes", models.TextField(blank=True, max_length=1000, verbose_name="notas")),
                (
                    "program",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="schedule",
                        to="workouts.program",
                        verbose_name="programa",
                    ),
                ),
                (
                    "routine",
                    models.ForeignKey(
                        blank=True,
                        help_text="Sin rutina = día de descanso.",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="scheduled_on",
                        to="workouts.routine",
                        verbose_name="rutina",
                    ),
                ),
            ],
            options={
                "verbose_name": "día del programa",
                "verbose_name_plural": "días del programa",
                "ordering": ["weekday"],
            },
        ),
        migrations.AddConstraint(
            model_name="scheduleentry",
            constraint=models.UniqueConstraint(
                fields=("program", "weekday"), name="unique_day_per_program"
            ),
        ),

        migrations.AddField(
            model_name="workoutsession",
            name="routine",
            field=models.ForeignKey(
                blank=True,
                help_text="Qué rutina se estaba haciendo. Vacío = entrenamiento libre.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="sessions",
                to="workouts.routine",
                verbose_name="rutina",
            ),
        ),
    ]
