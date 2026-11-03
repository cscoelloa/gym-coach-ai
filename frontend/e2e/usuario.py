import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

import django  # noqa: E402

django.setup()

from django.contrib.auth import get_user_model  # noqa: E402

USUARIO = "e2e"
CLAVE = "Contrasena-Larga-E2E-1"  # noqa: S105 - cuenta de pruebas en desarrollo, no un secreto

usuario, creado = get_user_model().objects.get_or_create(
    username=USUARIO, defaults={"email": "e2e@example.invalid", "first_name": "Eva"}
)
usuario.is_staff = True
usuario.set_password(CLAVE)
usuario.first_name = usuario.first_name or "Eva"
usuario.save()

print(f"{'Creada' if creado else 'Actualizada'} la cuenta «{USUARIO}».")

from apps.workouts.models import Program, ScheduleEntry, Weekday  # noqa: E402

programa = Program.objects.filter(user=usuario, is_active=True).first()
if programa is None:
    programa = Program.objects.create(user=usuario, name="Semana de pruebas")
    programa.activate()
for dia in Weekday:
    ScheduleEntry.objects.get_or_create(program=programa, weekday=dia)

print(f"Programa activo: «{programa.name}», con los siete días.")
