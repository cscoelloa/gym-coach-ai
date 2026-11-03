from django.contrib import admin
from django.utils.html import format_html

from .models import (
    Exercise,
    MuscleGroup,
    Program,
    Routine,
    RoutineExercise,
    ScheduleEntry,
    SetLog,
    WorkoutSession,
)


@admin.register(MuscleGroup)
class MuscleGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "primary_count")
    search_fields = ("name", "slug")

    @admin.display(description="ejercicios como objetivo")
    def primary_count(self, obj):
        return obj.primary_exercises.count()


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ("thumbnail", "name", "external_id", "body_part", "equipment", "target_muscle")
    list_display_links = ("name",)
    list_filter = ("body_part", "equipment", "is_cardio", "is_bodyweight", "is_global")
    search_fields = ("name", "external_id")
    autocomplete_fields = ("target_muscle", "secondary_muscles")
    readonly_fields = ("preview", "attribution", "external_id")
    list_select_related = ("target_muscle",)

    fieldsets = (
        (None, {"fields": ("name", "slug", "external_id", "is_global", "created_by")}),
        ("Clasificación", {
            "fields": ("body_part", "category", "equipment", "target_muscle",
                       "secondary_muscles", "is_cardio", "is_bodyweight"),
        }),
        ("Material visual", {
            "fields": ("preview", "image", "animation", "attribution"),
            "description": (
                "La atribución es un requisito de licencia del material visual y no debe "
                "modificarse ni ocultarse. Ver .docs/01-decisions.md (ADR-007)."
            ),
        }),
        ("Instrucciones", {"fields": ("instruction_steps",), "classes": ("collapse",)}),
    )

    @admin.display(description="")
    def thumbnail(self, obj):
        if not obj.image:
            return "—"
        return format_html('<img src="{}" height="48" alt="">', obj.image.url)

    @admin.display(description="vista previa")
    def preview(self, obj):
        if not obj.animation:
            return "—"
        return format_html(
            '<div><img src="{}" height="180" alt=""></div>'
            '<p style="margin-top:.5rem;color:#666">{}</p>',
            obj.animation.url,
            obj.attribution,
        )


class RoutineExerciseInline(admin.TabularInline):
    model = RoutineExercise
    extra = 0
    autocomplete_fields = ("exercise",)


@admin.register(Routine)
class RoutineAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "source", "scheduled_days", "created_at")
    list_filter = ("source",)
    search_fields = ("name", "user__username")
    inlines = [RoutineExerciseInline]
    autocomplete_fields = ("user",)

    @admin.display(description="asignada a")
    def scheduled_days(self, obj):
        dias = [entrada.get_weekday_display() for entrada in obj.scheduled_on.all()]
        return ", ".join(dias) if dias else "—"


class ScheduleEntryInline(admin.TabularInline):
    model = ScheduleEntry
    extra = 0
    fields = ("weekday", "routine")
    autocomplete_fields = ("routine",)


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "source", "is_active", "created_at")
    list_filter = ("is_active", "source")
    search_fields = ("name", "user__username")
    inlines = [ScheduleEntryInline]
    autocomplete_fields = ("user",)


class SetLogInline(admin.TabularInline):
    model = SetLog
    extra = 0
    autocomplete_fields = ("exercise",)


@admin.register(WorkoutSession)
class WorkoutSessionAdmin(admin.ModelAdmin):
    list_display = ("user", "date", "routine")
    list_filter = ("date",)
    search_fields = ("user__username",)
    date_hierarchy = "date"
    inlines = [SetLogInline]
    autocomplete_fields = ("user", "routine")
