from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

import pytest
from cryptography.fernet import Fernet
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.management import call_command
from django.utils import timezone

from apps.aiassist.models import (
    AIGeneration,
    AIProviderConfig,
    GenerationKind,
    GenerationStatus,
    Provider,
)
from apps.aiassist.providers.base import ProviderResult
from apps.aiassist.schemas import (
    ProgressAnalysis,
    ProposedChange,
    StalledExercise,
    WeightAnalysis,
)
from apps.aiassist.services.progress_analyzer import (
    MIN_SESSIONS,
    NotEnoughData,
    analyze_progress,
    notify_progress,
)
from apps.aiassist.services.weight_analyzer import (
    COOLDOWN_DAYS,
    analyze_weight,
    notify_weight,
    should_analyze,
    target_rate,
)
from apps.bodyweight.models import BodyWeightEntry
from apps.notifications.models import Notification, NotificationKind, Severity
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
    return User.objects.create_user(
        "atleta", email="atleta@example.com", password="Contrasena-Larga-1", goal="bulk"
    )


def configurar(mock, parsed):
    mock.return_value.supports_rag = False
    mock.return_value.config.provider = "anthropic"
    mock.return_value.model = "claude-opus-5"
    mock.return_value.generate_structured.return_value = ProviderResult(
        parsed=parsed, raw_text="{}", input_tokens=800, output_tokens=300, latency_ms=2000
    )
    return mock


def sesiones(user, cuantas):
    for dia in range(cuantas):
        WorkoutSession.objects.create(user=user, date=date.today() - timedelta(days=dia * 3))


def pesos(user, valores, *, desde_dias=None):
    total = len(valores)
    for indice, valor in enumerate(valores):
        BodyWeightEntry.objects.create(
            user=user,
            date=date.today() - timedelta(days=(desde_dias or total) - indice - 1),
            weight_kg=Decimal(str(valor)),
        )


def analisis_progreso(*, stalled=()) -> ProgressAnalysis:
    return ProgressAnalysis(
        summary="Vas bien en general.",
        patterns=["Volumen estable"],
        stalled=[
            StalledExercise(exercise=nombre, weeks_stalled=6, likely_cause="poco volumen")
            for nombre in stalled
        ],
        recommendations=["Sube una serie en press"],
        proposed_changes=[
            ProposedChange(target="Lunes", change="Añadir una serie", reason="Estancamiento")
        ],
        data_caveats=[],
    )


class TestProgreso:
    def test_no_llama_al_modelo_sin_historial(self, user):
        sesiones(user, MIN_SESSIONS - 1)

        with patch("apps.aiassist.services.progress_analyzer.get_provider") as get_prov:
            with pytest.raises(NotEnoughData, match=str(MIN_SESSIONS)):
                analyze_progress(user)

            get_prov.assert_not_called()

    def test_con_historial_suficiente_analiza(self, user):
        sesiones(user, MIN_SESSIONS)

        with patch("apps.aiassist.services.progress_analyzer.get_provider") as get_prov:
            configurar(get_prov, analisis_progreso())
            generation = analyze_progress(user)

        assert generation.kind == GenerationKind.PROGRESS
        assert generation.status == GenerationStatus.OK

    def test_las_metricas_llegan_con_su_cobertura(self, user):
        sesiones(user, MIN_SESSIONS)

        with patch("apps.aiassist.services.progress_analyzer.get_provider") as get_prov:
            configurar(get_prov, analisis_progreso())
            analyze_progress(user)

        enviado = get_prov.return_value.generate_structured.call_args.kwargs["user"]
        assert "cobertura" in enviado

    def test_un_estancamiento_genera_aviso(self, user):
        sesiones(user, MIN_SESSIONS)
        with patch("apps.aiassist.services.progress_analyzer.get_provider") as get_prov:
            configurar(get_prov, analisis_progreso(stalled=["Press de banca"]))
            generation = analyze_progress(user)

        notificacion = notify_progress(generation)

        assert notificacion.kind == NotificationKind.STALL_DETECTED
        assert notificacion.severity == Severity.WARNING
        assert "Press de banca" in notificacion.body

    def test_sin_estancamiento_el_aviso_es_informativo(self, user):
        sesiones(user, MIN_SESSIONS)
        with patch("apps.aiassist.services.progress_analyzer.get_provider") as get_prov:
            configurar(get_prov, analisis_progreso())
            generation = analyze_progress(user)

        notificacion = notify_progress(generation)

        assert notificacion.kind == NotificationKind.PROGRESS_READY
        assert notificacion.severity == Severity.INFO


class TestPuertaDeterminista:
    def test_con_pocos_registros_no_analiza(self, user):
        pesos(user, [75, 75.2])

        procede, motivo = should_analyze(user)

        assert procede is False
        assert "registros de peso" in motivo

    def test_si_el_ritmo_va_acorde_no_analiza(self, user):
        pesos(user, [75.0, 75.05, 75.1, 75.15, 75.2, 75.25, 75.3, 75.35])

        procede, motivo = should_analyze(user)

        assert procede is False
        assert "acorde al objetivo" in motivo

    def test_si_el_ritmo_se_desvia_si_analiza(self, user):
        pesos(user, [78, 77.5, 77.0, 76.5, 76.0, 75.5, 75.0, 74.5])

        procede, motivo = should_analyze(user)

        assert procede is True
        assert "se aparta" in motivo

    def test_no_repite_el_analisis_en_la_misma_semana(self, user):
        pesos(user, [78, 77.5, 77.0, 76.5, 76.0, 75.5, 75.0, 74.5])
        AIGeneration.objects.create(
            user=user, kind=GenerationKind.WEIGHT, provider="anthropic",
            model="m", status=GenerationStatus.OK,
        )

        procede, motivo = should_analyze(user)

        assert procede is False
        assert str(COOLDOWN_DAYS) in motivo

    def test_pasado_el_periodo_vuelve_a_analizar(self, user):
        pesos(user, [78, 77.5, 77.0, 76.5, 76.0, 75.5, 75.0, 74.5])
        vieja = AIGeneration.objects.create(
            user=user, kind=GenerationKind.WEIGHT, provider="anthropic",
            model="m", status=GenerationStatus.OK,
        )
        AIGeneration.objects.filter(pk=vieja.pk).update(
            created_at=timezone.now() - timedelta(days=COOLDOWN_DAYS + 1)
        )

        procede, _ = should_analyze(user)

        assert procede is True


class TestObjetivoDePeso:
    @pytest.mark.parametrize(
        "goal, esperado", [("bulk", 0.25), ("cut", -0.5), ("maintain", 0.0)]
    )
    def test_ritmo_por_defecto_segun_objetivo(self, user, goal, esperado):
        user.goal = goal
        user.save()

        assert target_rate(user) == esperado

    def test_el_objetivo_propio_manda_sobre_el_de_por_defecto(self, user):
        user.weekly_weight_change_target_kg = Decimal("0.4")
        user.save()

        assert target_rate(user) == 0.4


class TestAvisoDePeso:
    def _generar(self, user, *, on_track):
        analisis = WeightAnalysis(
            trend="bajando", rate_kg_per_week=-0.5, on_track=on_track,
            message="Estás perdiendo peso.", recommendation="Sube las calorías.",
        )
        pesos(user, [78, 77.5, 77.0, 76.5, 76.0, 75.5, 75.0, 74.5])
        with patch("apps.aiassist.services.weight_analyzer.get_provider") as get_prov:
            configurar(get_prov, analisis)
            return analyze_weight(user)

    def test_si_va_desviado_avisa(self, user):
        generation = self._generar(user, on_track=False)

        notificacion = notify_weight(generation)

        assert notificacion.kind == NotificationKind.WEIGHT_OFF_TRACK
        assert "Sube las calorías" in notificacion.body

    def test_si_va_bien_no_avisa(self, user):
        generation = self._generar(user, on_track=True)

        assert notify_weight(generation) is None
        assert Notification.objects.count() == 0


class TestCorreo:
    def test_la_notificacion_se_envia_por_correo(self, user):
        sesiones(user, MIN_SESSIONS)
        with patch("apps.aiassist.services.progress_analyzer.get_provider") as get_prov:
            configurar(get_prov, analisis_progreso(stalled=["Press"]))
            generation = analyze_progress(user)

        notify_progress(generation)

        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == ["atleta@example.com"]

    def test_sin_correo_no_se_intenta_enviar(self, user):
        user.email = ""
        user.save()
        sesiones(user, MIN_SESSIONS)
        with patch("apps.aiassist.services.progress_analyzer.get_provider") as get_prov:
            configurar(get_prov, analisis_progreso())
            generation = analyze_progress(user)

        notify_progress(generation)

        assert len(mail.outbox) == 0

    def test_no_se_envia_dos_veces(self, user):
        from apps.notifications.services import deliver_email

        notificacion = Notification.objects.create(
            user=user, kind=NotificationKind.PROGRESS_READY, title="Hola", body="Qué tal"
        )

        assert deliver_email(notificacion) is True
        assert deliver_email(notificacion) is False
        assert len(mail.outbox) == 1


class TestElMotivoNoFiltraDatosDeSalud:
    def test_ningun_motivo_incluye_kilos(self, user):
        import re

        from apps.bodyweight.models import BodyWeightEntry

        hoy = date.today()
        for dias in range(0, 40, 4):
            BodyWeightEntry.objects.create(
                user=user,
                date=hoy - timedelta(days=dias),
                weight_kg=Decimal("80") - Decimal(dias) * Decimal("0.2"),
            )

        _, motivo = should_analyze(user)

        assert "kg" not in motivo, f"«{motivo}» lleva una cifra de peso al log"
        assert not re.search(r"-?\d+[.,]\d+", motivo), f"«{motivo}» lleva un decimal al log"
