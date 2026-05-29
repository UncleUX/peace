from django import template
from ..models import Category

register = template.Library()

@register.simple_tag
def get_categories():
    """
    Returns all categories with courses.
    Usage: {% get_categories as categories %}
    """
    return Category.objects.filter(course__is_published=True).distinct().order_by('name')

@register.filter
def get_item(dictionary, key):
    """
    Template filter to access dictionary values by key.
    Usage: {{ my_dict|get_item:key }}
    """
    if not dictionary:
        return None
    return dictionary.get(key)

@register.filter
def average_rating(ratings):
    """
    Calculate average rating from a queryset of ratings.
    Usage: {{ course.ratings.all|average_rating }}
    """
    if not ratings:
        return 0
    total = sum(rating.rating for rating in ratings)
    count = ratings.count()
    return round(total / count, 1) if count > 0 else 0

@register.filter
def course_level(course):
    """
    Get the overall level of a course based on its modules.
    Returns the highest level among modules or 'beginner' if no modules.
    Usage: {{ course|course_level }}
    """
    if not course.modules.exists():
        return 'beginner'
    
    levels = {'beginner': 1, 'intermediate': 2, 'advanced': 3}
    max_level = 1
    
    for module in course.modules.all():
        if module.level in levels and levels[module.level] > max_level:
            max_level = levels[module.level]
    
    # Convert back to level name
    for level_name, level_num in levels.items():
        if level_num == max_level:
            return level_name
    
    return 'beginner'

@register.filter
def get_level_display(level):
    """
    Get display name for course level.
    Usage: {{ course|course_level|get_level_display }}
    """
    level_names = {
        'beginner': 'Débutant',
        'intermediate': 'Intermédiaire', 
        'advanced': 'Avancé'
    }
    return level_names.get(level, 'Débutant')

@register.filter
def has_promotional_video(course):
    """
    Check if a course has a promotional video.
    Usage: {% if course|has_promotional_video %}
    """
    return bool(course.video_promotionnelle)

@register.filter
def format_price(price):
    """
    Format price for display with FCFA currency.
    Usage: {{ price|format_price }}
    """
    if price is None:
        return "0 FCFA"
    
    try:
        # Convertir en entier si c'est un Decimal
        price_int = int(price)
        return f"{price_int:,} FCFA".replace(',', ' ')
    except (ValueError, TypeError):
        return f"{price} FCFA"
