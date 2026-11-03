from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "email", "goal", "experience_level", "is_staff")
    list_filter = BaseUserAdmin.list_filter + ("goal", "experience_level")

    fieldsets = BaseUserAdmin.fieldsets + (
        (
            "Perfil de entrenamiento",
            {
                "fields": (
                    "goal",
                    "experience_level",
                    "target_weight_kg",
                    "weekly_weight_change_target_kg",
                    "available_days_per_week",
                    "available_equipment",
                )
            },
        ),
        (
            "Datos de salud",
            {
                "fields": ("sex", "birth_date", "height_cm", "injuries_notes"),
                "description": (
                    "Categoría sensible. No copiar a logs, tickets ni capturas de pantalla."
                ),
            },
        ),
    )
