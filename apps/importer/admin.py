"""
Админка журнала загрузок прайса. Пока только просмотр истории;
страница самой загрузки с предпросмотром появится на этапе 7.
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import ImportLog


@admin.register(ImportLog)
class ImportLogAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "status",
        "rows_total",
        "rows_created",
        "rows_updated",
        "rows_failed",
        "user",
    )
    list_filter = ("status", "created_at")
    readonly_fields = (
        "file",
        "created_at",
        "user",
        "rows_total",
        "rows_created",
        "rows_updated",
        "rows_failed",
        "status",
        "errors",
    )
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        # Загрузка идёт через отдельную страницу импорта (этап 7), не отсюда
        return False

    class Meta:
        verbose_name = _("Загрузка прайса")
