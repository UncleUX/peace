from django import forms
from django.contrib.auth import get_user_model
from .models import Question, Answer, Category
from courses.models import Module, Lesson

User = get_user_model()

class QuestionForm(forms.ModelForm):
    """Formulaire pour poser une question"""
    class Meta:
        model = Question
        fields = ['title', 'content', 'category', 'course', 'module', 'lesson', 'tags']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Titre de votre question...'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Décrivez votre question en détail...'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'course': forms.Select(attrs={'class': 'form-select', 'required': False}),
            'module': forms.Select(attrs={'class': 'form-select', 'required': False}),
            'lesson': forms.Select(attrs={'class': 'form-select', 'required': False}),
            'tags': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tags séparés par des virgules (ex: naissance, mariage, décès)...'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        # Récupérer toutes les catégories disponibles
        self.fields['category'].queryset = Category.objects.all()
        # Filtrer les cours/modules/leçons en fonction de l'utilisateur
        if user and hasattr(user, 'courses_enrolled'):
            self.fields['course'].queryset = user.courses_enrolled.all()
            self.fields['module'].queryset = Module.objects.filter(course__in=user.courses_enrolled.all())
            self.fields['lesson'].queryset = Lesson.objects.filter(module__course__in=user.courses_enrolled.all())
        else:
            # Si pas d'utilisateur ou pas de cours, laisser vide
            self.fields['course'].queryset = Module.objects.none()
            self.fields['module'].queryset = Module.objects.none()
            self.fields['lesson'].queryset = Lesson.objects.none()

class AnswerForm(forms.ModelForm):
    """Formulaire pour répondre à une question"""
    class Meta:
        model = Answer
        fields = ['content', 'references']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Votre réponse détaillée...'}),
            'references': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Références réglementaires, textes de loi, articles...'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Le champ question sera automatiquement défini dans la vue

class ValidationForm(forms.Form):
    """Formulaire pour valider une réponse"""
    validation_reason = forms.ChoiceField(
        choices=[
            ('', 'Sélectionnez une raison...'),
            ('correct', 'Réponse correcte et complète'),
            ('incomplete', 'Réponse partielle - informations manquantes'),
            ('unclear', 'Réponse peu claire - précision nécessaire'),
            ('irrelevant', 'Réponse non pertinente'),
            ('needs_references', 'Références réglementaires requises'),
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Commentaires supplémentaires...'}),
        required=False
    )
