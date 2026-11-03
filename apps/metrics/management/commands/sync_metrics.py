from django.core.management.base import BaseCommand

from apps.metrics.models import Metric
from apps.metrics.registry import REGISTRY


class Command(BaseCommand):
    help = "Sincroniza el catálogo de métricas con el registro del código."

    def handle(self, *args, **options):
        created = updated = 0

        for key, spec in REGISTRY.items():
            _obj, was_created = Metric.objects.update_or_create(
                key=key,
                defaults={
                    "label": spec.label,
                    "description": spec.description,
                    "unit": spec.unit,
                    "category": str(spec.category),
                    "chart": str(spec.chart),
                    "order": spec.order,
                },
            )
            created += was_created
            updated += not was_created

        stale = Metric.objects.exclude(key__in=REGISTRY).filter(is_active=True)
        deactivated = stale.count()
        stale.update(is_active=False)

        self.stdout.write(
            self.style.SUCCESS(
                f"Métricas sincronizadas: {created} creadas, {updated} actualizadas, "
                f"{deactivated} desactivadas."
            )
        )
