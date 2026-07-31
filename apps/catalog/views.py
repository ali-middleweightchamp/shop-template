"""Витрина: главная, каталог, карточка товара, поиск, контакты, корзина."""
import json

from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from .models import Category, Product, ShortOrder

PER_PAGE = 24


def _active_products():
    # Активные товары с подгруженной категорией — без N+1 в списках
    return Product.objects.filter(is_active=True).select_related("category")


def _sidebar_categories():
    # Категории верхнего уровня с числом активных товаров у каждой
    return (
        Category.objects.filter(is_active=True, parent__isnull=True)
        .annotate(num=Count("products", filter=Q(products__is_active=True), distinct=True))
        .order_by("order", "name")
    )


def home(request):
    """Главная: блок о магазине, категории, популярные товары."""
    context = {
        "categories": _sidebar_categories(),
        "featured": _active_products().filter(is_featured=True)[:8],
    }
    return render(request, "catalog/home.html", context)


def catalog(request):
    """Весь каталог с пагинацией и сайдбаром категорий."""
    products = _active_products()
    page = Paginator(products, PER_PAGE).get_page(request.GET.get("page"))
    context = {
        "categories": _sidebar_categories(),
        "total_count": products.count(),
        "page_obj": page,
        "title": _("Каталог"),
    }
    return render(request, "catalog/catalog.html", context)


def category(request, slug):
    """Товары одной категории (включая подкатегории). Тот же шаблон, что и каталог."""
    cat = get_object_or_404(Category, slug=slug, is_active=True)
    # Товары самой категории и её дочерних
    products = _active_products().filter(Q(category=cat) | Q(category__parent=cat))
    page = Paginator(products, PER_PAGE).get_page(request.GET.get("page"))
    context = {
        "categories": _sidebar_categories(),
        "total_count": _active_products().count(),
        "current_category": cat,
        "page_obj": page,
        "title": cat.name,
    }
    return render(request, "catalog/catalog.html", context)


def product_detail(request, slug):
    """Карточка товара: галерея, описание, похожие товары."""
    product = get_object_or_404(
        _active_products().prefetch_related("images"), slug=slug
    )
    related = (
        _active_products()
        .filter(category=product.category)
        .exclude(pk=product.pk)[:4]
    )
    return render(
        request,
        "catalog/product.html",
        {"product": product, "related": related},
    )


def search(request):
    """Поиск по названию, артикулу и описанию (регистронезависимый)."""
    q = (request.GET.get("q") or "").strip()
    results = _active_products().none()
    if q:
        # Ищем по обоим языкам названия/описания и по артикулу
        results = _active_products().filter(
            Q(name_ru__icontains=q)
            | Q(name_uz__icontains=q)
            | Q(sku__icontains=q)
            | Q(description_ru__icontains=q)
            | Q(description_uz__icontains=q)
        )
    page = Paginator(results, PER_PAGE).get_page(request.GET.get("page"))
    return render(request, "catalog/search.html", {"q": q, "page_obj": page})


def contacts(request):
    """Контакты магазина (данные из настроек)."""
    return render(request, "catalog/contacts.html")


from django.views.decorators.csrf import ensure_csrf_cookie  # noqa: E402


@ensure_csrf_cookie
def cart(request):
    """Страница корзины. Логика — на Alpine/localStorage.
    ensure_csrf_cookie — чтобы fetch на /order/create/ мог отправить CSRF-токен."""
    return render(request, "catalog/cart.html")


# Лимит длины закодированного текста для deep-link. Свыше — сохраняем заказ и
# отправляем сокращённый вариант со ссылкой.
ORDER_TEXT_LIMIT = 1500


@require_POST
def order_create(request):
    """Сохраняет состав длинного заказа, возвращает код и ссылку."""
    try:
        data = json.loads(request.body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({"error": "bad json"}, status=400)

    lines = data.get("lines")
    if not isinstance(lines, list) or not lines:
        return JsonResponse({"error": "empty"}, status=400)

    # Сохраняем только нужные поля — не доверяем клиенту лишнее
    payload = {
        "header": str(data.get("header", ""))[:255],
        "currency": str(data.get("currency", ""))[:32],
        "comment": str(data.get("comment", ""))[:1000],
        "total": data.get("total", 0),
        "lines": [
            {
                "sku": str(li.get("sku", ""))[:64],
                "name": str(li.get("name", ""))[:255],
                "qty": li.get("qty", 0),
                "unit": str(li.get("unit", ""))[:16],
                "price": li.get("price", 0),
            }
            for li in lines[:500]
        ],
    }
    order = ShortOrder.objects.create(payload=payload)
    return JsonResponse({"code": order.code, "url": order.get_absolute_url()})


def order_detail(request, code):
    """Публичная страница полного состава заказа по коду."""
    order = get_object_or_404(ShortOrder, code=code)
    payload = order.payload or {}
    lines = []
    for li in payload.get("lines", []):
        item = dict(li)
        try:
            item["sum"] = float(li.get("qty", 0)) * float(li.get("price", 0))
        except (TypeError, ValueError):
            item["sum"] = 0
        lines.append(item)
    return render(
        request, "catalog/order.html", {"order": order, "p": payload, "lines": lines}
    )
