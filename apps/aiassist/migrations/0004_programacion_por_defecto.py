from django.db import migrations


def crear(apps, schema_editor):
    from apps.aiassist.models import PROGRAMACION_POR_DEFECTO

    ProgrammingRules = apps.get_model("aiassist", "ProgrammingRules")
    for goal, valores in PROGRAMACION_POR_DEFECTO.items():
        ProgrammingRules.objects.get_or_create(goal=goal, defaults=valores)


def borrar(apps, schema_editor):
    apps.get_model("aiassist", "ProgrammingRules").objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [("aiassist", "0003_programmingrules")]

    operations = [migrations.RunPython(crear, borrar)]
