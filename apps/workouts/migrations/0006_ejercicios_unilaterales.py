from django.db import migrations, models

INEQUIVOCOS = [
    "one arm",
    "single arm",
    "one leg",
    "single leg",
    "split squat",
    "bulgarian",
]


def marcar_unilaterales(apps, schema_editor):
    Exercise = apps.get_model("workouts", "Exercise")

    consulta = Exercise.objects.none()
    for patron in INEQUIVOCOS:
        consulta = consulta | Exercise.objects.filter(name__icontains=patron)

    actualizados = consulta.filter(is_global=True).distinct().update(is_unilateral=True)
    print(f"  {actualizados} ejercicios marcados como unilaterales")


class Migration(migrations.Migration):
    dependencies = [
        ("workouts", "0005_quitar_campos_sin_uso"),
    ]

    operations = [
        migrations.AddField(
            model_name="exercise",
            name="is_unilateral",
            field=models.BooleanField(
                default=False,
                help_text=(
                    "Se hace un lado y luego el otro (remo a una mano, zancada). Las series se "
                    "anotan POR LADO y el tonelaje cuenta los dos."
                ),
                verbose_name="unilateral",
            ),
        ),
        migrations.RunPython(marcar_unilaterales, migrations.RunPython.noop),
    ]
