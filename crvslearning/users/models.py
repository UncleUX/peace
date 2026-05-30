from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
import json
from django.core.cache import cache

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('learner', _('Apprenant')),
        ('trainer', _('Formateur')),
        ('admin', _('Administrateur')),
    )
    
    UNIVERSITE_CHOICES = [
        ('uya1', 'Université de Yaoundé 1'),
        ('uya2', 'Université de Yaoundé 2 - Soa'),
        ('ucac', 'Université Catholique d\'Afrique Centrale - UCAC'),
        ('injs', 'INJS'),
        ('ud', 'Université de Douala'),
        ('ub', 'Université de Bertoua'),
        ('uds', 'Université de Dschang'),
        ('mantanfen', 'MANTANFEN'),
        ('istag', 'ISTAG'),
        ('saintou', 'Institut Siantou'),
    ]
    
    FONCTION_CHOICES = [
        ('secretaire', 'Secrétaire d\'état civil'),
        ('officier', 'Officier d\'état civil'),
    ]
    
    STRUCTURE_CHOICES = [
        ('bunec', 'BUNEC'),
        ('commune', 'Commune'),
        ('minsante', 'Ministère de la Santé'),
        ('minddevel', 'Ministère du Développement'),
        ('ong', 'ONG'),
        ('universite', 'Université'),
        ('consultant', 'Consultant'),
        ('partenaire', 'Partenaire'),
        ('autre', 'Autre'),
    ]
    
    BUNEC_STRUCTURE_CHOICES = [
        ('direction_generale', 'Direction Générale'),
        ('agence_regionale', 'Agence Régionale'),
    ]
    
    DIRECTION_GENERALE_SERVICE_CHOICES = [
        ('cabinet_dg', 'Cabinet DG'),
        ('das', 'DAS'),
        ('daf', 'DAF'),
        ('dsi', 'DSI'),
        ('dncc', 'DNCC'),
        ('cfs', 'CFS'),
        ('cajc', 'CAJC'),
        ('dac', 'DAC'),
        ('courrier', 'COURRIER'),
        ('cppc', 'CPPC'),
        ('autres', 'AUTRES'),
    ]
    
    AGENCE_REGIONALE_SERVICE_CHOICES = [
        ('service_suivi_cec', 'Service du suivi et des CEC'),
        ('service_formation_sensibilisation', 'Service de la formation et de la sensibilisation'),
        ('service_informatique_fichier_statistiques', 'Service informatique du fichier et des statistiques'),
        ('autres', 'Autres'),
    ]
    
    SANTE_TYPE_CHOICES = [
        ('admin_centrale', 'Administration centrale'),
        ('fosa', 'FOSA (Formation Sanitaire)'),
    ]
    
    FOSA_PROFESSION_CHOICES = [
        ('medecin', 'Médecin'),
        ('sage_femme', 'Sage femme'),
        ('infirmiere', 'Infirmière'),
        ('aide_soignant', 'Aide soignant'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='learner')
    date_of_birth = models.DateField(
        verbose_name='Date de naissance',
        help_text='Entrez votre date de naissance',
        null=True,
        blank=True
    )
    structure = models.CharField(
        max_length=20, 
        choices=STRUCTURE_CHOICES, 
        verbose_name='Structure',
        help_text='Sélectionnez votre structure d\'appartenance',
        default='autre',
        blank=False
    )
    service = models.CharField(
        max_length=100,
        verbose_name='Service',
        help_text='Veuillez préciser votre service à la BUNEC',
        blank=True,
        null=True
    )
    
    bunec_structure = models.CharField(
        max_length=30,
        choices=BUNEC_STRUCTURE_CHOICES,
        verbose_name='Structure BUNEC',
        help_text='Sélectionnez votre structure au sein de la BUNEC',
        blank=True,
        null=True
    )
    
    bunec_service = models.CharField(
        max_length=50,
        verbose_name='Service BUNEC',
        help_text='Sélectionnez votre service spécifique',
        blank=True,
        null=True
    )
    commune = models.CharField(
        max_length=100,
        verbose_name='Nom de la commune',
        help_text='Veuillez entrer le nom de votre commune',
        blank=True,
        null=True
    )
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    cover = models.ImageField(upload_to='covers/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    last_seen = models.DateTimeField(blank=True, null=True)
    
    fonction = models.CharField(
        max_length=20,
        choices=FONCTION_CHOICES,
        verbose_name='Fonction',
        help_text='Fonction au sein de la commune',
        blank=True,
        null=True
    )
    
    universite = models.CharField(
        max_length=20,
        choices=UNIVERSITE_CHOICES,
        verbose_name='Établissement universitaire',
        blank=True,
        null=True
    )
    
    sante_type = models.CharField(
        max_length=20,
        choices=SANTE_TYPE_CHOICES,
        verbose_name='Type de structure sanitaire',
        blank=True,
        null=True
    )
    
    sante_service = models.CharField(
        max_length=100,
        verbose_name='Service (Administration centrale)',
        help_text='Entrez votre service au sein de l\'administration centrale',
        blank=True,
        null=True
    )
    
    fosa_profession = models.CharField(
        max_length=20,
        choices=FOSA_PROFESSION_CHOICES,
        verbose_name='Profession (FOSA)',
        blank=True,
        null=True
    )

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_online(self):
        from django.utils import timezone
        from django.core.cache import cache
        
        # Vérifier d'abord le cache pour plus de performance
        cache_key = f'user_online_{self.id}'
        cached_status = cache.get(cache_key)
        
        if cached_status:
            try:
                data = json.loads(cached_status)
                # Si le cache date de moins de 2 minutes, utiliser le cache
                if (timezone.now() - timezone.datetime.fromisoformat(data['last_seen'])).total_seconds() < 120:
                    return data['is_online']
            except (json.JSONDecodeError, ValueError):
                pass
        
        # Calculer le statut en temps réel si pas de cache valide
        if not self.last_seen:
            return False
        
        # Augmenter le seuil à 10 minutes pour plus de flexibilité
        is_online = (timezone.now() - self.last_seen).total_seconds() < 600
        
        # Mettre en cache pour 2 minutes
        cache.set(cache_key, json.dumps({
            'is_online': is_online,
            'last_seen': self.last_seen.isoformat()
        }), 120)
        
        return is_online

    def get_avatar_url(self):
        """
        Return avatar URL if exists, else None.
        """
        if self.avatar and hasattr(self.avatar, 'url'):
            try:
                return self.avatar.url
            except ValueError:
                return None
        return None

    def get_avatar_display(self, default_color='#3b82f6'):
        """
        Returns avatar display info:
        - If image → return URL
        - Else → return initial with generated color
        """
        avatar_url = self.get_avatar_url()
        if avatar_url:
            return {
                'type': 'image',
                'url': avatar_url,
                'alt': f"Photo de profil de {self.username}"
            }

        # Generate a background color based on username
        import hashlib
        if self.username:
            hue = int(hashlib.md5(self.username.encode()).hexdigest()[:8], 16) % 360
            bg_color = f'hsl({hue}, 70%, 60%)'
        else:
            bg_color = default_color

        # Get initial
        initial = (self.first_name[0] if self.first_name else self.username[0]).upper()

        return {
            'type': 'initial',
            'text': initial,
            'bg_color': bg_color,
            'color': '#ffffff',
            'alt': f"Initiale de {self.username}"
        }

    def get_unread_messages(self):
        """
        Return user's unread messages
        """
        if hasattr(self, 'received_messages'):
            return self.received_messages.filter(read=False)
        return self.receivedmessage_set.filter(read=False)

    def get_unread_messages_count(self):
        """
        Return count of unread messages
        """
        return self.get_unread_messages().count()


class UserPreference(models.Model):
    """
    Modèle pour stocker les préférences utilisateur avec support pour cookies
    """
    user = models.OneToOneField(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='preferences',
        verbose_name=_('Utilisateur')
    )
    
    # Préférences de modules et catégories
    favorite_modules = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Modules favoris'),
        help_text=_('Liste des IDs des modules favoris')
    )
    
    favorite_categories = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Catégories favorites'),
        help_text=_('Liste des IDs des catégories favorites')
    )
    
    # Préférences d'affichage
    theme = models.CharField(
        max_length=20,
        choices=[
            ('light', 'Clair'),
            ('dark', 'Sombre'),
            ('auto', 'Auto')
        ],
        default='light',
        verbose_name=_('Thème')
    )
    
    language = models.CharField(
        max_length=10,
        choices=[
            ('fr', 'Français'),
            ('en', 'English')
        ],
        default='fr',
        verbose_name=_('Langue')
    )
    
    # Préférences de notification
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    
    # Préférences d'apprentissage
    auto_play_video = models.BooleanField(default=False)
    show_progress = models.BooleanField(default=True)
    download_for_offline = models.BooleanField(default=False)
    
    # Session et cookies
    session_preferences = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Préférences de session'),
        help_text=_('Préférences temporaires stockées en session')
    )
    
    cookie_consent = models.BooleanField(
        default=False,
        verbose_name=_('Consentement cookies')
    )
    
    last_activity = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Préférence utilisateur')
        verbose_name_plural = _('Préférences utilisateurs')

    def __str__(self):
        return f"Préférences de {self.user.username}"

    def get_favorite_modules_ids(self):
        """Retourne la liste des IDs des modules favoris"""
        return self.favorite_modules or []

    def add_favorite_module(self, module_id):
        """Ajoute un module aux favoris"""
        if module_id not in self.favorite_modules:
            self.favorite_modules.append(module_id)
            self.save()

    def remove_favorite_module(self, module_id):
        """Retire un module des favoris"""
        if module_id in self.favorite_modules:
            self.favorite_modules.remove(module_id)
            self.save()

    def get_favorite_categories_ids(self):
        """Retourne la liste des IDs des catégories favorites"""
        return self.favorite_categories or []

    def add_favorite_category(self, category_id):
        """Ajoute une catégorie aux favoris"""
        if category_id not in self.favorite_categories:
            self.favorite_categories.append(category_id)
            self.save()

    def remove_favorite_category(self, category_id):
        """Retire une catégorie des favoris"""
        if category_id in self.favorite_categories:
            self.favorite_categories.remove(category_id)
            self.save()

    def update_session_preference(self, key, value):
        """Met à jour une préférence de session"""
        self.session_preferences[key] = value
        self.save()

    def get_session_preference(self, key, default=None):
        """Récupère une préférence de session"""
        return self.session_preferences.get(key, default)

    def to_cookie_data(self):
        """Convertit les préférences en format pour cookie"""
        return {
            'theme': self.theme,
            'language': self.language,
            'favorite_modules': self.favorite_modules,
            'favorite_categories': self.favorite_categories,
            'email_notifications': self.email_notifications,
            'push_notifications': self.push_notifications,
            'auto_play_video': self.auto_play_video,
            'show_progress': self.show_progress
        }

    @classmethod
    def create_from_cookie_data(cls, user, cookie_data):
        """Crée les préférences utilisateur à partir des données cookie"""
        preferences = cls.objects.create(
            user=user,
            theme=cookie_data.get('theme', 'light'),
            language=cookie_data.get('language', 'fr'),
            favorite_modules=cookie_data.get('favorite_modules', []),
            favorite_categories=cookie_data.get('favorite_categories', []),
            email_notifications=cookie_data.get('email_notifications', True),
            push_notifications=cookie_data.get('push_notifications', True),
            auto_play_video=cookie_data.get('auto_play_video', False),
            show_progress=cookie_data.get('show_progress', True),
            cookie_consent=True
        )
        return preferences
