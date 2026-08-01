"""Двуязычные поля настроек магазина (ru/uz)."""
from modeltranslation.translator import TranslationOptions, register

from .models import ShopSettings


@register(ShopSettings)
class ShopSettingsTR(TranslationOptions):
    fields = (
        "name",
        "tagline",
        "description",
        "address",
        "work_hours",
        "currency_label",
        "order_message_header",
    )
