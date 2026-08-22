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
        "faq1_q", "faq1_a",
        "faq2_q", "faq2_a",
        "faq3_q", "faq3_a",
        "faq4_q", "faq4_a",
        "faq5_q", "faq5_a",
    )
