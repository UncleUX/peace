from django import forms
from django.contrib.auth import get_user_model
from .models import ChatRoom, Message

User = get_user_model()

class ChatRoomForm(forms.ModelForm):
    """Formulaire pour créer/éditer un salon de discussion"""
    participants = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select',
            'placeholder': 'Sélectionnez des participants'
        }),
        required=False,
        help_text="Sélectionnez les utilisateurs à ajouter au salon"
    )
    
    class Meta:
        model = ChatRoom
        fields = ['name', 'description', 'participants', 'is_private']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom du salon'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Description du salon (optionnel)',
                'rows': 3
            }),
            'is_private': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            # Exclure l'utilisateur actuel de la liste des participants
            self.fields['participants'].queryset = User.objects.exclude(id=user.id)

class MessageForm(forms.ModelForm):
    """Formulaire pour envoyer un message"""
    
    class Meta:
        model = Message
        fields = ['content']
        widgets = {
            'content': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tapez votre message...',
                'autocomplete': 'off'
            })
        }
    
    def clean_content(self):
        content = self.cleaned_data.get('content')
        if not content or not content.strip():
            raise forms.ValidationError("Le message ne peut pas être vide")
        return content.strip()
