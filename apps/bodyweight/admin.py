from django.contrib import admin

from .models import BodyWeightEntry


@admin.register(BodyWeightEntry)
class BodyWeightEntryAdmin(admin.ModelAdmin):
    list_display = ("user", "date", "weight_kg", "body_fat_pct")
    list_filter = ("date",)
    search_fields = ("user__username",)
    date_hierarchy = "date"
    autocomplete_fields = ("user",)
