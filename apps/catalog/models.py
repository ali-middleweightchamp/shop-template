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
        SET = "набор", _("набор")
        PAIR = "пара", _("пара")
        KG = "кг", _("кг")
        GRAM = "г", _("г")
        LITER = "л", _("л")
        ML = "мл", _("мл")
        METER = "м", _("м")
        ROLL = "рулон", _("рулон")

    name = models.CharField(_("Название"), max_length=255)
    slug = models.SlugField(_("Ссылка (slug)"), max_length=255, unique=True, blank=True)
    sku = models.CharField(
        _("Артикул"),
        max_length=64,
        unique=True,
        blank=True,
        help_text=_("Ключ для импорта прайса. Оставьте пустым — сгенерируется автоматически."),
    )
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
    # Полки на главной: владелец сам отмечает товары для каждой из них
    is_featured = models.BooleanField(_("Популярный"), default=False)
    is_new = models.BooleanField(_("Новинка"), default=False)
    is_bestseller = models.BooleanField(_("Хит продаж"), default=False)
    order = models.PositiveIntegerField(_("Порядок"), default=0)

    created_at = models.DateTimeField(_("Создан"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Обновлён"), auto_now=True)

    # Денормализованный текст для поиска в нижнем регистре: регистронезависимый
    # поиск по кириллице работает и на SQLite (LIKE), и на PostgreSQL.
    search_blob = models.TextField(editable=False, blank=True, default="")

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
        # Артикул не задан вручную — генерируем уникальный (ART-XXXXXX).
        # Если продавец указал свой (для сопоставления с Excel) — оставляем его.
        if not self.sku:
            for _attempt in range(10):
                candidate = f"ART-{generate_order_code(6)}"
                if not Product.objects.filter(sku=candidate).exists():
                    self.sku = candidate
                    break
        if not self.slug:
            base = slugify(self.sku) or slugify(self.name, allow_unicode=True)
            self.slug = unique_slug(Product, base, self.pk)
        parts = [self.name_ru, self.name_uz, self.sku, self.description_ru, self.pack_size]
        self.search_blob = " ".join(p for p in parts if p).lower()
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


class Banner(models.Model):
    """Слайд hero-баннера на главной. Продавец управляет ими из панели.

    Показываются только активные и попадающие в период показа, максимум 3.
    Весь блок включается тумблером ShopSettings.banners_enabled.
    """

    title = models.CharField(_("Заголовок"), max_length=60)
    subtitle = models.CharField(_("Подзаголовок"), max_length=120, blank=True)
    badge = models.CharField(_("Текст плашки"), max_length=30, blank=True)
    button_text = models.CharField(_("Текст кнопки"), max_length=30, blank=True)
    button_link = models.CharField(
        _("Ссылка кнопки"), max_length=500, blank=True,
        help_text=_("URL или путь, напр. /catalog/ или https://…"),
    )
    image = models.ImageField(_("Фон"), upload_to="banners/", blank=True)
    is_active = models.BooleanField(_("Активен"), default=True)
    order = models.PositiveIntegerField(_("Порядок"), default=0)
    start_at = models.DateField(_("Показ с"), null=True, blank=True)
    end_at = models.DateField(_("Показ по"), null=True, blank=True)

    class Meta:
        verbose_name = _("Баннер")
        verbose_name_plural = _("Баннеры")
        ordering = ["order", "id"]

    def __str__(self):
        return self.title

    @classmethod
    def active_now(cls):
        """Активные баннеры в пределах периода показа, максимум 3."""
        from django.db.models import Q
        from django.utils import timezone

        today = timezone.localdate()
        return list(
            cls.objects.filter(is_active=True)
            .filter(Q(start_at__isnull=True) | Q(start_at__lte=today))
            .filter(Q(end_at__isnull=True) | Q(end_at__gte=today))
            .order_by("order", "id")[:3]
        )


class ProductAttribute(models.Model):
    """Характеристика товара: название → значение (напр. «Бренд» → «Erich Krause»).

    Гибкая замена жёстко заданным полям: владелец добавляет любые строки —
    бренд, страна, код классификатора (ИКПУ), тип упаковки и т.д. Показываются
    в таблице характеристик на странице товара.
    """

    product = models.ForeignKey(
        Product,
        verbose_name=_("Товар"),
        on_delete=models.CASCADE,
        related_name="attributes",
    )
    name = models.CharField(_("Характеристика"), max_length=100)
    value = models.CharField(_("Значение"), max_length=255)
    order = models.PositiveIntegerField(_("Порядок"), default=0)

    class Meta:
        verbose_name = _("Характеристика")
        verbose_name_plural = _("Характеристики")
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.name}: {self.value}"


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
