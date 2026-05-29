from django import template

register = template.Library()

@register.filter
def index(sequence, index):
    """Retourne l'élément à l'index spécifié"""
    try:
        return sequence[index]
    except (IndexError, TypeError):
        return None

@register.filter
def add(value, arg):
    """Additionne deux valeurs"""
    try:
        return int(value) + int(arg)
    except (ValueError, TypeError):
        return value

@register.filter
def mul(value, arg):
    """Multiplie deux valeurs"""
    try:
        return int(value) * int(arg)
    except (ValueError, TypeError):
        return value

@register.filter
def div(value, arg):
    """Divise deux valeurs"""
    try:
        return int(value) // int(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return value

@register.filter
def default(value, default_value):
    """Retourne la valeur par défaut si la valeur est None ou vide"""
    if value is None or value == '':
        return default_value
    return value
