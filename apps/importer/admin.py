"""
Админка импортёра: страница загрузки прайса с предпросмотром и применением,
скачивание шаблона, экспорт каталога, история загрузок.
"""
from django.contrib import admin, messages
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import path
from django.utils.translation import gettext_lazy as _

from . import services
from .models import ImportLog


@admin.register(ImportLog)
class ImportLogAdmin(admin.ModelAdmin):
    list_display = (
        "created_at", "status", "rows_total", "rows_created",
        "rows_updated", "rows_failed", "user",
    )
    list_filter = ("status", "created_at")
    date_hierarchy = "created_at"
    readonly_fields = (
        "file", "created_at", "user", "rows_total", "rows_created",
        "rows_updated", "rows_failed", "status", "errors",
    )

    def has_add_permission(self, request):
        return False

    # --- Кастомные страницы ---
    def get_urls(self):
        custom = [
            path("import/", self.admin_site.admin_view(self.import_view), name="importer_import"),
            path("import/template/", self.admin_site.admin_view(self.template_view), name="importer_template"),
            path("import/export/", self.admin_site.admin_view(self.export_view), name="importer_export"),
        ]
        return custom + super().get_urls()

    def import_view(self, request):
        preview = None

        # Шаг 2: применить ранее загруженный файл
        if request.method == "POST" and request.POST.get("apply") and request.POST.get("log_id"):
            log = ImportLog.objects.filter(pk=request.POST["log_id"]).first()
            if log:
                log.file.open("rb")
                try:
                    result = services.apply(log.file)
                finally:
                    log.file.close()
                if result.get("missing_columns"):
                    log.status = ImportLog.Status.FAILED
                    log.save()
                    messages.error(request, _("Не хватает колонок: %s") % ", ".join(result["missing_columns"]))
                else:
                    log.rows_total = result.get("rows_total", 0)
                    log.rows_created = result.get("rows_created", 0)
                    log.rows_updated = result.get("rows_updated", 0)
                    log.rows_failed = len(result.get("errors", []))
                    log.errors = result.get("errors", [])
                    log.status = ImportLog.Status.SUCCESS
                    log.save()
                    messages.success(
                        request,
                        _("Импорт применён: создано %(c)d, обновлено %(u)d, ошибок %(e)d.")
                        % {"c": log.rows_created, "u": log.rows_updated, "e": log.rows_failed},
                    )
            return redirect("admin:importer_import")

        # Шаг 1: загрузка файла → предпросмотр
        if request.method == "POST" and request.FILES.get("file"):
            log = ImportLog.objects.create(
                file=request.FILES["file"], user=request.user,
                status=ImportLog.Status.PREVIEW,
            )
            log.file.open("rb")
            try:
                preview = services.analyze(log.file)
            finally:
                log.file.close()
            preview["log_id"] = log.pk
            log.rows_total = preview["rows_total"]
            log.rows_failed = len(preview["errors"])
            log.errors = preview["errors"]
            log.save()

        context = {
            **self.admin_site.each_context(request),
            "title": _("Загрузка прайса"),
            "preview": preview,
            "history": ImportLog.objects.all()[:12],
            "opts": self.model._meta,
        }
        return render(request, "admin/importer/import.html", context)

    def template_view(self, request):
        content = services.build_template()
        resp = HttpResponse(
            content,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        resp["Content-Disposition"] = 'attachment; filename="price-template.xlsx"'
        return resp

    def export_view(self, request):
        content = services.export_catalog()
        resp = HttpResponse(
            content,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        resp["Content-Disposition"] = 'attachment; filename="catalog.xlsx"'
        return resp
