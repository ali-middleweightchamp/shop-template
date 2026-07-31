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
