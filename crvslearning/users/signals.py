from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.contrib.auth import get_user_model
from courses.models import LearningPath
from notifications.models import Notification

User = get_user_model()

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_learning_path(sender, instance, created, **kwargs):
    """
    Crée automatiquement un LearningPath lorsqu'un nouvel utilisateur est créé
    """
    if created and not hasattr(instance, 'learning_path'):
        LearningPath.objects.create(user=instance)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_learning_path(sender, instance, **kwargs):
    """
    Sauvegarde le LearningPath lors de la mise à jour de l'utilisateur
    """
    if hasattr(instance, 'learning_path'):
        instance.learning_path.save()

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def send_welcome_notification(sender, instance, created, **kwargs):
    """
    Envoie une notification de bienvenue quand un nouvel utilisateur s'inscrit
    """
    if created:  # Seulement lors de la création
        message = f"Bienvenue {instance.first_name} {instance.last_name} !\n\nNous sommes ravis de vous accueillir sur notre plateforme d'apprentissage en ligne. Votre compte a été créé avec succès.\n\nN'hésitez pas à explorer les cours disponibles et à commencer votre parcours d'apprentissage.\n\nL'équipe CRVS Learning"
        
        Notification.objects.create(
            user=instance,
            sender="CRVS Learning",
            subject="Bienvenue sur CRVS Learning !",
            message=message,
            url="/courses/"
        )
