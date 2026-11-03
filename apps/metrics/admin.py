from django.contrib import admin

from .models import Metric, UserMetricPreference


@admin.register(Metric)
class MetricAdmin(admin.ModelAdmin):
    list_display = ("label", "category_label", "unit", "is_active", "send_to_ai", "default_visible")
    list_filter = ("category", "is_active", "send_to_ai")
    list_editable = ("is_active", "send_to_ai", "default_visible")
    search_fields = ("key", "label")

    readonly_fields = ("key", "label", "description", "unit", "category", "chart", "order")

    fieldsets = (
        ("Definición (viene del código)", {
            "fields": ("key", "label", "description", "unit", "category", "chart", "order"),
            "description": (
                "Estos campos los genera `python manage.py sync_metrics` desde el registro del "
                "código. Para cambiarlos, edita la métrica en `apps/metrics/catalog/`."
            ),
        }),
        ("Configuración", {
            "fields": ("is_active", "send_to_ai", "default_visible"),
        }),
    )

    def has_add_permission(self, request):
        return False


@admin.register(UserMetricPreference)
class UserMetricPreferenceAdmin(admin.ModelAdmin):
    list_display = ("user", "metric", "is_visible")
    list_filter = ("is_visible", "metric")
    search_fields = ("user__username",)
    autocomplete_fields = ("user",)
