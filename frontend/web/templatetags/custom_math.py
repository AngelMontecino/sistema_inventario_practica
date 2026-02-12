from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def multiply(value, arg):
    try:
        return Decimal(str(value)) * Decimal(str(arg))
    except (ValueError, TypeError):
        return 0
@register.filter
def calculate_discounted_total(value, discount_percent):
    try:
        val = Decimal(str(value))
        disc = Decimal(str(discount_percent))
        factor = (Decimal(100) - disc) / Decimal(100)
        return val * factor
    except (ValueError, TypeError):
        return value
