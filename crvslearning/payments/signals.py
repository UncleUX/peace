from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Payment, ModuleAccess


@receiver(post_save, sender=Payment)
def handle_payment_completion(sender, instance, created, **kwargs):
    """Gère la complétion de paiement et la création d'accès"""
    if not created and instance.status == 'completed':
        # Utiliser get_or_create pour éviter les doublons
        module_access, access_created = ModuleAccess.objects.get_or_create(
            user=instance.user,
            module=instance.module,
            defaults={
                'payment': instance,
                'expires_at': None  # Accès permanent pour les modules individuels
            }
        )
        
        # Si l'accès existait déjà, s'assurer qu'il est actif
        if not access_created:
            module_access.is_active = True
            module_access.save()
    
    elif not created and instance.status in ['failed', 'refunded']:
        # Désactiver l'accès si le paiement échoue ou est remboursé
        access = ModuleAccess.objects.filter(
            user=instance.user,
            module=instance.module,
            payment=instance
        ).first()
        if access:
            access.is_active = False
            access.save()
