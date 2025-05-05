from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    """Multiplies the arg and the value"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.simple_tag
def is_in_stock(product):
    """Check if a product is in stock"""
    return product.stock > 0