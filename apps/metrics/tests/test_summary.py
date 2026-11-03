from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.bodyweight.models import BodyWeightEntry
from apps.metrics.summary import (
    LEVEL_UNKNOWN_DURATION,
    activity_calendar,
    headline_tiles,
    streak,
    week_strip,
    weight_delta,
)
from apps.workouts.models import Program, Routine, ScheduleEntry, WorkoutSession

pytestmark = pytest.mark.django_db

User = get_user_model()

LUNES = date(2026, 9, 7)


@pytest.fixture
def ana():
    return User.objects.create_user("ana", password="Contrasena-Larga-1")


def entrena(user, dia, minutos=None):
    inicio = timezone.make_aware(timezone.datetime.combine(dia, timezone.datetime.min.time()))
    return WorkoutSession.objects.create(
        user=user,
        date=dia,
        started_at=inicio if minutos is not None else None,
        finished_at=inicio + timedelta(minutes=minutos) if minutos is not None else None,
    )


class TestTiraDeSemana:
    def test_son_siete_dias_de_lunes_a_domingo(self, ana):
        tira = week_strip(ana, on_date=LUNES + timedelta(days=3))

        assert len(tira) == 7
        assert [d.initial for d in tira] == ["L", "M", "X", "J", "V", "S", "D"]
        assert tira[0].date == LUNES
        assert tira[6].date == LUNES + timedelta(days=6)

    def test_marca_los_dias_entrenados_y_el_de_hoy(self, ana):
        entrena(ana, LUNES)
        entrena(ana, LUNES + timedelta(days=2))

        tira = week_strip(ana, on_date=LUNES + timedelta(days=3))

        assert [d.trained for d in tira] == [True, False, True, False, False, False, False]
        assert [d.is_today for d in tira] == [False, False, False, True, False, False, False]

    def test_distingue_el_futuro(self, ana):
        tira = week_strip(ana, on_date=LUNES + timedelta(days=2))

        assert [d.is_future for d in tira] == [False, False, False, True, True, True, True]

    def test_marca_los_dias_planificados_de_la_rutina_activa(self, ana):
        entrena_los = {0, 2, 4}
        rutina = Routine.objects.create(user=ana, name="Empuje")
        programa = Program.objects.create(user=ana, name="P", is_active=True)
        for weekday in range(7):
            ScheduleEntry.objects.create(
                program=programa,
                weekday=weekday,
                routine=rutina if weekday in entrena_los else None,
            )

        tira = week_strip(ana, on_date=LUNES)

        assert [d.planned for d in tira] == [True, False, True, False, True, False, False]

    def test_sin_programa_no_hay_nada_planificado(self, ana):
        assert all(not d.planned for d in week_strip(ana, on_date=LUNES))


class TestRacha:
    def test_semanas_consecutivas(self, ana):
        for semanas in range(3):
            entrena(ana, LUNES - timedelta(weeks=semanas))

        assert streak(ana, on_date=LUNES + timedelta(days=2)).weeks == 3

    def test_la_semana_en_curso_vacia_NO_rompe_la_racha(self, ana):
        for semanas in range(1, 4):
            entrena(ana, LUNES - timedelta(weeks=semanas))

        assert streak(ana, on_date=LUNES).weeks == 3

    def test_una_semana_terminada_sin_entrenar_SI_la_rompe(self, ana):
        entrena(ana, LUNES)
        entrena(ana, LUNES - timedelta(weeks=2))

        assert streak(ana, on_date=LUNES + timedelta(days=3)).weeks == 1

    def test_sin_ninguna_sesion_la_racha_es_cero(self, ana):
        assert streak(ana, on_date=LUNES).weeks == 0

    def test_cuenta_bien_al_cambiar_de_año(self, ana):
        fin_de_año = date(2025, 12, 29)
        for semanas in range(3):
            entrena(ana, fin_de_año + timedelta(weeks=semanas))

        assert streak(ana, on_date=fin_de_año + timedelta(weeks=2, days=3)).weeks == 3

    def test_informa_de_lo_hecho_y_lo_planificado_esta_semana(self, ana):
        entrena_los = {0, 2, 4, 6}
        rutina = Routine.objects.create(user=ana, name="Empuje")
        programa = Program.objects.create(user=ana, name="P", is_active=True)
        for weekday in range(7):
            ScheduleEntry.objects.create(
                program=programa,
                weekday=weekday,
                routine=rutina if weekday in entrena_los else None,
            )
        entrena(ana, LUNES)
        entrena(ana, LUNES + timedelta(days=2))

        resultado = streak(ana, on_date=LUNES + timedelta(days=3))

        assert resultado.this_week_done == 2
        assert resultado.this_week_planned == 4
        assert resultado.total_sessions == 2


class TestCalendarioDeActividad:
    def test_un_dia_entrenado_sin_duracion_NO_vale_cero(self, ana):
        entrena(ana, LUNES, minutos=None)

        celda = self._celda(activity_calendar(ana, on_date=LUNES), LUNES)

        assert celda.sessions == 1
        assert celda.level == LEVEL_UNKNOWN_DURATION
        assert celda.level > 0

    def test_la_intensidad_sube_con_los_minutos(self, ana):
        entrena(ana, LUNES - timedelta(days=3), minutos=20)
        entrena(ana, LUNES - timedelta(days=2), minutos=45)
        entrena(ana, LUNES - timedelta(days=1), minutos=120)

        calendario = activity_calendar(ana, on_date=LUNES)
        niveles = [
            self._celda(calendario, LUNES - timedelta(days=d)).level for d in (3, 2, 1)
        ]

        assert niveles == sorted(niveles), f"no es monótono: {niveles}"
        assert niveles[0] < niveles[-1]

    def test_un_dia_sin_entrenar_vale_cero(self, ana):
        assert self._celda(activity_calendar(ana, on_date=LUNES), LUNES).level == 0

    def test_suma_dos_sesiones_del_mismo_dia(self, ana):
        entrena(ana, LUNES, minutos=40)
        entrena(ana, LUNES, minutos=40)

        celda = self._celda(activity_calendar(ana, on_date=LUNES), LUNES)

        assert celda.sessions == 2
        assert celda.minutes == 80

    def test_no_consulta_una_vez_por_dia(self, ana, django_assert_num_queries):
        for offset in range(0, 300, 3):
            entrena(ana, LUNES - timedelta(days=offset), minutos=45)

        with django_assert_num_queries(1):
            activity_calendar(ana, on_date=LUNES)

    def test_no_pinta_dias_futuros(self, ana):
        calendario = activity_calendar(ana, on_date=LUNES)
        ultima_columna = calendario["weeks"][-1].days

        assert ultima_columna[0] is not None
        assert all(celda is None for celda in ultima_columna[1:])

    def test_el_mes_se_etiqueta_en_su_propia_columna(self, ana):
        from django.utils import formats

        calendario = activity_calendar(ana, on_date=LUNES)
        etiquetadas = [c for c in calendario["weeks"] if c.label]

        assert len(etiquetadas) >= 10, "un año debería etiquetar casi todos los meses"
        for columna in etiquetadas:
            lunes = next(c.date for c in columna.days if c is not None)
            assert columna.label == formats.date_format(lunes, "M")

    def test_los_nombres_de_mes_estan_en_espanol(self, ana):
        calendario = activity_calendar(ana, on_date=date(2026, 1, 5))

        nombres = {c.label for c in calendario["weeks"] if c.label}

        assert nombres, "ningún mes etiquetado"
        assert not nombres & {"Jan", "Aug", "Dec", "Apr"}, nombres

    def test_un_mes_cortado_no_pisa_al_siguiente(self, ana):
        calendario = activity_calendar(ana, on_date=LUNES)
        etiquetadas = [i for i, c in enumerate(calendario["weeks"]) if c.label]

        separaciones = [b - a for a, b in zip(etiquetadas, etiquetadas[1:], strict=False)]

        assert all(sep >= 3 for sep in separaciones), separaciones

    @staticmethod
    def _celda(calendario, dia):
        for columna in calendario["weeks"]:
            for celda in columna.days:
                if celda is not None and celda.date == dia:
                    return celda
        raise AssertionError(f"{dia} no aparece en el calendario")


class TestVariacionDePeso:
    def test_sin_dos_registros_devuelve_None_y_no_cero(self, ana):
        assert weight_delta(ana, on_date=LUNES) is None

        BodyWeightEntry.objects.create(user=ana, date=LUNES, weight_kg=Decimal("80"))
        assert weight_delta(ana, on_date=LUNES) is None

    def test_calcula_la_diferencia(self, ana):
        BodyWeightEntry.objects.create(
            user=ana, date=LUNES - timedelta(days=30), weight_kg=Decimal("80")
        )
        BodyWeightEntry.objects.create(user=ana, date=LUNES, weight_kg=Decimal("78.6"))

        assert weight_delta(ana, on_date=LUNES) == Decimal("-1.4")


class TestCifrasDeCabecera:
    def test_las_cuatro_cifras(self, ana):
        entrena(ana, LUNES)
        entrena(ana, LUNES - timedelta(weeks=1))

        tiles = headline_tiles(ana, on_date=LUNES + timedelta(days=1))

        assert tiles["total_sessions"] == 2
        assert tiles["sessions_this_month"] == 1
        assert tiles["streak_weeks"] == 2
        assert tiles["weight_delta"] is None

    def test_el_mes_es_natural_y_no_los_ultimos_treinta_dias(self, ana):
        entrena(ana, date(2026, 8, 31))
        entrena(ana, date(2026, 9, 1))

        assert headline_tiles(ana, on_date=date(2026, 9, 1))["sessions_this_month"] == 1
