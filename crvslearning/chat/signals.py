from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import UserStatus, Message

User = get_user_model()

@receiver(post_save, sender=User)
def create_user_status(sender, instance, created, **kwargs):
    """Crée un statut utilisateur lors de la création d'un utilisateur"""
    if created:
        UserStatus.objects.create(user=instance)

@receiver(post_save, sender=Message)
def mark_message_as_read_for_sender(sender, instance, created, **kwargs):
    """Marque automatiquement le message comme lu pour l'expéditeur"""
    if created:
        from .models import MessageRead
        MessageRead.objects.get_or_create(
            message=instance,
            user=instance.sender
        )
