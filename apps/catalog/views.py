"""Витрина: главная, каталог, карточка товара, поиск, контакты, корзина."""
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from .models import Category, Product

PER_PAGE = 24


def _active_products():
    # Активные товары с подгруженной категорией — без N+1 в списках
    return Product.objects.filter(is_active=True).select_related("category")


def home(request):
    """Главная: блок о магазине, категории, популярные товары."""
    context = {
        "categories": Category.objects.filter(is_active=True, parent__isnull=True),
        "featured": _active_products().filter(is_featured=True)[:8],
    }
    return render(request, "catalog/home.html", context)


def catalog(request):
    """Весь каталог с пагинацией и лентой категорий."""
    page = Paginator(_active_products(), PER_PAGE).get_page(request.GET.get("page"))
    context = {
        "categories": Category.objects.filter(is_active=True, parent__isnull=True),
        "page_obj": page,
        "title": "Каталог",
    }
    return render(request, "catalog/catalog.html", context)


def category(request, slug):
    """Товары одной категории (включая подкатегории)."""
    cat = get_object_or_404(Category, slug=slug, is_active=True)
    # Товары самой категории и её дочерних
    products = _active_products().filter(
        Q(category=cat) | Q(category__parent=cat)
    )
    page = Paginator(products, PER_PAGE).get_page(request.GET.get("page"))
    context = {
        "categories": Category.objects.filter(is_active=True, parent__isnull=True),
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
        results = _active_products().filter(
            Q(name__icontains=q) | Q(sku__icontains=q) | Q(description__icontains=q)
        )
    page = Paginator(results, PER_PAGE).get_page(request.GET.get("page"))
    return render(request, "catalog/search.html", {"q": q, "page_obj": page})


def contacts(request):
    """Контакты магазина (данные из настроек)."""
    return render(request, "catalog/contacts.html")


def cart(request):
    """Страница корзины. Логика — на Alpine/localStorage (детализация на этапе 5)."""
    return render(request, "catalog/cart.html")
