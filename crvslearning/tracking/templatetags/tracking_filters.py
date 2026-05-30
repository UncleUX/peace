from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    """Multiplie la valeur par l'argument"""
    try:
        return int(value) * int(arg)
    except (ValueError, TypeError):
        return 0

@register.filter(name='get_item')
def get_item(dictionary, key):
    """
    Get a value from a dictionary using a key in templates
    Usage: {{ my_dict|get_item:my_key }}
    """
    if not dictionary:
        return ""
    return dictionary.get(key, "")

@register.filter(name='get_completion_color')
def get_completion_color(percentage):
    """
    Retourne une classe de couleur Bootstrap en fonction du pourcentage de complétion
    """
    if not percentage:
        return 'secondary'
    
    percentage = float(percentage)
    
    if percentage < 25:
        return 'danger'
    elif 25 <= percentage < 50:
        return 'warning'
    elif 50 <= percentage < 75:
        return 'info'
    else:
        return 'success'
