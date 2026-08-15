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

    class Theme(models.TextChoices):
        NOIR = "noir", _("Noir (чёрная, по умолчанию)")
        EMERALD = "emerald", _("Emerald (зелёная)")
        OCEAN = "ocean", _("Ocean (синяя)")
        VIOLET = "violet", _("Violet (фиолетовая)")
        ROSE = "rose", _("Rose (розовая)")
        SUNSET = "sunset", _("Sunset (тёплая, с засечками)")
        # Новый пресет = блок в themes.css + строка здесь, без переделки логики

    # --- Бренд ---
    name = models.CharField(_("Название магазина"), max_length=255, default="Магазин")
    logo = models.ImageField(_("Логотип"), upload_to="shop/", blank=True)
    tagline = models.CharField(
        _("Слоган на главной"), max_length=120, blank=True,
        help_text=_("Крупный заголовок в шапке главной. Пусто — покажем название."),
    )
    description = models.TextField(_("Описание"), blank=True)
    theme = models.CharField(
        _("Тема оформления"),
        max_length=32,
        choices=Theme.choices,
        default=Theme.NOIR,
        help_text=_("Цветовой пресет витрины (светлая/тёмная переключаются на сайте)"),
    )
    primary_color = models.CharField(
        _("Фирменный цвет"),
        max_length=7,
        blank=True,
        validators=[hex_color_validator],
        help_text=_("HEX, например #0F7B5F. Если заполнен — перебивает акцент темы. Пусто — цвет из темы."),
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
    order_message_footer = models.CharField(
        _("Подпись сообщения заказа"),
        max_length=255,
        blank=True,
        default="",
        help_text=_("Необязательная последняя строка. Например: «Укажите адрес доставки»"),
    )
    show_prices = models.BooleanField(
        _("Показывать цены"),
        default=True,
        help_text=_("Выключите, если цены только по запросу"),
    )
    banners_enabled = models.BooleanField(
        _("Показывать баннеры на главной"),
        default=False,
        help_text=_("Hero-слайдер вверху главной. По умолчанию выключен."),
    )

    class BannerFormat(models.TextChoices):
        STRIP = "strip", _("Полоса (4:1) — самый низкий")
        WIDE = "wide", _("Широкий (3:1)")
        CLASSIC = "classic", _("Классический (12:5)")
        HALF = "half", _("Средний (2:1)")
        MOBILE = "mobile", _("Высокий (16:9)")

    banner_format = models.CharField(
        _("Формат баннеров"),
        max_length=16,
        choices=BannerFormat.choices,
        default=BannerFormat.WIDE,
        help_text=_("Единый размер всех баннеров. Делайте картинки под эту пропорцию — без обрезки. Чем шире формат, тем ниже баннер."),
    )

    # Пропорции под каждый формат: для кропа при загрузке и для CSS aspect-ratio.
    _BANNER_RATIOS = {"strip": (4, 1), "wide": (3, 1), "classic": (12, 5), "half": (2, 1), "mobile": (16, 9)}

    @property
    def banner_ratio(self):
        """Кортеж (w, h) для обрезки изображения баннера."""
        return self._BANNER_RATIOS.get(self.banner_format, (3, 1))

    @property
    def banner_aspect_css(self):
        """Строка для CSS aspect-ratio, напр. '3 / 1'."""
        w, h = self.banner_ratio
        return f"{w} / {h}"

    # --- Верхняя инфо-полоса (top bar) над шапкой ---
    topbar_enabled = models.BooleanField(
        _("Показывать инфо-полосу сверху"),
        default=False,
        help_text=_("Тонкая полоса над шапкой: город, доставка, часы, телефон."),
    )
    topbar_location = models.CharField(
        _("Город/локация в полосе"),
        max_length=80,
        blank=True,
        default="",
        help_text=_("Например: Ташкент. Кликается на карту, если задана ссылка на карту."),
    )
    delivery_note = models.CharField(
        _("Доставка (текст в полосе)"),
        max_length=120,
        blank=True,
        default="",
        help_text=_("Например: Доставка по городу от 1 дня"),
    )

    # --- Плавающая кнопка заказа в Telegram ---
    telegram_float_enabled = models.BooleanField(
        _("Плавающая кнопка Telegram"),
        default=False,
        help_text=_("Круглая кнопка в углу экрана — быстрый заказ. Нужен заполненный Telegram продавца."),
    )

    # --- Блок «О нас» на главной ---
    about_enabled = models.BooleanField(_("Показывать блок «О нас»"), default=False)
    about_title = models.CharField(_("Заголовок «О нас»"), max_length=120, blank=True, default="")
    about_text = models.TextField(_("Текст «О нас»"), blank=True, default="")
    about_image = models.ImageField(_("Фото для «О нас»"), upload_to="shop/", blank=True)

    # --- Доверительные плашки (trust badges) ---
    trust_enabled = models.BooleanField(_("Показывать плашки доверия"), default=False)

    class TrustIcon(models.TextChoices):
        TAG = "tag", _("Ценник (опт/розница)")
        TRUCK = "truck", _("Грузовик (доставка)")
        USERS = "users", _("Клиенты")
        CALENDAR = "calendar", _("Календарь (с какого года)")
        BOX = "box", _("Коробка (наличие на складе)")
        SHIELD = "shield", _("Щит (гарантия/качество)")
        CLOCK = "clock", _("Часы работы")
        PERCENT = "percent", _("Скидки")
        STAR = "star", _("Звезда (качество)")
        WALLET = "wallet", _("Кошелёк (цены)")

    # Четыре фиксированных слота — просто и без отдельного CRUD.
    trust1_icon = models.CharField(_("Плашка 1 · иконка"), max_length=16, choices=TrustIcon.choices, default=TrustIcon.TAG, blank=True)
    trust1_text = models.CharField(_("Плашка 1 · текст"), max_length=60, blank=True, default="")
    trust2_icon = models.CharField(_("Плашка 2 · иконка"), max_length=16, choices=TrustIcon.choices, default=TrustIcon.TRUCK, blank=True)
    trust2_text = models.CharField(_("Плашка 2 · текст"), max_length=60, blank=True, default="")
    trust3_icon = models.CharField(_("Плашка 3 · иконка"), max_length=16, choices=TrustIcon.choices, default=TrustIcon.USERS, blank=True)
    trust3_text = models.CharField(_("Плашка 3 · текст"), max_length=60, blank=True, default="")
    trust4_icon = models.CharField(_("Плашка 4 · иконка"), max_length=16, choices=TrustIcon.choices, default=TrustIcon.BOX, blank=True)
    trust4_text = models.CharField(_("Плашка 4 · текст"), max_length=60, blank=True, default="")

    @property
    def trust_badges(self):
        """Список заполненных плашек: [{icon, text}, …]. Пустые слоты пропускаем."""
        out = []
        for i in (1, 2, 3, 4):
            text = getattr(self, f"trust{i}_text", "")
            if text:
                out.append({"icon": getattr(self, f"trust{i}_icon", ""), "text": text})
        return out

    # --- Блок «Как заказать» (3 шага, универсальный флоу шаблона) ---
    howto_enabled = models.BooleanField(_("Показывать блок «Как заказать»"), default=False)

    # --- FAQ (часто задаваемые вопросы) ---
    faq_enabled = models.BooleanField(_("Показывать FAQ"), default=False)
    faq1_q = models.CharField(_("Вопрос 1"), max_length=200, blank=True, default="")
    faq1_a = models.TextField(_("Ответ 1"), blank=True, default="")
    faq2_q = models.CharField(_("Вопрос 2"), max_length=200, blank=True, default="")
    faq2_a = models.TextField(_("Ответ 2"), blank=True, default="")
    faq3_q = models.CharField(_("Вопрос 3"), max_length=200, blank=True, default="")
    faq3_a = models.TextField(_("Ответ 3"), blank=True, default="")
    faq4_q = models.CharField(_("Вопрос 4"), max_length=200, blank=True, default="")
    faq4_a = models.TextField(_("Ответ 4"), blank=True, default="")
    faq5_q = models.CharField(_("Вопрос 5"), max_length=200, blank=True, default="")
    faq5_a = models.TextField(_("Ответ 5"), blank=True, default="")

    @property
    def faq_items(self):
        """Заполненные пары вопрос-ответ: [{q, a}, …]."""
        out = []
        for i in (1, 2, 3, 4, 5):
            q = getattr(self, f"faq{i}_q", "")
            a = getattr(self, f"faq{i}_a", "")
            if q and a:
                out.append({"q": q, "a": a})
        return out

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

    # Короткий TTL: сохранение сбрасывает кэш в своём воркере мгновенно,
    # между воркерами (LocMemCache у каждого свой) устаревание — не дольше TTL.
    CACHE_TTL = 60

    @classmethod
    def get_solo(cls):
        """Вернуть настройки, создав их при первом обращении. Кэшируется."""
        obj = cache.get(cls.CACHE_KEY)
        if obj is None:
            obj, _created = cls.objects.get_or_create(pk=1)
            cache.set(cls.CACHE_KEY, obj, cls.CACHE_TTL)
        return obj
