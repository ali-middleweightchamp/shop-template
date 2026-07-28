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
