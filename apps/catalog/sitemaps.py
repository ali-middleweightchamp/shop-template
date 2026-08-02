"""Карта сайта для поисковиков: статические страницы, товары, категории."""
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Category, Product


class StaticSitemap(Sitemap):
    priority = 0.6
    changefreq = "weekly"

    def items(self):
        return ["catalog:home", "catalog:catalog", "catalog:contacts"]

    def location(self, item):
        return reverse(item)


class ProductSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Product.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.updated_at


class CategorySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return Category.objects.filter(is_active=True)
