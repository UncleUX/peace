from django import template

register = template.Library()

@register.filter
def split(value, delimiter=','):
    """Split a string by delimiter"""
    if value:
        return value.split(delimiter)
    return []

@register.filter
def intcomma(value):
    """Format a number with commas as thousands separators"""
    try:
        value = int(value)
        return "{:,}".format(value)
    except (ValueError, TypeError):
        return value
