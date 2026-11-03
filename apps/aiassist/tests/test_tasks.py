from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

import pytest
from cryptography.fernet import Fernet
from django.contrib.auth import get_user_model
from django.core.management import call_command

from apps.aiassist.models import AIProviderConfig, Provider
from apps.aiassist.tasks import (
    analyze_new_bodyweight,
    index_knowledge_document,
    run_progress_analysis,
    run_weekly_progress_analysis,
)
from apps.bodyweight.models import BodyWeightEntry
from apps.workouts.models import WorkoutSession

pytestmark = pytest.mark.django_db

User = get_user_model()
CLAVE = Fernet.generate_key().decode()


@pytest.fixture(autouse=True)
def entorno(settings):
    settings.FIELD_ENCRYPTION_KEYS = [CLAVE]
    call_command("sync_metrics")
    call_command("seed_prompts")
    AIProviderConfig.objects.create(
        provider=Provider.ANTHROPIC, api_key="sk-de-prueba", is_active=True
    )


@pytest.fixture
def user():
    return User.objects.create_user("atleta", password="Contrasena-Larga-1", goal="bulk")


class TestTareasQueNoEncuentranSuObjeto:
    def test_documento_inexistente(self):
        assert index_knowledge_document(999999) == "missing"

    def test_peso_inexistente(self):
        assert analyze_new_bodyweight(999999) == "missing"

    def test_usuario_inexistente(self):
        assert run_progress_analysis(999999) == "missing"


class TestAnalisisDePesoEnSegundoPlano:
    def test_no_analiza_si_la_puerta_dice_que_no(self, user):
        entry = BodyWeightEntry.objects.create(
            user=user, date=date.today(), weight_kg=Decimal("75")
        )

        with patch("apps.aiassist.services.weight_analyzer.get_provider") as get_prov:
            resultado = analyze_new_bodyweight(entry.pk)

        assert resultado == "skipped"
        get_prov.assert_not_called()

    def test_un_fallo_del_proveedor_no_propaga(self, user):
        for indice, kg in enumerate([78, 77.5, 77, 76.5, 76, 75.5, 75, 74.5]):
            entry = BodyWeightEntry.objects.create(
                user=user,
                date=date.today() - timedelta(days=7 - indice),
                weight_kg=Decimal(str(kg)),
            )

        with patch("apps.aiassist.services.weight_analyzer.get_provider") as get_prov:
            get_prov.side_effect = RuntimeError("el proveedor está caído")
            resultado = analyze_new_bodyweight(entry.pk)

        assert resultado == "failed"


class TestSenal:
    def test_guardar_un_peso_funciona_aunque_el_broker_este_caido(self, user):
        with patch("apps.aiassist.tasks.analyze_new_bodyweight.delay") as delay:
            delay.side_effect = OSError("no hay broker")

            BodyWeightEntry.objects.create(
                user=user, date=date.today(), weight_kg=Decimal("75")
            )

        assert BodyWeightEntry.objects.count() == 1


class TestAnalisisSemanal:
    def test_solo_encola_a_quien_tiene_historial(self, user):
        sin_historial = User.objects.create_user("novato", password="Contrasena-Larga-2")
        for dia in range(8):
            WorkoutSession.objects.create(user=user, date=date.today() - timedelta(days=dia * 3))

        with patch("apps.aiassist.tasks.run_progress_analysis.delay") as delay:
            resultado = run_weekly_progress_analysis()

        assert resultado == "encolados:1"
        encolados = [llamada.args[0] for llamada in delay.call_args_list]
        assert user.pk in encolados
        assert sin_historial.pk not in encolados

    def test_encola_una_tarea_por_usuario(self, user):
        otro = User.objects.create_user("otro", password="Contrasena-Larga-3")
        for persona in (user, otro):
            for dia in range(8):
                WorkoutSession.objects.create(
                    user=persona, date=date.today() - timedelta(days=dia * 3)
                )

        with patch("apps.aiassist.tasks.run_progress_analysis.delay") as delay:
            run_weekly_progress_analysis()

        assert delay.call_count == 2

    def test_sin_datos_suficientes_no_llama_al_modelo(self, user):
        with patch("apps.aiassist.services.progress_analyzer.get_provider") as get_prov:
            resultado = run_progress_analysis(user.pk)

        assert resultado == "not-enough-data"
        get_prov.assert_not_called()
