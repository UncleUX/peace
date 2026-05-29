from django import forms
from django.core.exceptions import ValidationError
from .models import Course, Module, Lesson, Category


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'description', 'category', 'language', 'thumbnail']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'language': forms.Select(attrs={'class': 'form-control'}),
        }


class ModuleForm(forms.ModelForm):
    class Meta:
        model = Module
        fields = ['title', 'description', 'level', 'order']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'level': forms.Select(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['title', 'description', 'content_file', 'order']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'required': 'required'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'content_file': forms.ClearableFileInput(attrs={'class': 'form-control', 'required': False}),
            # 'video_file': forms.ClearableFileInput(attrs={'class': 'form-control', 'required': False}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'required': 'required'}),
        }


class CategoryForm(forms.ModelForm):
    """
    Formulaire pour la création et la modification de catégories.
    Valide l'unicité du nom (insensible à la casse).
    """
    class Meta:
        model = Category
        fields = ['name', 'image']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'vTextField',
                'placeholder': 'Entrez le nom de la catégorie',
                'required': 'required',
                'maxlength': '100'
            }),
            'image': forms.ClearableFileInput(attrs={
                'class': 'vTextField',
                'accept': 'image/*'
            }),
        }
        help_texts = {
            'name': 'Le nom de la catégorie doit être unique (100 caractères max).',
            'image': 'Image représentative de la catégorie (format recommandé: 800x600px).',
        }
    
    def clean_name(self):
        """Valide que le nom de la catégorie est unique (insensible à la casse)."""
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise ValidationError("Ce champ est obligatoire.")
        
        # Vérifie si une catégorie avec ce nom existe déjà (insensible à la casse)
        # Sauf si on est en train de modifier la catégorie actuelle
        qs = Category.objects.filter(name__iexact=name)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
            
        if qs.exists():
            raise ValidationError("Une catégorie avec ce nom existe déjà.")
        
        return name
