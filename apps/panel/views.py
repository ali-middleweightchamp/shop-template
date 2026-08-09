"""Кастомная панель продавца — свой UI поверх моделей каталога.

Доступ только для сотрудников (is_staff). Покупателей здесь нет вообще —
у них никакого входа не существует. Суперюзер (мы) заходит и сюда, и в /admin/.
"""
import json
from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Count, F
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.text import slugify
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from apps.catalog.models import Banner, Category, Product, ProductAttribute, ProductImage
from apps.importer import services
from apps.importer.models import ImportLog

from . import imaging
from .forms import BannerForm, CategoryForm, ProductForm, ShopSettingsForm

XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def panel_required(view):
    """Пускаем в панель только активных сотрудников."""
    check = user_passes_test(
        lambda u: u.is_active and u.is_staff, login_url="panel:login"
    )
    return check(view)


def _greeting():
    from django.utils.translation import gettext as _

    hour = timezone.localtime().hour
    if 5 <= hour < 12:
        return _("Доброе утро")
    if 12 <= hour < 18:
        return _("Добрый день")
    if 18 <= hour < 23:
        return _("Добрый вечер")
    return _("Доброй ночи")


@panel_required
def dashboard(request):
    """Обзор: четыре цифры, товары «нет в наличии» и предупреждение о залежавшихся."""
    products = Product.objects.all()
    total = products.count()
    out_qs = products.filter(in_stock=False)
    out_count = out_qs.count()
    # «Активные акции» = товары со скидкой (старая цена больше текущей)
    discounted = products.filter(old_price__gt=F("price")).count()
    # Висят «нет в наличии» дольше двух недель — их пора обновить или скрыть
    two_weeks_ago = timezone.now() - timedelta(days=14)
    stale_count = out_qs.filter(updated_at__lt=two_weeks_ago).count()

    context = {
        "section": "dashboard",
        "greeting": _greeting(),
        "today": timezone.localdate(),
        "total": total,
        "in_stock": total - out_count,
        "out_count": out_count,
        "cats_count": Category.objects.count(),
        "discounted": discounted,
        "stale_count": stale_count,
        "out_list": out_qs.select_related("category").order_by("updated_at")[:6],
        "last_import": ImportLog.objects.order_by("-created_at").first(),
    }
    return render(request, "panel/dashboard.html", context)


# ==================== Товары ====================

PER_PAGE = 30


@panel_required
@ensure_csrf_cookie
def products(request):
    """Список товаров: поиск, фильтры, инлайн-правка цены, массовые действия."""
    qs = Product.objects.select_related("category").order_by("order", "name")

    q = (request.GET.get("q") or "").strip()
    if q:
        qs = qs.filter(search_blob__contains=q.lower())

    cat = (request.GET.get("cat") or "").strip()
    if cat.isdigit():
        qs = qs.filter(category_id=int(cat))

    stock = (request.GET.get("stock") or "").strip()
    if stock == "in":
        qs = qs.filter(in_stock=True)
    elif stock == "out":
        qs = qs.filter(in_stock=False)
    elif stock == "sale":
        qs = qs.filter(old_price__gt=F("price"))

    total = Product.objects.count()
    discounted = Product.objects.filter(old_price__gt=F("price")).count()
    page = Paginator(qs, PER_PAGE).get_page(request.GET.get("page"))

    context = {
        "section": "products",
        "page_obj": page,
        "categories": Category.objects.order_by("order", "name"),
        "total": total,
        "discounted": discounted,
        "q": q,
        "cat": cat,
        "stock": stock,
    }
    return render(request, "panel/products.html", context)


def _json_body(request):
    try:
        return json.loads(request.body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return {}


@panel_required
@require_POST
def product_save_prices(request):
    """Массовое сохранение цен, отредактированных прямо в таблице."""
    data = _json_body(request)
    changes = data.get("changes") or {}
    saved = 0
    for pid, raw in changes.items():
        try:
            price = Decimal(str(raw))
        except (InvalidOperation, TypeError):
            continue
        if price < 0:
            continue
        if Product.objects.filter(pk=pid).update(price=price):
            saved += 1
    return JsonResponse({"ok": True, "saved": saved})


_TOGGLE_FIELDS = {"in_stock", "is_active", "is_featured", "is_new", "is_bestseller"}


@panel_required
@require_POST
def product_toggle(request):
    """Переключить один булев флаг товара (наличие/видимость/полки)."""
    data = _json_body(request)
    field = data.get("field")
    if field not in _TOGGLE_FIELDS:
        return JsonResponse({"error": "bad field"}, status=400)
    try:
        product = Product.objects.get(pk=data.get("id"))
    except Product.DoesNotExist:
        return JsonResponse({"error": "not found"}, status=404)
    value = not getattr(product, field)
    setattr(product, field, value)
    product.save(update_fields=[field, "updated_at"])
    return JsonResponse({"ok": True, "value": value})


@panel_required
@require_POST
def product_discount(request):
    """Задать скидку по проценту (старая цена = текущая / (1 − %)) или снять её."""
    data = _json_body(request)
    try:
        product = Product.objects.get(pk=data.get("id"))
    except Product.DoesNotExist:
        return JsonResponse({"error": "not found"}, status=404)

    if data.get("clear"):
        product.old_price = None
        product.save(update_fields=["old_price", "updated_at"])
        return JsonResponse({"ok": True, "old_price": None})

    try:
        percent = int(data.get("percent"))
    except (TypeError, ValueError):
        return JsonResponse({"error": "bad percent"}, status=400)
    if not (1 <= percent <= 90):
        return JsonResponse({"error": "percent 1..90"}, status=400)

    old = (product.price / (Decimal(100 - percent) / Decimal(100))).quantize(Decimal("1"))
    product.old_price = old
    product.save(update_fields=["old_price", "updated_at"])
    return JsonResponse({"ok": True, "old_price": int(old), "percent": product.discount_percent()})


@panel_required
@require_POST
def product_bulk(request):
    """Массовые действия по отмеченным товарам."""
    data = _json_body(request)
    ids = data.get("ids") or []
    action = data.get("action")
    qs = Product.objects.filter(pk__in=ids)
    if action == "in_stock":
        n = qs.update(in_stock=True)
    elif action == "out_stock":
        n = qs.update(in_stock=False)
    elif action == "hide":
        n = qs.update(is_active=False)
    elif action == "show":
        n = qs.update(is_active=True)
    elif action == "delete":
        n = qs.count()
        qs.delete()
    else:
        return JsonResponse({"error": "bad action"}, status=400)
    return JsonResponse({"ok": True, "count": n})


# ==================== Акции (скидки + полки) ====================


@panel_required
@ensure_csrf_cookie
def promotions(request):
    """Управление скидками и полками главной (Популярное / Хит продаж / Новинки)."""
    products = Product.objects.select_related("category").order_by("name")
    ctx = {
        "section": "promotions",
        "discounted": products.filter(old_price__gt=F("price")),
        "featured": products.filter(is_featured=True),
        "bestsellers": products.filter(is_bestseller=True),
        "new_products": products.filter(is_new=True),
        # для клиентского поиска при добавлении товара в полку/скидку
        "all_products": list(
            products.values("id", "name_ru", "sku", "is_featured", "is_bestseller", "is_new")
        ),
    }
    return render(request, "panel/promotions.html", ctx)


# ==================== Баннеры ====================

MAX_ACTIVE_BANNERS = 3


@panel_required
@ensure_csrf_cookie
def banners(request):
    from apps.shopsettings.models import ShopSettings

    items = Banner.objects.order_by("order", "id")
    return render(
        request,
        "panel/banners.html",
        {
            "section": "banners",
            "banners": items,
            "active_count": Banner.objects.filter(is_active=True).count(),
            "banners_enabled": ShopSettings.get_solo().banners_enabled,
            "max_active": MAX_ACTIVE_BANNERS,
        },
    )


@panel_required
def banner_edit(request, pk=None):
    instance = get_object_or_404(Banner, pk=pk) if pk else None
    if request.method == "POST":
        form = BannerForm(request.POST, instance=instance)
        img_error = None
        img_file = request.FILES.get("image")
        if img_file:
            try:
                imaging.validate_image(img_file, min_side=450)
            except ValidationError as e:
                img_error = e.messages[0]
        if form.is_valid() and not img_error:
            banner = form.save(commit=False)
            # Лимит 3 активных: нельзя включить четвёртый
            if banner.is_active:
                active = Banner.objects.filter(is_active=True)
                if instance:
                    active = active.exclude(pk=instance.pk)
                if active.count() >= MAX_ACTIVE_BANNERS:
                    banner.is_active = False
                    messages.error(request, f"Активных баннеров может быть максимум {MAX_ACTIVE_BANNERS}. Слайд сохранён выключенным.")
            if img_file:
                # Готовый баннер не кропим — показываем целиком, какие пропорции залили.
                banner.image = imaging.process_image(img_file, ratio=None, width=1600, name="banner")
            banner.save()
            return redirect("panel:banners")
    else:
        form = BannerForm(instance=instance)
        img_error = None
    return render(
        request,
        "panel/banner_form.html",
        {"section": "banners", "form": form, "instance": instance, "img_error": img_error},
    )


@panel_required
@require_POST
def banner_delete(request, pk):
    Banner.objects.filter(pk=pk).delete()
    return redirect("panel:banners")


@panel_required
@require_POST
def banner_toggle(request):
    data = _json_body(request)
    banner = Banner.objects.filter(pk=data.get("id")).first()
    if not banner:
        return JsonResponse({"error": "not found"}, status=404)
    if not banner.is_active:
        # включаем — проверяем лимит
        if Banner.objects.filter(is_active=True).count() >= MAX_ACTIVE_BANNERS:
            return JsonResponse({"error": "limit", "max": MAX_ACTIVE_BANNERS}, status=400)
    banner.is_active = not banner.is_active
    banner.save(update_fields=["is_active"])
    return JsonResponse({"ok": True, "value": banner.is_active})


@panel_required
@require_POST
def banner_reorder(request):
    ids = _json_body(request).get("ids") or []
    for i, bid in enumerate(ids):
        Banner.objects.filter(pk=bid).update(order=i)
    return JsonResponse({"ok": True})


# ==================== Настройки ====================


@panel_required
def settings_view(request):
    """Настройки магазина + живое превью шапки."""
    from apps.shopsettings.models import ShopSettings

    shop_obj = ShopSettings.get_solo()
    if request.method == "POST":
        form = ShopSettingsForm(request.POST, request.FILES, instance=shop_obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Настройки сохранены.")
            return redirect("panel:settings")
    else:
        form = ShopSettingsForm(instance=shop_obj)
    return render(request, "panel/settings.html", {"section": "settings", "form": form})


# ==================== Прайс-лист ====================


@panel_required
def price(request):
    """Импорт Excel: загрузка → предпросмотр (создастся/обновится/ошибки) → применить."""
    preview = None

    # Шаг 2: применить ранее загруженный файл по log_id
    if request.method == "POST" and request.POST.get("apply") and request.POST.get("log_id"):
        log = ImportLog.objects.filter(pk=request.POST["log_id"]).first()
        if log:
            log.file.open("rb")
            try:
                result = services.apply(log.file)
            finally:
                log.file.close()
            if result.get("missing_columns"):
                log.status = ImportLog.Status.FAILED
                log.save(update_fields=["status"])
                messages.error(request, "Не хватает колонок: " + ", ".join(result["missing_columns"]))
            else:
                log.rows_total = result.get("rows_total", 0)
                log.rows_created = result.get("rows_created", 0)
                log.rows_updated = result.get("rows_updated", 0)
                log.rows_failed = len(result.get("errors", []))
                log.errors = result.get("errors", [])
                log.status = ImportLog.Status.SUCCESS
                log.save()
                messages.success(
                    request,
                    f"Прайс применён: создано {log.rows_created}, обновлено {log.rows_updated}, "
                    f"ошибок {log.rows_failed}.",
                )
        return redirect("panel:price")

    # Шаг 1: загрузка → предпросмотр (без записи в БД)
    if request.method == "POST" and request.FILES.get("file"):
        log = ImportLog.objects.create(
            file=request.FILES["file"], user=request.user, status=ImportLog.Status.PREVIEW
        )
        log.file.open("rb")
        try:
            preview = services.analyze(log.file)
        finally:
            log.file.close()
        preview["log_id"] = log.pk
        preview["filename"] = log.file.name.rsplit("/", 1)[-1]
        log.rows_total = preview["rows_total"]
        log.rows_failed = len(preview["errors"])
        log.errors = preview["errors"]
        log.save()

    return render(
        request,
        "panel/price.html",
        {"section": "price", "preview": preview, "history": ImportLog.objects.all()[:12]},
    )


@panel_required
def price_template(request):
    resp = HttpResponse(services.build_template(), content_type=XLSX)
    resp["Content-Disposition"] = 'attachment; filename="price-template.xlsx"'
    return resp


@panel_required
def price_export(request):
    resp = HttpResponse(services.export_catalog(), content_type=XLSX)
    resp["Content-Disposition"] = 'attachment; filename="catalog.xlsx"'
    return resp


# ==================== Заглушки будущих разделов ====================

_STUB_TITLES = {
    "settings": "Настройки",
}


@panel_required
def styleguide(request):
    """Витрина компонентов (только staff): проверить новую тему за минуту."""
    return render(request, "panel/styleguide.html", {})


@panel_required
def stub(request, section):
    return render(
        request,
        "panel/stub.html",
        {"section": section, "title": _STUB_TITLES.get(section, "Раздел")},
    )


@panel_required
def product_edit(request, pk=None):
    """Создание/редактирование карточки товара (блоки, ru/uz, фото, характеристики)."""
    instance = get_object_or_404(Product, pk=pk) if pk else None

    if request.method == "POST":
        form = ProductForm(request.POST, instance=instance)
        img_error = None
        main_file = request.FILES.get("image")
        if main_file:
            try:
                imaging.validate_image(main_file, min_side=600)
            except ValidationError as e:
                img_error = e.messages[0]

        if form.is_valid() and not img_error:
            product = form.save(commit=False)
            if main_file:
                # центр-кроп в квадрат, WebP; оригинал не храним
                product.image = imaging.process_image(
                    main_file, ratio=(1, 1), width=1000, name=(product.sku or "product")
                )
            product.save()

            # Галерея: удаление отмеченных и обновление порядка
            for im in list(product.images.all()):
                if request.POST.get(f"img_delete_{im.id}"):
                    im.delete()
                    continue
                try:
                    im.order = int(request.POST.get(f"img_order_{im.id}", im.order))
                    im.save(update_fields=["order"])
                except (TypeError, ValueError):
                    pass

            # Галерея: новые изображения
            base = product.images.count()
            for i, gf in enumerate(request.FILES.getlist("gallery")):
                try:
                    imaging.validate_image(gf, min_side=600)
                except ValidationError:
                    continue
                cf = imaging.process_image(gf, ratio=(1, 1), width=1000, name=f"{product.sku}-{base + i}")
                ProductImage.objects.create(product=product, image=cf, order=base + i)

            # Характеристики: пересобираем из строк формы
            names = request.POST.getlist("attr_name")
            values = request.POST.getlist("attr_value")
            product.attributes.all().delete()
            order = 0
            for n, v in zip(names, values):
                n, v = n.strip(), v.strip()
                if n and v:
                    ProductAttribute.objects.create(product=product, name=n, value=v, order=order)
                    order += 1

            return redirect("panel:products")
    else:
        form = ProductForm(instance=instance)
        img_error = None

    return render(
        request,
        "panel/product_form.html",
        {"section": "products", "form": form, "instance": instance, "img_error": img_error},
    )


@panel_required
@require_POST
def product_delete(request, pk):
    Product.objects.filter(pk=pk).delete()
    return redirect("panel:products")


# ==================== Категории ====================


@panel_required
@ensure_csrf_cookie
def categories(request):
    """Список категорий: число товаров + ручная сортировка перетаскиванием."""
    cats = Category.objects.annotate(num=Count("products")).order_by("order", "name")
    return render(request, "panel/categories.html", {"section": "categories", "categories": cats})


@panel_required
def category_edit(request, pk=None):
    instance = get_object_or_404(Category, pk=pk) if pk else None
    if request.method == "POST":
        form = CategoryForm(request.POST, instance=instance)
        img_error = None
        img_file = request.FILES.get("image")
        if img_file:
            try:
                imaging.validate_image(img_file, min_side=400)
            except ValidationError as e:
                img_error = e.messages[0]
        if form.is_valid() and not img_error:
            cat = form.save(commit=False)
            if img_file:
                cat.image = imaging.process_image(
                    img_file, ratio=(4, 3), width=800, name=(slugify(cat.name) or "category")
                )
            try:
                cat.full_clean(exclude=["slug", "image"])
            except ValidationError as e:
                for msgs in e.message_dict.values():
                    form.add_error(None, msgs[0])
            else:
                cat.save()
                return redirect("panel:categories")
    else:
        form = CategoryForm(instance=instance)
        img_error = None
    return render(
        request,
        "panel/category_form.html",
        {"section": "categories", "form": form, "instance": instance, "img_error": img_error},
    )


@panel_required
@require_POST
def category_delete(request, pk):
    cat = get_object_or_404(Category, pk=pk)
    # Категорию с товарами не удаляем — сначала перенесите товары в другую
    if not cat.products.exists():
        cat.delete()
    return redirect("panel:categories")


@panel_required
@require_POST
def category_reorder(request):
    """Сохранить порядок категорий после перетаскивания."""
    ids = _json_body(request).get("ids") or []
    for i, cid in enumerate(ids):
        Category.objects.filter(pk=cid).update(order=i)
    return JsonResponse({"ok": True})
