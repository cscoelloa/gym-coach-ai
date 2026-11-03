from dataclasses import replace
from datetime import timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.utils import timezone

from apps.metrics.services import compute
from apps.workouts.models import Exercise, MuscleGroup, SetLog, WorkoutSession

pytestmark = pytest.mark.django_db

User = get_user_model()


@pytest.fixture
def catalogo(db):
    call_command("sync_metrics", verbosity=0)


@pytest.fixture
def nueva():
    return User.objects.create_user("nueva", password="Contrasena-Larga-1")


def metrica(user, key):
    return next(m for m in compute(user) if m.metric.key == key)


class TestElCeroQueNoEsUnCero:
    def test_sin_historial_no_se_felicita_por_no_estar_estancado(self, catalogo, nueva):
        item = metrica(nueva, "stalled_exercises")

        assert item.result.coverage == 0
        assert item.result.notes == []

    def test_un_cero_sin_cobertura_cuenta_como_no_tener_datos(self, catalogo, nueva):
        item = metrica(nueva, "stalled_exercises")

        assert item.result.is_empty is False
        assert item.has_no_data is True

    def test_un_cero_con_cobertura_si_es_un_resultado(self, catalogo, nueva):
        item = metrica(nueva, "week_streak")

        assert item.result.value == 0
        assert item.result.coverage == 1
        assert item.has_no_data is False


class TestLaFraseDeLaTarjetaVacia:
    def test_gana_la_nota_de_la_metrica(self, catalogo, nueva):
        item = metrica(nueva, "bodyweight_trend")

        assert item.empty_hint == "Registra tu peso al menos dos días para ver la tendencia."

    def test_sin_nota_se_construye_con_lo_que_falta(self, catalogo, nueva):
        item = metrica(nueva, "session_density")

        assert item.empty_hint == "Para verlo, registra la hora de inicio y fin de tus sesiones."

    def test_sin_nota_y_sin_requisitos_queda_lo_generico(self, catalogo, nueva):
        item = metrica(nueva, "stalled_exercises")

        assert item.empty_hint == "Todavía no hay datos."

    def test_varios_requisitos_se_encadenan(self, catalogo, nueva):
        item = metrica(nueva, "session_density")
        item.spec = replace(item.spec, requires=item.spec.requires * 2)

        assert " y " in item.empty_hint


class TestLaPantallaDeEstreno:
    def test_el_dia_cero_ninguna_metrica_tiene_un_numero_que_defender(self, catalogo, nueva):
        con_aviso = [
            item for item in compute(nueva) if not item.has_no_data and not item.is_reliable
        ]

        assert con_aviso == []

    def test_cada_tarjeta_vacia_trae_una_frase_y_solo_una(self, catalogo, nueva):
        vacias = [item for item in compute(nueva) if item.has_no_data]

        assert vacias
        assert all(item.empty_hint for item in vacias)
        assert all(isinstance(item.empty_hint, str) for item in vacias)


class TestElAvisoSigueHaciendoSuTrabajo:
    @pytest.fixture
    def a_medias(self, nueva):
        musculo = MuscleGroup.objects.create(slug="pectorals", name="Pectorales")
        ejercicio = Exercise.objects.create(
            external_id="0001", name="barbell bench press", slug="press",
            body_part="chest", equipment="barbell", target_muscle=musculo, is_global=True,
        )
        hoy = timezone.localdate()
        for dias in range(4):
            sesion = WorkoutSession.objects.create(user=nueva, date=hoy - timedelta(days=dias))
            if dias == 0:
                inicio = timezone.now() - timedelta(hours=1)
                WorkoutSession.objects.filter(pk=sesion.pk).update(
                    started_at=inicio, finished_at=inicio + timedelta(minutes=50)
                )
            SetLog.objects.create(
                session=sesion, exercise=ejercicio, set_number=1,
                weight_kg=Decimal("80"), reps=8,
            )
        return nueva

    def test_hay_cifra_y_la_cobertura_es_parcial(self, catalogo, a_medias):
        item = metrica(a_medias, "session_density")

        assert item.result.value is not None
        assert 0 < item.result.coverage < 0.8
        assert item.has_no_data is False

    def test_y_dice_qué_falta_para_afinarla(self, catalogo, a_medias):
        item = metrica(a_medias, "session_density")

        assert item.is_reliable is False
        assert item.needs == ["la hora de inicio y fin de tus sesiones"]


class TestNoSeRompeElHistorialDeVerdad:
    def test_con_datos_la_metrica_trae_sus_filas(self, catalogo, nueva):
        musculo = MuscleGroup.objects.create(slug="lats", name="Dorsales")
        ejercicio = Exercise.objects.create(
            external_id="0002", name="barbell row", slug="remo",
            body_part="back", equipment="barbell", target_muscle=musculo, is_global=True,
        )
        sesion = WorkoutSession.objects.create(user=nueva, date=timezone.localdate())
        SetLog.objects.create(
            session=sesion, exercise=ejercicio, set_number=1, weight_kg=Decimal("70"), reps=5
        )

        con_filas = [item for item in compute(nueva) if item.result.rows]

        assert con_filas
        texto = str([item.result.rows for item in con_filas]).lower()
        assert "barbell row" in texto
