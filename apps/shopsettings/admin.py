"""
Админка настроек магазина. Singleton: добавить вторую запись нельзя,
удалить нельзя, при заходе в раздел сразу открывается единственная запись.
"""
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from modeltranslation.admin import TranslationAdmin

from .models import ShopSettings


@admin.register(ShopSettings)
class ShopSettingsAdmin(TranslationAdmin):
    readonly_fields = ("color_preview",)

    fieldsets = (
        (_("Бренд"), {"fields": ("name", "tagline", "logo", "description")}),
        (_("Оформление"), {"fields": ("theme", "primary_color", "color_preview")}),
        (
            _("Контакты для заказа"),
            {
                "fields": ("telegram_username", "whatsapp_phone", "phone", "phone_secondary"),
                "description": _(
                    "Именно сюда покупатель отправит готовый заказ. "
                    "Telegram — без символа @."
                ),
            },
        ),
        (_("Адрес и время работы"), {"fields": ("address", "map_link", "work_hours")}),
        (_("Соцсети"), {"fields": ("instagram_url", "telegram_channel_url")}),
        (
            _("Витрина"),
            {
                "fields": (
                    "currency_label",
                    "min_order_amount",
                    "order_message_header",
                    "order_message_footer",
                    "show_prices",
                )
            },
        ),
    )

    @admin.display(description=_("Как выглядит цвет"))
    def color_preview(self, obj):
        color = obj.primary_color or "#2563eb"
        return format_html(
            '<span style="display:inline-block;width:120px;height:32px;'
            'border-radius:6px;border:1px solid #ccc;background:{}"></span>'
            '<span style="margin-left:8px;color:#666">{}</span>',
            color,
            color,
        )

    def has_add_permission(self, request):
        # Запрещаем добавлять вторую запись
        return not ShopSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Singleton нельзя удалить
        return False

    def changelist_view(self, request, extra_context=None):
        # Вместо списка сразу открываем единственную запись настроек
        obj = ShopSettings.get_solo()
        return redirect(
            reverse("admin:shopsettings_shopsettings_change", args=[obj.pk])
        )
