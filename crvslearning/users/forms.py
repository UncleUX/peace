from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    # Champ rôle caché avec valeur par défaut
    role = forms.ChoiceField(
        label='Rôle',
        choices=(
            ('learner', 'Apprenant'),
            ('trainer', 'Formateur')
        ),
        widget=forms.HiddenInput(),  # Champ caché
        initial='learner',  # Valeur par défaut
        required=False  # Non obligatoire
    )
    
    # Champ nom
    first_name = forms.CharField(
        label='Prénom',
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Entrez votre prénom'
        })
    )
    
    # Champ prénom
    last_name = forms.CharField(
        label='Nom',
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Entrez votre nom de famille'
        })
    )
    
    # Champ date de naissance
    date_of_birth = forms.DateField(
        label='Date de naissance',
        required=True,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    structure = forms.ChoiceField(
        label='Structure',
        choices=CustomUser.STRUCTURE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text='Sélectionnez votre structure d\'appartenance',
        required=True
    )
    
    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'date_of_birth', 'username', 'email', 'role', 'structure', 'service', 'bunec_structure', 'bunec_service', 'commune', 'fonction', 'universite', 'sante_type', 'sante_service', 'fosa_profession', 'password1', 'password2')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personnalisation des champs
        self.fields['username'].help_text = 'Obligatoire. 150 caractères maximum. Lettres, chiffres et @/./+/-/_ uniquement.'
        self.fields['email'].required = True
        
        # Le champ rôle est maintenant caché et non requis
        self.fields['role'].widget = forms.HiddenInput()
        self.fields['role'].required = False
        self.fields['role'].initial = 'learner'
        
        # Configuration du champ service
        self.fields['service'].required = False
        self.fields['service'].widget.attrs.update({
            'class': 'form-control',
            'style': 'display: none; margin-top: 0.5rem;',
            'placeholder': 'Entrez votre service à la BUNEC'
        })
        
        # Configuration des champs BUNEC
        self.fields['bunec_structure'] = forms.ChoiceField(
            label='Structure BUNEC',
            choices=CustomUser.BUNEC_STRUCTURE_CHOICES,
            required=False,
            widget=forms.Select(attrs={
                'class': 'form-select',
                'style': 'display: none; margin-top: 0.5rem;',
                'id': 'bunec_structure_select'
            })
        )
        
        self.fields['bunec_service'] = forms.ChoiceField(
            label='Service BUNEC',
            required=False,
            widget=forms.Select(attrs={
                'class': 'form-select',
                'style': 'display: none; margin-top: 0.5rem;',
                'id': 'bunec_service_select'
            })
        )
        
        # Configuration du champ commune
        self.fields['commune'].required = False
        self.fields['commune'].widget.attrs.update({
            'class': 'form-control',
            'style': 'display: none; margin-top: 0.5rem;',
            'placeholder': 'Entrez le nom de votre commune'
        })
        
        # Configuration du champ fonction
        self.fields['fonction'] = forms.ChoiceField(
            label='Fonction',
            choices=CustomUser.FONCTION_CHOICES,
            required=False,
            widget=forms.Select(attrs={
                'class': 'form-select',
                'style': 'display: none; margin-top: 0.5rem;',
                'placeholder': 'Sélectionnez votre fonction'
            })
        )
        
        # Champ université
        self.fields['universite'] = forms.ChoiceField(
            label='Établissement universitaire',
            choices=CustomUser.UNIVERSITE_CHOICES,
            required=False,
            widget=forms.Select(attrs={
                'class': 'form-select',
                'style': 'display: none; margin-top: 1rem;',
                'placeholder': 'Sélectionnez votre établissement'
            })
        )
        
        # Configuration des champs pour le Ministère de la Santé
        self.fields['sante_type'] = forms.ChoiceField(
            label='Type de structure sanitaire',
            choices=CustomUser.SANTE_TYPE_CHOICES,
            required=False,
            widget=forms.Select(attrs={
                'class': 'form-select',
                'style': 'display: none; margin-top: 1rem;',
                'placeholder': 'Sélectionnez le type de structure'
            })
        )
        
        self.fields['sante_service'] = forms.CharField(
            label='Service (Administration centrale)',
            required=False,
            widget=forms.TextInput(attrs={
                'class': 'form-control',
                'style': 'display: none; margin-top: 1rem;',
                'placeholder': 'Entrez votre service'
            })
        )
        
        self.fields['fosa_profession'] = forms.ChoiceField(
            label='Profession (FOSA)',
            choices=CustomUser.FOSA_PROFESSION_CHOICES,
            required=False,
            widget=forms.Select(attrs={
                'class': 'form-select',
                'style': 'display: none; margin-top: 1rem;',
                'placeholder': 'Sélectionnez votre profession'
            })
        )
        
    def clean(self):
        cleaned_data = super().clean()
        structure = cleaned_data.get('structure')
        service = cleaned_data.get('service')
        commune = cleaned_data.get('commune')
        fonction = cleaned_data.get('fonction')
        universite = cleaned_data.get('universite')
        sante_type = cleaned_data.get('sante_type')
        sante_service = cleaned_data.get('sante_service')
        fosa_profession = cleaned_data.get('fosa_profession')
        
        # S'assurer que le rôle est toujours 'learner'
        if not cleaned_data.get('role'):
            cleaned_data['role'] = 'learner'
        
        # Ne valider que si le formulaire est soumis
        if not self.data:
            return cleaned_data
            
        # Validation pour BUNEC
        if structure == 'bunec':
            if not service:
                self.add_error('service', 'Veuillez préciser votre service à la BUNEC')
        
        # Validation pour Commune
        elif structure == 'commune':
            if not commune:
                self.add_error('commune', 'Veuillez entrer le nom de votre commune')
            if not fonction:
                self.add_error('fonction', 'Veuillez sélectionner votre fonction')
                
        # Validation pour Université
        elif structure == 'universite':
            if not universite:
                self.add_error('universite', 'Veuillez sélectionner votre établissement universitaire')
        
        # Validation pour Ministère de la Santé
        elif structure == 'minsante':
            if not sante_type:
                self.add_error('sante_type', 'Veuillez sélectionner le type de structure')
            elif sante_type == 'admin_centrale' and not sante_service:
                self.add_error('sante_service', 'Veuillez préciser votre service')
            elif sante_type == 'fosa' and not fosa_profession:
                self.add_error('fosa_profession', 'Veuillez sélectionner votre profession')
            
        return cleaned_data


class ProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'email', 'bio', 'avatar', 'cover', 'structure', 'service', 'commune', 'fonction')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'structure': forms.Select(attrs={'class': 'form-select'}),
            'service': forms.TextInput(attrs={'class': 'form-control'}),
            'commune': forms.TextInput(attrs={'class': 'form-control'}),
            'fonction': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Masquer les champs non pertinents selon la structure
        if self.instance.structure != 'bunec':
            self.fields['service'].widget = forms.HiddenInput()
        if self.instance.structure != 'commune':
            self.fields['commune'].widget = forms.HiddenInput()
            self.fields['fonction'].widget = forms.HiddenInput()
            
        # Ajouter des placeholders
        self.fields['service'].widget.attrs.update({
            'placeholder': 'Entrez votre service à la BUNEC',
            'style': 'margin-top: 0.5rem;'
        })
        self.fields['commune'].widget.attrs.update({
            'placeholder': 'Entrez le nom de votre commune',
            'style': 'margin-top: 0.5rem;'
        })
