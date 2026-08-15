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
        "order_message_footer",
        "topbar_location",
        "delivery_note",
        "about_title",
        "about_text",
        "trust1_text",
        "trust2_text",
        "trust3_text",
        "trust4_text",
    )
