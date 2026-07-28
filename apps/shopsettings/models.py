"""
Настройки магазина. Одна запись на весь сайт (singleton): бренд, контакты,
поведение витрины. Кэшируется, доступна в шаблонах как `shop`.
"""
from django.core.cache import cache
from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

# Валидатор HEX-цвета вида #RRGGBB
hex_color_validator = RegexValidator(
    regex=r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$",
    message=_("Цвет должен быть в формате HEX, например #2563eb"),
)


class ShopSettings(models.Model):
    """Singleton: всегда ровно одна запись с pk=1."""

    CACHE_KEY = "shop_settings"

    # --- Бренд ---
    name = models.CharField(_("Название магазина"), max_length=255, default="Магазин")
    logo = models.ImageField(_("Логотип"), upload_to="shop/", blank=True)
    description = models.TextField(_("Описание"), blank=True)
    primary_color = models.CharField(
        _("Фирменный цвет"),
        max_length=7,
        default="#2563eb",
        validators=[hex_color_validator],
        help_text=_("HEX, например #2563eb"),
    )

    # --- Контакты для заказа ---
    telegram_username = models.CharField(
        _("Telegram продавца"),
        max_length=64,
        blank=True,
        help_text=_("Без @, например: myshop"),
    )
    whatsapp_phone = models.CharField(
        _("WhatsApp"),
        max_length=20,
        blank=True,
        help_text=_("Только цифры с кодом страны, например: 998901234567"),
    )
    phone = models.CharField(_("Телефон"), max_length=32, blank=True)
    phone_secondary = models.CharField(_("Доп. телефон"), max_length=32, blank=True)

    # --- Адрес и время работы ---
    address = models.CharField(_("Адрес"), max_length=500, blank=True)
    map_link = models.URLField(_("Ссылка на карту"), blank=True)
    work_hours = models.CharField(
        _("Часы работы"), max_length=255, blank=True, help_text=_("Например: Пн–Сб 9:00–18:00")
    )

    # --- Соцсети ---
    instagram_url = models.URLField(_("Instagram"), blank=True)
    telegram_channel_url = models.URLField(_("Telegram-канал"), blank=True)

    # --- Поведение витрины ---
    currency_label = models.CharField(_("Валюта"), max_length=32, default="сум")
    min_order_amount = models.DecimalField(
        _("Минимальная сумма заказа"),
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text=_("0 — без ограничения"),
    )
    order_message_header = models.CharField(
        _("Заголовок сообщения заказа"),
        max_length=255,
        default="Здравствуйте! Хочу заказать:",
        help_text=_("Первая строка сообщения, которое уходит в Telegram/WhatsApp"),
    )
    show_prices = models.BooleanField(
        _("Показывать цены"),
        default=True,
        help_text=_("Выключите, если цены только по запросу"),
    )

    class Meta:
        verbose_name = _("Настройки магазина")
        verbose_name_plural = _("Настройки магазина")

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Гарантируем единственность записи и сбрасываем кэш
        self.pk = 1
        super().save(*args, **kwargs)
        cache.delete(self.CACHE_KEY)

    def delete(self, *args, **kwargs):
        # Singleton нельзя удалить — просто игнорируем
        pass

    @classmethod
    def get_solo(cls):
        """Вернуть настройки, создав их при первом обращении. Кэшируется."""
        obj = cache.get(cls.CACHE_KEY)
        if obj is None:
            obj, _created = cls.objects.get_or_create(pk=1)
            cache.set(cls.CACHE_KEY, obj)
        return obj
