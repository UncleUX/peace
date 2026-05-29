from django import template

register = template.Library()

@register.filter(name='filter_level')
def filter_level(queryset, level):
    return [item for item in queryset if item.level == level]
