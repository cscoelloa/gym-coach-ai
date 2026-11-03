import pytest
from django.core.management import call_command

from apps.metrics.models import Metric
from apps.metrics.registry import CATEGORY_LABELS, REGISTRY, REQUIRES_LABELS

pytestmark = pytest.mark.django_db


class TestRegistro:
    def test_el_registro_no_esta_vacio(self):
        assert len(REGISTRY) >= 12

    @pytest.mark.parametrize("key", sorted(REGISTRY))
    def test_toda_metrica_esta_descrita(self, key):
        spec = REGISTRY[key]

        assert spec.label
        assert spec.description
        assert spec.category in CATEGORY_LABELS
        assert all(requirement in REQUIRES_LABELS for requirement in spec.requires)

    def test_las_descripciones_explican_el_porque(self):
        for spec in REGISTRY.values():
            assert len(spec.description) > 60, f"«{spec.key}» tiene una descripción demasiado corta"


class TestSincronizacion:
    def test_crea_una_fila_por_metrica_registrada(self):
        call_command("sync_metrics")

        assert Metric.objects.count() == len(REGISTRY)
        assert set(Metric.objects.values_list("key", flat=True)) == set(REGISTRY)

    def test_es_idempotente(self):
        call_command("sync_metrics")
        call_command("sync_metrics")

        assert Metric.objects.count() == len(REGISTRY)

    def test_no_pisa_la_configuracion_del_admin(self):
        call_command("sync_metrics")
        Metric.objects.filter(key="session_density").update(is_active=False, send_to_ai=False)

        call_command("sync_metrics")

        metric = Metric.objects.get(key="session_density")
        assert metric.is_active is False
        assert metric.send_to_ai is False

    def test_desactiva_en_vez_de_borrar(self):
        Metric.objects.create(
            key="metrica-retirada", label="Retirada", description="x",
            category="volume", chart="bar",
        )

        call_command("sync_metrics")

        retirada = Metric.objects.get(key="metrica-retirada")
        assert retirada.is_active is False
        assert Metric.objects.filter(key="metrica-retirada").exists()

    def test_actualiza_los_textos_desde_el_codigo(self):
        call_command("sync_metrics")
        Metric.objects.filter(key="adherence_rate").update(label="Texto viejo")

        call_command("sync_metrics")

        assert Metric.objects.get(key="adherence_rate").label == REGISTRY["adherence_rate"].label
