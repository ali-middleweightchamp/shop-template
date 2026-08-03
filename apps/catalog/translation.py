"""Двуязычные поля каталога (ru/uz) для django-modeltranslation."""
from modeltranslation.translator import TranslationOptions, register

from .models import Banner, Category, Product


@register(Category)
class CategoryTR(TranslationOptions):
    fields = ("name",)


@register(Banner)
class BannerTR(TranslationOptions):
    fields = ("title", "subtitle", "badge", "button_text")


@register(Product)
class ProductTR(TranslationOptions):
    fields = ("name", "description")
