from django import template
from django.utils import timezone
from courses.models import Module
from ..models import ModuleAccess, Payment

register = template.Library()


@register.filter
def has_paid_access(user, module):
    """Vérifie si l'utilisateur a accès à un module payant"""
    if not user.is_authenticated:
        return False
    
    if not module.is_paid:
        return True
    
    access = ModuleAccess.objects.filter(
        user=user,
        module=module
    ).first()
    
    return access and access.is_valid


@register.filter
def get_access_status(user, module):
    """Retourne le statut d'accès à un module"""
    if not user.is_authenticated:
        return 'login_required'
    
    if not module.is_paid:
        return 'free'
    
    access = ModuleAccess.objects.filter(
        user=user,
        module=module
    ).first()
    
    if access and access.is_valid:
        return 'granted'
    else:
        return 'payment_required'


@register.simple_tag
def get_user_module_accesses(user):
    """Retourne les accès aux modules de l'utilisateur"""
    if not user.is_authenticated:
        return ModuleAccess.objects.none()
    
    return ModuleAccess.objects.filter(
        user=user,
        is_active=True
    ).select_related('module', 'module__course')


@register.simple_tag
def get_user_payment_history(user, limit=5):
    """Retourne l'historique des paiements de l'utilisateur"""
    if not user.is_authenticated:
        return Payment.objects.none()
    
    return Payment.objects.filter(
        user=user
    ).order_by('-created_at')[:limit]


@register.filter
def format_price(price):
    """Formate le prix en FCFA"""
    if price == 0:
        return 'Gratuit'
    return f"{price:,.0f} FCFA"


@register.simple_tag
def can_access_lesson(user, lesson):
    """Vérifie si l'utilisateur peut accéder à une leçon"""
    if not user.is_authenticated:
        return False
    
    module = lesson.module
    
    # Si le module n'est pas payant, accès autorisé
    if not module.is_paid:
        return True
    
    # Vérifier l'accès au module
    access = ModuleAccess.objects.filter(
        user=user,
        module=module
    ).first()
    
    return access and access.is_valid
