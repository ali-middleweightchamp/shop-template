"""Шаблонные фильтры каталога."""
from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()


@register.filter
def money(value):
    """Формат суммы с пробелом-разделителем тысяч: 12500 → «12 500».
    Дробную часть отбрасываем (в сумах копейки не используются)."""
    try:
        number = int(Decimal(value))
    except (TypeError, ValueError, InvalidOperation):
        return value
    return f"{number:,}".replace(",", " ")
