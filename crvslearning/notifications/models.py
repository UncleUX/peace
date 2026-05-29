from django.db import models
from django.contrib.auth import get_user_model

# Obtenez le modèle User personnalisé
User = get_user_model()

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.CharField(max_length=100, default="CRVS Learning")
    subject = models.CharField(max_length=200, default="Notification")
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    url = models.URLField(blank=True, null=True)
    
    # Champ pour la pièce jointe
    attachment = models.FileField(
        upload_to='notifications/attachments/%Y/%m/%d/',
        blank=True,
        null=True,
        verbose_name="Pièce jointe"
    )
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification pour {self.user.username}: {self.subject[:50]}..."