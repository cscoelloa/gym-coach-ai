import pytest
from django.contrib.auth import get_user_model
from django.core.management import CommandError, call_command

from apps.bodyweight.models import BodyWeightEntry
from apps.workouts.models import (
    Exercise,
    MuscleGroup,
    Program,
    Routine,
    SetLog,
    WorkoutSession,
)

pytestmark = pytest.mark.django_db

User = get_user_model()

CATALOGO = [
    ("0001", "barbell bench press", "chest", "barbell"),
    ("0002", "cable shoulder press", "shoulders", "cable"),
    ("0003", "cable pushdown", "upper arms", "cable"),
    ("0004", "barbell bent over row", "back", "barbell"),
    ("0005", "alternate lateral pulldown", "back", "cable"),
    ("0006", "barbell curl", "upper arms", "barbell"),
    ("0007", "barbell full squat", "upper legs", "barbell"),
    ("0008", "lever leg extension", "upper legs", "leverage machine"),
    ("0009", "lever lying leg curl", "upper legs", "leverage machine"),
    ("0010", "barbell incline bench press", "chest", "barbell"),
    ("0011", "cable lateral raise", "shoulders", "cable"),
]


@pytest.fixture
def catalogo():
    musculo = MuscleGroup.objects.create(slug="pectorals", name="Pectorales")
    return [
        Exercise.objects.create(
            external_id=ext, name=nombre, slug=ext, body_part=zona,
            equipment=equipo, target_muscle=musculo, is_global=True,
        )
        for ext, nombre, zona, equipo in CATALOGO
    ]


class TestRequisitos:
    def test_sin_catalogo_falla_con_una_pista(self, db):
        with pytest.raises(CommandError, match="import_catalog"):
            call_command("seed_demo")

    def test_no_pisa_un_usuario_existente_sin_pedirlo(self, catalogo):
        call_command("seed_demo")

        with pytest.raises(CommandError, match="--reset"):
            call_command("seed_demo")

    def test_con_reset_lo_recrea(self, catalogo):
        call_command("seed_demo")
        primero = User.objects.get(username="demo").pk

        call_command("seed_demo", reset=True)

        assert User.objects.get(username="demo").pk != primero
        assert User.objects.filter(username="demo").count() == 1


class TestDatosGenerados:
    def test_crea_usuario_rutinas_e_historial(self, catalogo):
        call_command("seed_demo")

        user = User.objects.get(username="demo")
        assert Routine.objects.filter(user=user).count() == 3
        assert Program.objects.get(user=user).schedule.count() == 7
        assert WorkoutSession.objects.filter(user=user).count() > 20
        assert BodyWeightEntry.objects.filter(user=user).count() > 30
        assert SetLog.objects.filter(session__user=user).count() > 100

    def test_una_rutina_esta_asignada_a_DOS_dias(self, catalogo):
        call_command("seed_demo")
        user = User.objects.get(username="demo")

        empuje = Routine.objects.get(user=user, name="Empuje")
        dias = empuje.scheduled_on.values_list("weekday", flat=True)

        assert sorted(dias) == [0, 3]

    def test_editar_la_rutina_afecta_a_los_dos_dias(self, catalogo):
        call_command("seed_demo")
        user = User.objects.get(username="demo")

        empuje = Routine.objects.get(user=user, name="Empuje")
        primero = empuje.exercises.order_by("order").first()
        primero.target_sets = 7
        primero.save(update_fields=["target_sets"])

        programa = Program.objects.get(user=user)
        lunes = programa.schedule.get(weekday=0).routine
        jueves = programa.schedule.get(weekday=3).routine

        assert lunes == jueves == empuje
        assert lunes.exercises.order_by("order").first().target_sets == 7
        assert jueves.exercises.order_by("order").first().target_sets == 7

    def test_el_historial_es_reproducible(self, catalogo):
        call_command("seed_demo")
        primero = SetLog.objects.filter(session__user__username="demo").count()

        call_command("seed_demo", reset=True)
        segundo = SetLog.objects.filter(session__user__username="demo").count()

        assert primero == segundo

    def test_la_adherencia_no_sale_perfecta(self, catalogo):
        call_command("seed_demo")
        user = User.objects.get(username="demo")

        sesiones = WorkoutSession.objects.filter(user=user).count()
        assert sesiones < 4 * 12


class TestLoQueElAnalisisDebeEncontrar:
    def test_hay_un_ejercicio_estancado(self, catalogo):
        from apps.metrics.catalog.strength import stalled_exercises
        from apps.metrics.context import MetricContext

        call_command("seed_demo")
        user = User.objects.get(username="demo")

        resultado = stalled_exercises(MetricContext(user=user))

        assert resultado.value >= 1
        assert any("bench press" in fila[0] for fila in resultado.rows)

    def test_el_peso_se_aparta_del_objetivo(self, catalogo):
        from apps.aiassist.services.weight_analyzer import should_analyze

        call_command("seed_demo")
        user = User.objects.get(username="demo")

        procede, motivo = should_analyze(user)

        assert procede is True
        assert "se aparta" in motivo

    def test_alguna_sesion_se_queda_sin_cerrar(self, catalogo):
        from apps.metrics.catalog.consistency import session_density
        from apps.metrics.context import MetricContext

        call_command("seed_demo")
        user = User.objects.get(username="demo")

        resultado = session_density(MetricContext(user=user))

        assert 0 < resultado.coverage < 1
        assert resultado.value is not None, "sin ninguna sesión cronometrada no habría cifra"
