"""Формы панели продавца."""
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.catalog.models import Banner, Category, Product
from apps.shopsettings.models import ShopSettings


class StaffAuthenticationForm(AuthenticationForm):
    """Вход в панель разрешён только сотрудникам (staff), не покупателям."""

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not user.is_staff:
            raise ValidationError(
                _("У этой учётной записи нет доступа в панель."), code="no_staff"
            )


class ProductForm(forms.ModelForm):
    """Карточка товара: поля ru/uz рядом. Фото обрабатывается отдельно во вью."""

    class Meta:
        model = Product
        fields = [
            "name_ru", "name_uz", "sku", "category", "unit", "pack_size",
            "price", "old_price",
            "description_ru", "description_uz",
            "in_stock", "is_active", "is_featured", "is_new", "is_bestseller",
        ]
        widgets = {
            "description_ru": forms.Textarea(attrs={"rows": 4}),
            "description_uz": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # name_ru обязателен, name_uz — нет (есть фолбэк uz→ru)
        self.fields["name_ru"].required = True
        self.fields["name_uz"].required = False
        self.fields["pack_size"].required = False
        self.fields["old_price"].required = False
        # Артикул можно не указывать — сгенерируется автоматически при сохранении
        self.fields["sku"].required = False
        # единый вид полей
        for name, field in self.fields.items():
            if isinstance(field.widget, (forms.CheckboxInput,)):
                continue
            css = "pfield"
            if isinstance(field.widget, forms.Textarea):
                css = "pfield"
            field.widget.attrs["class"] = css

    def clean(self):
        cleaned = super().clean()
        price = cleaned.get("price")
        old = cleaned.get("old_price")
        if old and price and old <= price:
            self.add_error("old_price", _("Старая цена должна быть больше текущей."))
        return cleaned


class CategoryForm(forms.ModelForm):
    """Категория: ru/uz, родитель (вложенность до 2 уровней), картинка отдельно."""

    class Meta:
        model = Category
        fields = ["name_ru", "name_uz", "parent", "is_active"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name_ru"].required = True
        self.fields["name_uz"].required = False
        self.fields["parent"].required = False
        # Родителем может быть только категория верхнего уровня (макс. 2 уровня),
        # и нельзя выбрать саму себя.
        qs = Category.objects.filter(parent__isnull=True)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        self.fields["parent"].queryset = qs
        for name, field in self.fields.items():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = "pfield"


class ShopSettingsForm(forms.ModelForm):
    """Настройки магазина: двуязычные поля рядом + брендинг/контакты/витрина."""

    class Meta:
        model = ShopSettings
        fields = [
            # Бренд
            "name_ru", "name_uz", "logo",
            "tagline_ru", "tagline_uz",
            "description_ru", "description_uz",
            # Оформление
            "theme", "primary_color",
            # Контакты
            "telegram_username", "whatsapp_phone", "phone", "phone_secondary",
            # Адрес и время
            "address_ru", "address_uz", "map_link",
            "work_hours_ru", "work_hours_uz",
            # Соцсети
            "instagram_url", "telegram_channel_url",
            # Витрина
            "currency_label_ru", "currency_label_uz",
            "min_order_amount", "show_prices", "banners_enabled", "banner_format",
            "order_message_header_ru", "order_message_header_uz",
            "order_message_footer_ru", "order_message_footer_uz",
            # Инфо-полоса сверху
            "topbar_enabled", "topbar_location_ru", "topbar_location_uz",
            "delivery_note_ru", "delivery_note_uz",
            # Плавающая кнопка Telegram
            "telegram_float_enabled",
            # Блок «О нас»
            "about_enabled", "about_title_ru", "about_title_uz",
            "about_text_ru", "about_text_uz", "about_image",
            # Плашки доверия
            "trust_enabled",
            "trust1_icon", "trust1_text_ru", "trust1_text_uz",
            "trust2_icon", "trust2_text_ru", "trust2_text_uz",
            "trust3_icon", "trust3_text_ru", "trust3_text_uz",
            "trust4_icon", "trust4_text_ru", "trust4_text_uz",
            # Как заказать
            "howto_enabled",
            # FAQ
            "faq_enabled",
            "faq1_q_ru", "faq1_q_uz", "faq1_a_ru", "faq1_a_uz",
            "faq2_q_ru", "faq2_q_uz", "faq2_a_ru", "faq2_a_uz",
            "faq3_q_ru", "faq3_q_uz", "faq3_a_ru", "faq3_a_uz",
            "faq4_q_ru", "faq4_q_uz", "faq4_a_ru", "faq4_a_uz",
            "faq5_q_ru", "faq5_q_uz", "faq5_a_ru", "faq5_a_uz",
        ]
        widgets = {
            "description_ru": forms.Textarea(attrs={"rows": 3}),
            "description_uz": forms.Textarea(attrs={"rows": 3}),
            "about_text_ru": forms.Textarea(attrs={"rows": 3}),
            "about_text_uz": forms.Textarea(attrs={"rows": 3}),
            "primary_color": forms.TextInput(attrs={"placeholder": "необязательно, напр. #2563EB"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name_ru"].required = True
        # Ответы FAQ — многострочные
        for i in range(1, 6):
            for lang in ("ru", "uz"):
                fn = f"faq{i}_a_{lang}"
                if fn in self.fields:
                    self.fields[fn].widget = forms.Textarea(attrs={"rows": 2})
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                continue
            if name != "name_ru":
                field.required = False
            field.widget.attrs["class"] = "pfield"


class BannerForm(forms.ModelForm):
    """Слайд hero-баннера: заголовок/подзаголовок/плашка/кнопка ru/uz. Фон — отдельно."""

    class Meta:
        model = Banner
        fields = [
            "title_ru", "title_uz",
            "subtitle_ru", "subtitle_uz",
            "badge_ru", "badge_uz",
            "button_text_ru", "button_text_uz", "button_link",
            "is_active", "start_at", "end_at",
        ]
        widgets = {
            "start_at": forms.DateInput(attrs={"type": "date"}),
            "end_at": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Всё необязательно: баннер может быть просто картинкой без текста.
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                continue
            field.required = False
            field.widget.attrs["class"] = "pfield"
