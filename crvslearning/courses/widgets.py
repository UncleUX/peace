"""
Widgets personnalisés pour l'admin des cours
"""

from django import forms
from django.utils.safestring import mark_safe


class MultipleStructuresWidget(forms.SelectMultiple):
    """Widget pour sélectionner plusieurs structures avec des cases à cocher"""
    
    def __init__(self, attrs=None, choices=None):
        super().__init__(attrs)
        self.choices = choices or []
    
    def render(self, name, value, attrs=None, renderer=None):
        if value is None:
            value = []
        
        # Convertir la valeur en liste
        if isinstance(value, str):
            selected_structures = [s.strip() for s in value.split(',') if s.strip()]
        else:
            selected_structures = value or []
        
        html = []
        html.append('<div class="multiple-structures-widget">')
        
        for choice_value, choice_label in self.choices:
            checked = choice_value in selected_structures
            checkbox = f'''
            <div class="form-check">
                <input type="checkbox" 
                       name="{name}" 
                       value="{choice_value}" 
                       class="form-check-input" 
                       id="{name}_{choice_value}"
                       {'checked' if checked else ''}>
                <label class="form-check-label" for="{name}_{choice_value}">
                    {choice_label}
                </label>
            </div>
            '''
            html.append(checkbox)
        
        html.append('</div>')
        
        return mark_safe('\n'.join(html))
