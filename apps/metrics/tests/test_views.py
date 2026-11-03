import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command

from apps.metrics.models import Metric, UserMetricPreference
from apps.metrics.services import visible_for

pytestmark = pytest.mark.django_db

User = get_user_model()


@pytest.fixture
def catalogo(db):
    call_command("sync_metrics")
    return Metric.objects.all()


class TestQueVeQuienNoHaElegido:
    def test_sin_preferencias_se_usan_las_visibles_por_defecto(self, user, catalogo):
        assert len(visible_for(user)) == Metric.objects.count()

    def test_una_metrica_desactivada_no_sale_para_nadie(self, user, catalogo):
        Metric.objects.filter(key="session_density").update(is_active=False)

        assert "session_density" not in visible_for(user)


class TestLaEleccionEsDeCadaUno:
    def test_la_de_uno_no_afecta_a_otro(self, user, catalogo):
        otro = User.objects.create_user("otro", password="Contrasena-Larga-2")
        for metrica in catalogo:
            UserMetricPreference.objects.create(
                user=user, metric=metrica, is_visible=(metrica.key == "weekly_tonnage")
            )

        assert visible_for(user) == ["weekly_tonnage"]
        assert len(visible_for(otro)) == Metric.objects.count()

    def test_una_preferencia_apagada_pesa_mas_que_el_valor_por_defecto(self, user, catalogo):
        marcada_por_defecto = catalogo.filter(default_visible=True).first()
        UserMetricPreference.objects.create(
            user=user, metric=marcada_por_defecto, is_visible=False
        )

        assert marcada_por_defecto.key not in visible_for(user)
