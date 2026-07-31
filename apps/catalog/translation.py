"""Двуязычные поля каталога (ru/uz) для django-modeltranslation."""
from modeltranslation.translator import TranslationOptions, register

from .models import Category, Product


@register(Category)
class CategoryTR(TranslationOptions):
    fields = ("name",)


@register(Product)
class ProductTR(TranslationOptions):
    fields = ("name", "description")
