from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Récupère une valeur dans un dictionnaire avec une clé"""
    try:
        return dictionary.get(key, None)
    except (AttributeError, KeyError):
        return None
