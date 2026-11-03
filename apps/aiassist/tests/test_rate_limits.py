from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.aiassist.models import AIGeneration, GenerationKind, GenerationStatus
from apps.aiassist.services import QuotaExceeded, check_quota
from apps.aiassist.services.limits import remaining

pytestmark = pytest.mark.django_db

User = get_user_model()


@pytest.fixture
def user():
    return User.objects.create_user("atleta", password="Contrasena-Larga-1")


def registrar(user, *, cuantas=1, hace=timedelta(0), status=GenerationStatus.OK):
    for _ in range(cuantas):
        generation = AIGeneration.objects.create(
            user=user, kind=GenerationKind.ROUTINE, provider="anthropic",
            model="claude-opus-5", status=status,
        )
        if hace:
            AIGeneration.objects.filter(pk=generation.pk).update(
                created_at=timezone.now() - hace
            )


class TestCupoPorHora:
    def test_dentro_del_cupo_no_pasa_nada(self, user, settings):
        settings.AI_RATE_LIMIT_GENERATION_PER_HOUR = 5
        registrar(user, cuantas=4)

        check_quota(user, GenerationKind.ROUTINE)

    def test_al_llegar_al_limite_se_bloquea(self, user, settings):
        settings.AI_RATE_LIMIT_GENERATION_PER_HOUR = 5
        registrar(user, cuantas=5)

        with pytest.raises(QuotaExceeded, match="por hora"):
            check_quota(user, GenerationKind.ROUTINE)

    def test_las_de_hace_mas_de_una_hora_no_cuentan(self, user, settings):
        settings.AI_RATE_LIMIT_GENERATION_PER_HOUR = 5
        registrar(user, cuantas=5, hace=timedelta(hours=2))

        check_quota(user, GenerationKind.ROUTINE)

    def test_los_fallos_del_proveedor_no_gastan_cupo(self, user, settings):
        settings.AI_RATE_LIMIT_GENERATION_PER_HOUR = 5
        registrar(user, cuantas=5, status=GenerationStatus.ERROR)

        check_quota(user, GenerationKind.ROUTINE)

    def test_un_rechazo_del_modelo_si_gasta_cupo(self, user, settings):
        settings.AI_RATE_LIMIT_GENERATION_PER_HOUR = 2
        registrar(user, cuantas=2, status=GenerationStatus.REFUSED)

        with pytest.raises(QuotaExceeded):
            check_quota(user, GenerationKind.ROUTINE)


class TestCupoDiario:
    def test_se_puede_agotar_el_dia_sin_agotar_la_hora(self, user, settings):
        settings.AI_RATE_LIMIT_GENERATION_PER_HOUR = 5
        settings.AI_RATE_LIMIT_GENERATION_PER_DAY = 10
        registrar(user, cuantas=10, hace=timedelta(hours=3))

        with pytest.raises(QuotaExceeded, match="diarias"):
            check_quota(user, GenerationKind.ROUTINE)


class TestPorUsuario:
    def test_el_gasto_de_uno_no_afecta_a_otro(self, user, settings):
        settings.AI_RATE_LIMIT_GENERATION_PER_HOUR = 2
        otro = User.objects.create_user("otro", password="Contrasena-Larga-2")
        registrar(user, cuantas=2)

        check_quota(otro, GenerationKind.ROUTINE)


class TestRestantes:
    def test_cuenta_bien_lo_que_queda(self, user, settings):
        settings.AI_RATE_LIMIT_GENERATION_PER_HOUR = 5
        registrar(user, cuantas=2)

        assert remaining(user, GenerationKind.ROUTINE) == 3

    def test_nunca_baja_de_cero(self, user, settings):
        settings.AI_RATE_LIMIT_GENERATION_PER_HOUR = 2
        registrar(user, cuantas=5)

        assert remaining(user, GenerationKind.ROUTINE) == 0


class TestAnalisis:
    def test_el_analisis_tiene_su_propio_cupo(self, user, settings):
        settings.AI_RATE_LIMIT_GENERATION_PER_HOUR = 1
        settings.AI_RATE_LIMIT_ANALYSIS_PER_HOUR = 3
        registrar(user, cuantas=1)

        check_quota(user, GenerationKind.PROGRESS)
