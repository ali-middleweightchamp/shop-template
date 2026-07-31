"""
Админка каталога. Рассчитана на продавца без технических навыков:
редактирование цен и наличия прямо в списке, массовые действия, превью фото.
"""
from django.contrib import admin
from django.contrib.auth.models import Group
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from easy_thumbnails.files import get_thumbnailer
from modeltranslation.admin import TranslationAdmin

from .models import Category, Product, ProductImage

# Прячем из админки лишнее, что продавцу не нужно
for _model in (Group,):
    try:
        admin.site.unregister(_model)
    except admin.sites.NotRegistered:
        pass

# Сайты (django.contrib.sites) — тоже не нужны продавцу в интерфейсе
try:
    from django.contrib.sites.models import Site

    admin.site.unregister(Site)
except (ImportError, admin.sites.NotRegistered):
    pass


def _thumb(image, size="thumb"):
    """Маленькое превью картинки для списка. Возвращает <img> или прочерк."""
    if not image:
        return format_html('<span style="color:#bbb">—</span>')
    try:
        url = get_thumbnailer(image)[size].url
    except Exception:
        # Если файл битый/отсутствует — не роняем список
        return format_html('<span style="color:#bbb">—</span>')
    return format_html(
        '<img src="{}" style="height:40px;width:40px;object-fit:cover;'
        'border-radius:6px;border:1px solid #eee">',
        url,
    )


class ProductImageInline(admin.TabularInline):
    """Дополнительные фото товара прямо на странице товара."""

    model = ProductImage
    extra = 1
    fields = ("preview", "image", "order")
    readonly_fields = ("preview",)

    @admin.display(description=_("Превью"))
    def preview(self, obj):
        return _thumb(obj.image)


@admin.register(Product)
class ProductAdmin(TranslationAdmin):
    list_display = (
        "image_preview",
        "name",
        "sku",
        "category",
        "price",
        "in_stock",
        "is_active",
        "order",
    )
    # Кликабельны для перехода в карточку — название и артикул
    list_display_links = ("name", "sku")
    # Массовое редактирование цен и наличия прямо в списке
    list_editable = ("price", "in_stock", "is_active", "order")
    list_filter = ("category", "in_stock", "is_active", "is_featured")
    search_fields = ("name_ru", "name_uz", "sku")
    list_per_page = 50
    inlines = [ProductImageInline]
    autocomplete_fields = ("category",)
    actions = ("mark_in_stock", "mark_out_of_stock", "hide_from_site", "show_on_site")

    fieldsets = (
        (None, {"fields": ("name", "slug", "sku", "category")}),
        (_("Цена и единица"), {"fields": ("price", "old_price", "unit", "pack_size")}),
        (_("Описание и фото"), {"fields": ("description", "image")}),
        (
            _("Отображение"),
            {"fields": ("in_stock", "is_active", "is_featured", "order")},
        ),
    )

    @admin.display(description=_("Фото"))
    def image_preview(self, obj):
        return _thumb(obj.image)

    # --- Массовые действия ---
    @admin.action(description=_("Отметить как «в наличии»"))
    def mark_in_stock(self, request, queryset):
        updated = queryset.update(in_stock=True)
        self.message_user(request, _("Отмечено в наличии: %(n)d") % {"n": updated})

    @admin.action(description=_("Снять с наличия"))
    def mark_out_of_stock(self, request, queryset):
        updated = queryset.update(in_stock=False)
        self.message_user(request, _("Снято с наличия: %(n)d") % {"n": updated})

    @admin.action(description=_("Скрыть с сайта"))
    def hide_from_site(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, _("Скрыто с сайта: %(n)d") % {"n": updated})

    @admin.action(description=_("Показать на сайте"))
    def show_on_site(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, _("Показано на сайте: %(n)d") % {"n": updated})


@admin.register(Category)
class CategoryAdmin(TranslationAdmin):
    list_display = ("image_preview", "name", "parent", "order", "is_active")
    list_display_links = ("name",)
    list_editable = ("order", "is_active")
    list_filter = ("is_active", "parent")
    search_fields = ("name_ru", "name_uz")

    @admin.display(description=_("Картинка"))
    def image_preview(self, obj):
        return _thumb(obj.image)
