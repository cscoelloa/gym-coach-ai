from datetime import date, timedelta

import pytest
from django.utils import timezone

from apps.metrics.catalog.consistency import adherence_rate, session_density
from apps.metrics.context import MetricContext
from apps.workouts.models import Program, Routine, ScheduleEntry, WorkoutSession

pytestmark = pytest.mark.django_db


@pytest.fixture
def rutina(user):
    rutina = Routine.objects.create(user=user, name="Empuje")
    programa = Program.objects.create(user=user, name="P", is_active=True)
    for weekday in range(7):
        ScheduleEntry.objects.create(
            program=programa, weekday=weekday, routine=None if weekday >= 4 else rutina
        )
    return rutina


class TestAdherencia:
    def test_sin_rutina_activa_no_se_puede_medir(self, user):
        resultado = adherence_rate(MetricContext(user=user))

        assert resultado.value is None
        assert resultado.coverage == 0.0
        assert resultado.notes

    def test_cumplir_el_plan_da_cien_por_cien(self, user, rutina, log_set, bench):
        martes = date(2026, 9, 8)
        for offset in range(4):
            WorkoutSession.objects.create(user=user, date=martes + timedelta(days=offset))

        resultado = adherence_rate(MetricContext(user=user))

        assert resultado.value == 100

    def test_la_mitad_del_plan_da_la_mitad(self, user, rutina):
        martes = date(2026, 9, 8)
        for offset in range(2):
            WorkoutSession.objects.create(user=user, date=martes + timedelta(days=offset))

        resultado = adherence_rate(MetricContext(user=user))

        assert resultado.value == 50

    def test_entrenar_de_mas_se_acota_al_cien(self, user, rutina):
        martes = date(2026, 9, 8)
        for offset in range(6):
            WorkoutSession.objects.create(user=user, date=martes + timedelta(days=offset))

        resultado = adherence_rate(MetricContext(user=user))

        assert resultado.value == 100


class TestDensidad:
    def test_sin_horas_de_sesion_no_se_calcula(self, user, bench, log_set):
        log_set(bench, weight=100, reps=10)

        resultado = session_density(MetricContext(user=user))

        assert resultado.value is None
        assert resultado.coverage == 0.0

    def test_calcula_kilos_por_minuto(self, user, bench, log_set):
        set_log = log_set(bench, weight=100, reps=10)
        sesion = set_log.session
        sesion.started_at = timezone.now() - timedelta(minutes=50)
        sesion.finished_at = timezone.now()
        sesion.save()

        resultado = session_density(MetricContext(user=user))

        assert resultado.value == pytest.approx(20, abs=0.5)
        assert resultado.coverage == 1.0

    def test_la_cobertura_refleja_cuantas_sesiones_tienen_horas(self, user, bench, log_set):
        con_horas = log_set(bench, days_ago=0).session
        con_horas.started_at = timezone.now() - timedelta(minutes=60)
        con_horas.finished_at = timezone.now()
        con_horas.save()
        log_set(bench, days_ago=3)

        assert session_density(MetricContext(user=user)).coverage == 0.5

    def test_una_sesion_de_duracion_cero_no_divide_entre_cero(self, user, bench, log_set):
        sesion = log_set(bench).session
        ahora = timezone.now()
        sesion.started_at = ahora
        sesion.finished_at = ahora
        sesion.save()

        resultado = session_density(MetricContext(user=user))

        assert resultado.value is None
