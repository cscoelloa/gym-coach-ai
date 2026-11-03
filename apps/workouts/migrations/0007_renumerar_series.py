from django.db import migrations

LOTE = 500


def renumerar(apps, schema_editor):
    SetLog = apps.get_model("workouts", "SetLog")

    cambiadas = []
    grupo = None
    numero = 0
    for serie in SetLog.objects.order_by("session_id", "exercise_id", "set_number", "pk").only(
        "pk", "session_id", "exercise_id", "set_number"
    ).iterator(chunk_size=LOTE):
        clave = (serie.session_id, serie.exercise_id)
        if clave != grupo:
            grupo, numero = clave, 0
        numero += 1
        if serie.set_number != numero:
            serie.set_number = numero
            cambiadas.append(serie)
        if len(cambiadas) >= LOTE:
            SetLog.objects.bulk_update(cambiadas, ["set_number"])
            cambiadas = []

    SetLog.objects.bulk_update(cambiadas, ["set_number"])


class Migration(migrations.Migration):
    dependencies = [("workouts", "0006_ejercicios_unilaterales")]

    operations = [migrations.RunPython(renumerar, migrations.RunPython.noop)]
