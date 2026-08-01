"""Каталог: категории (до 2 уровней), товары и их дополнительные фото."""
import secrets

from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


def unique_slug(model, base, instance_pk=None):
    """Уникальный slug на основе base (с числовым суффиксом при коллизии)."""
    base = (base or "item").strip("-") or "item"
    slug = base
    i = 2
    qs = model.objects.exclude(pk=instance_pk)
    while qs.filter(slug=slug).exists():
        slug = f"{base}-{i}"
        i += 1
    return slug

# Без похожих символов (0/O, 1/I) — код читают и диктуют
_CODE_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"


def generate_order_code(length=6):
    return "".join(secrets.choice(_CODE_ALPHABET) for _ in range(length))


class Category(models.Model):
    """Категория товаров. Допускается вложенность максимум в 2 уровня."""

    name = models.CharField(_("Название"), max_length=255)
    slug = models.SlugField(_("Ссылка (slug)"), max_length=255, unique=True, blank=True)
    parent = models.ForeignKey(
        "self",
        verbose_name=_("Родительская категория"),
        on_delete=models.CASCADE,
        related_name="children",
        null=True,
        blank=True,
    )
    image = models.ImageField(_("Картинка"), upload_to="categories/", blank=True)
    order = models.PositiveIntegerField(_("Порядок"), default=0)
    is_active = models.BooleanField(_("Активна"), default=True)

    class Meta:
        verbose_name = _("Категория")
        verbose_name_plural = _("Категории")
        ordering = ["order", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name, allow_unicode=True) or slugify(self.name)
            self.slug = unique_slug(Category, base, self.pk)
        super().save(*args, **kwargs)

    def clean(self):
        # Ограничение глубины: у родителя не должно быть своего родителя (макс 2 уровня)
        if self.parent and self.parent.parent_id:
            raise ValidationError(_("Максимальная вложенность категорий — 2 уровня."))
        # Категория не может быть родителем самой себе
        if self.parent_id and self.parent_id == self.pk:
            raise ValidationError(_("Категория не может быть родителем самой себе."))

    def get_absolute_url(self):
        return reverse("catalog:category", kwargs={"slug": self.slug})


class Product(models.Model):
    """Товар. Ключ для импорта прайса — sku."""

    class Unit(models.TextChoices):
        PIECE = "шт", _("шт")
        PACK = "упак", _("упак")
        KG = "кг", _("кг")
        METER = "м", _("м")

    name = models.CharField(_("Название"), max_length=255)
    slug = models.SlugField(_("Ссылка (slug)"), max_length=255, unique=True, blank=True)
    sku = models.CharField(_("Артикул"), max_length=64, unique=True)
    category = models.ForeignKey(
        Category,
        verbose_name=_("Категория"),
        on_delete=models.PROTECT,
        related_name="products",
    )

    price = models.DecimalField(_("Цена"), max_digits=12, decimal_places=2)
    old_price = models.DecimalField(
        _("Старая цена"), max_digits=12, decimal_places=2, null=True, blank=True
    )

    unit = models.CharField(
        _("Единица"), max_length=8, choices=Unit.choices, default=Unit.PIECE
    )
    pack_size = models.CharField(
        _("Фасовка"), max_length=64, blank=True, help_text=_("Например: 12 шт в упаковке")
    )

    description = models.TextField(_("Описание"), blank=True)
    image = models.ImageField(_("Фото"), upload_to="products/", blank=True)

    in_stock = models.BooleanField(_("В наличии"), default=True)
    is_active = models.BooleanField(_("Показывать на сайте"), default=True)
    is_featured = models.BooleanField(_("Популярный"), default=False)
    order = models.PositiveIntegerField(_("Порядок"), default=0)

    created_at = models.DateTimeField(_("Создан"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Обновлён"), auto_now=True)

    class Meta:
        verbose_name = _("Товар")
        verbose_name_plural = _("Товары")
        ordering = ["order", "name"]
        indexes = [
            models.Index(fields=["sku"]),
            models.Index(fields=["category"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.sku})"

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.sku) or slugify(self.name, allow_unicode=True)
            self.slug = unique_slug(Product, base, self.pk)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("catalog:product", kwargs={"slug": self.slug})

    def get_display_price(self):
        """Цена для показа с учётом настройки show_prices.
        Если показ цен выключен — возвращаем None (шаблон покажет «по запросу»)."""
        from apps.shopsettings.models import ShopSettings

        if not ShopSettings.get_solo().show_prices:
            return None
        return self.price

    def discount_percent(self):
        """Процент скидки, если задана старая цена больше текущей. Иначе None."""
        if self.old_price and self.old_price > self.price and self.old_price > 0:
            return int(round((self.old_price - self.price) / self.old_price * 100))
        return None


class ProductImage(models.Model):
    """Дополнительное фото товара (галерея)."""

    product = models.ForeignKey(
        Product,
        verbose_name=_("Товар"),
        on_delete=models.CASCADE,
        related_name="images",
    )
    image = models.ImageField(_("Фото"), upload_to="products/")
    order = models.PositiveIntegerField(_("Порядок"), default=0)

    class Meta:
        verbose_name = _("Фото товара")
        verbose_name_plural = _("Фото товара")
        ordering = ["order"]

    def __str__(self):
        return f"Фото #{self.pk} — {self.product.name}"


class ShortOrder(models.Model):
    """Сохранённый состав заказа для длинных корзин.

    Если готовый текст для Telegram/WhatsApp длиннее лимита, отправляем
    сокращённый вариант с коротким кодом и ссылкой /order/<code>/, где лежит
    полный состав. payload — снимок корзины на момент оформления.
    """

    code = models.CharField(_("Код заказа"), max_length=12, unique=True, db_index=True)
    payload = models.JSONField(_("Состав заказа"))
    created_at = models.DateTimeField(_("Создан"), auto_now_add=True)

    class Meta:
        verbose_name = _("Заказ по ссылке")
        verbose_name_plural = _("Заказы по ссылке")
        ordering = ["-created_at"]

    def __str__(self):
        return f"Заказ {self.code}"

    def save(self, *args, **kwargs):
        # Генерируем уникальный код при первом сохранении
        if not self.code:
            for _attempt in range(10):
                candidate = generate_order_code()
                if not ShortOrder.objects.filter(code=candidate).exists():
                    self.code = candidate
                    break
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("catalog:order", kwargs={"code": self.code})
