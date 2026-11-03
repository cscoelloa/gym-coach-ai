from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "kind", "severity", "is_read", "emailed_at", "created_at")
    list_filter = ("kind", "severity", "is_read", "created_at")
    search_fields = ("user__username", "title")
    date_hierarchy = "created_at"
    autocomplete_fields = ("user",)
    readonly_fields = ("generation", "payload", "emailed_at", "created_at")
