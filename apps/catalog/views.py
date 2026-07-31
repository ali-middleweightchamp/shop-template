"""Витрина: главная, каталог, карточка товара, поиск, контакты, корзина."""
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext_lazy as _

from .models import Category, Product

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
