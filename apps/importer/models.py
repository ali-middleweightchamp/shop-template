"""Журнал загрузок прайса. Хранит результат и ошибки каждой загрузки."""
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class ImportLog(models.Model):
    """Одна запись = одна загрузка файла прайса."""

    class Status(models.TextChoices):
        PENDING = "pending", _("Ожидает")
        PREVIEW = "preview", _("Предпросмотр")
        SUCCESS = "success", _("Применён")
        FAILED = "failed", _("Ошибка")

    file = models.FileField(_("Файл"), upload_to="imports/")
    created_at = models.DateTimeField(_("Загружен"), auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("Пользователь"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    rows_total = models.PositiveIntegerField(_("Всего строк"), default=0)
    rows_created = models.PositiveIntegerField(_("Создано"), default=0)
    rows_updated = models.PositiveIntegerField(_("Обновлено"), default=0)
    rows_failed = models.PositiveIntegerField(_("С ошибками"), default=0)

    # Список ошибок вида [{"row": 42, "message": "цена не является числом"}]
    errors = models.JSONField(_("Ошибки"), default=list, blank=True)
    status = models.CharField(
        _("Статус"), max_length=16, choices=Status.choices, default=Status.PENDING
    )

    class Meta:
        verbose_name = _("Загрузка прайса")
        verbose_name_plural = _("Загрузки прайса")
        ordering = ["-created_at"]

    def __str__(self):
        return f"Импорт от {self.created_at:%d.%m.%Y %H:%M} — {self.get_status_display()}"
