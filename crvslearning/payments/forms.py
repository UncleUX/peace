from django import forms
from .models import Payment, PaymentPlan


class PaymentForm(forms.ModelForm):
    """Formulaire de paiement"""
    
    class Meta:
        model = Payment
        fields = ['payment_method', 'phone_number']
        widgets = {
            'payment_method': forms.RadioSelect(
                choices=[
                    ('orange_money', 'Orange Money'),
                    ('mtn_money', 'MTN Mobile Money'),
                    ('card', 'Carte bancaire'),
                ]
            ),
            'phone_number': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Entrez votre numéro de téléphone',
                    'pattern': r'^[6-9]\d{8}$',
                    'title': 'Numéro de téléphone camerounais (ex: 612345678)'
                }
            ),
        }
    
    payment_method = forms.ChoiceField(
        choices=[
            ('orange_money', 'Orange Money'),
            ('mtn_money', 'MTN Mobile Money'),
            ('card', 'Carte bancaire'),
        ],
        widget=forms.RadioSelect(
            attrs={'class': 'form-check-input'}
        )
    )
    
    phone_number = forms.CharField(
        max_length=20,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Entrez votre numéro de téléphone',
                'pattern': r'^[6-9]\d{8}$',
                'title': 'Numéro de téléphone camerounais (ex: 612345678)'
            }
        )
    )


class SubscriptionForm(forms.ModelForm):
    """Formulaire d'abonnement"""
    
    class Meta:
        model = PaymentPlan
        fields = []
        widgets = {}


class PaymentPlanForm(forms.ModelForm):
    """Formulaire pour les plans de paiement (admin)"""
    
    class Meta:
        model = PaymentPlan
        fields = ['name', 'description', 'price', 'duration_days', 'max_modules', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'duration_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_modules': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
