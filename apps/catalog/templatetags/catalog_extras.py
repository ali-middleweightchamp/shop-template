"""Шаблонные фильтры каталога."""
from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()


@register.simple_tag
def elided_pages(page_obj, on_each_side=1, on_ends=1):
    """Номера страниц с многоточиями: 1 … 4 5 6 … 20. Возвращает список,
    где многоточие — строка Paginator.ELLIPSIS ('…')."""
    paginator = page_obj.paginator
    try:
        return list(
            paginator.get_elided_page_range(
                page_obj.number, on_each_side=on_each_side, on_ends=on_ends
            )
        )
    except Exception:
        return list(paginator.page_range)


@register.filter
def money(value):
    """Формат суммы с пробелом-разделителем тысяч: 12500 → «12 500».
    Дробную часть отбрасываем (в сумах копейки не используются)."""
    try:
        number = int(Decimal(value))
    except (TypeError, ValueError, InvalidOperation):
        return value
    return f"{number:,}".replace(",", " ")
