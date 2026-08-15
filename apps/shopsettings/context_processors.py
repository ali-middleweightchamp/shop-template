"""
Context processor: во всех шаблонах доступна переменная `shop` с настройками
магазина. На этапе каркаса модели ещё нет — возвращаем безопасный заглушечный
объект, чтобы проект запускался. На этапе 2 здесь появится кэшируемый singleton.
"""


class _FallbackShop:
    """Заглушка на случай, если настройки ещё не созданы (пустая БД, первый запуск)."""

    name = "Магазин"
    currency_label = "сум"
    show_prices = True
    primary_color = "#2563eb"

    def __getattr__(self, item):
        # Любое неизвестное поле — пустая строка, чтобы шаблоны не падали
        return ""


def shop_settings(request):
    try:
        from .models import ShopSettings

        shop = ShopSettings.get_solo()
    except Exception:
        # Модели/таблицы ещё нет (каркас, непримигрированная БД)
        shop = _FallbackShop()
    return {"shop": shop}


def catalog_menu(request):
    """Дерево категорий для мега-меню «Каталог» в шапке.

    Кэшируем сами ORM-объекты: modeltranslation отдаёт `name` под текущий язык
    при обращении, поэтому один кэш безопасен для ru и uz. TTL короткий —
    правки категорий подхватятся быстро (панель к тому же чистит ключ явно).
    """
    from django.core.cache import cache
    from django.db.models import Prefetch

    key = "catalog_menu_v1"
    tops = cache.get(key)
    if tops is None:
        try:
            from apps.catalog.models import Category

            tops = list(
                Category.objects.filter(parent__isnull=True, is_active=True)
                .prefetch_related(
                    Prefetch("children", queryset=Category.objects.filter(is_active=True))
                )
                .order_by("order", "name")
            )
            cache.set(key, tops, 60)
        except Exception:
            tops = []
    return {"catalog_menu": tops}


def asset_version(request):
    """Версия для сброса кэша CSS/JS в dev (в проде статика и так хэшируется)."""
    import os

    from django.conf import settings

    path = settings.BASE_DIR / "static" / "dist" / "css" / "app.css"
    try:
        return {"asset_version": int(os.path.getmtime(path))}
    except OSError:
        return {"asset_version": 0}


def language_links(request):
    """URL текущей страницы на каждом языке для переключателя.

    Считаем здесь, а не в set_language: во время рендера страницы активен её
    язык, поэтому translate_url корректно резолвит путь (в т.ч. снимает/добавляет
    префикс /uz/). Переключатель — обычные ссылки, надёжно в обе стороны.
    """
    from django.conf import settings
    from django.urls import translate_url

    qs = request.META.get("QUERY_STRING", "")
    links = {}
    for code, _label in settings.LANGUAGES:
        try:
            url = translate_url(request.path, code)
        except Exception:
            url = "/"
        links[code] = f"{url}?{qs}" if qs else url
    return {"lang_urls": links}
