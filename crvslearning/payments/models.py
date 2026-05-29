from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from courses.models import Module
import uuid

class Payment(models.Model):
    """Modèle pour gérer les paiements des modules"""
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('completed', 'Complété'),
        ('failed', 'Échoué'),
        ('refunded', 'Remboursé'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name=_('Utilisateur')
    )
    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name=_('Module')
    )
    amount = models.DecimalField(
        'Montant',
        max_digits=10,
        decimal_places=2,
        help_text='Montant payé en FCFA'
    )
    status = models.CharField(
        'Statut',
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    payment_method = models.CharField(
        'Méthode de paiement',
        max_length=50,
        blank=True,
        null=True,
        help_text='Ex: Orange Money, MTN Mobile Money, Carte bancaire'
    )
    transaction_id = models.CharField(
        'ID de transaction',
        max_length=100,
        blank=True,
        null=True,
        unique=True
    )
    created_at = models.DateTimeField('Date de création', auto_now_add=True)
    updated_at = models.DateTimeField('Date de mise à jour', auto_now=True)
    
    class Meta:
        verbose_name = _('Paiement')
        verbose_name_plural = _('Paiements')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Paiement {self.id} - {self.user.username} - {self.module.title}"
    
    @property
    def is_successful(self):
        return self.status == 'completed'


class ModuleAccess(models.Model):
    """Modèle pour gérer l'accès aux modules payants"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='module_accesses',
        verbose_name=_('Utilisateur')
    )
    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name='accesses',
        verbose_name=_('Module')
    )
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name='accesses',
        verbose_name=_('Paiement')
    )
    granted_at = models.DateTimeField('Date d\'accès', auto_now_add=True)
    expires_at = models.DateTimeField(
        'Date d\'expiration',
        null=True,
        blank=True,
        help_text='Laisser vide pour un accès permanent'
    )
    is_active = models.BooleanField('Accès actif', default=True)
    
    class Meta:
        verbose_name = _('Accès au module')
        verbose_name_plural = _('Accès aux modules')
        unique_together = ('user', 'module')
        ordering = ['-granted_at']
    
    def __str__(self):
        return f"Accès de {self.user.username} à {self.module.title}"
    
    @property
    def is_valid(self):
        """Vérifie si l'accès est encore valide"""
        if not self.is_active:
            return False
        if self.expires_at and self.expires_at < timezone.now():
            return False
        return True


class PaymentPlan(models.Model):
    """Modèle pour gérer les plans de paiement (abonnements)"""
    name = models.CharField('Nom du plan', max_length=100)
    description = models.TextField('Description', blank=True)
    price = models.DecimalField('Prix', max_digits=10, decimal_places=2)
    duration_days = models.PositiveIntegerField(
        'Durée (jours)',
        help_text='Durée de l\'abonnement en jours. 0 pour illimité'
    )
    max_modules = models.PositiveIntegerField(
        'Nombre de modules maximum',
        null=True,
        blank=True,
        help_text='Nombre de modules inclus. Laisser vide pour illimité'
    )
    is_active = models.BooleanField('Plan actif', default=True)
    created_at = models.DateTimeField('Date de création', auto_now_add=True)
    
    class Meta:
        verbose_name = _('Plan de paiement')
        verbose_name_plural = _('Plans de paiement')
        ordering = ['price']
    
    def __str__(self):
        return f"{self.name} - {self.price} FCFA"


class Subscription(models.Model):
    """Modèle pour gérer les abonnements des utilisateurs"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payment_subscriptions',
        verbose_name=_('Utilisateur')
    )
    plan = models.ForeignKey(
        PaymentPlan,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name=_('Plan')
    )
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name='plan_subscriptions',
        verbose_name=_('Paiement initial')
    )
    started_at = models.DateTimeField('Date de début', auto_now_add=True)
    expires_at = models.DateTimeField('Date d\'expiration')
    is_active = models.BooleanField('Abonnement actif', default=True)
    
    class Meta:
        verbose_name = _('Abonnement')
        verbose_name_plural = _('Abonnements')
        ordering = ['-started_at']
    
    def __str__(self):
        return f"Abonnement {self.plan.name} de {self.user.username}"
    
    @property
    def is_valid(self):
        """Vérifie si l'abonnement est encore valide"""
        if not self.is_active:
            return False
        return self.expires_at >= timezone.now()
    
    def extend(self, days):
        """Prolonge l'abonnement du nombre de jours spécifié"""
        from django.utils import timezone
        if self.expires_at < timezone.now():
            self.expires_at = timezone.now() + timezone.timedelta(days=days)
        else:
            self.expires_at += timezone.timedelta(days=days)
        self.save()
