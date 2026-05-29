from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class Conversation(models.Model):
    """Conversation entre deux utilisateurs (comme LinkedIn)"""
    participant1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations1')
    participant2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations2')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Conversation"
        verbose_name_plural = "Conversations"
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"Conversation: {self.participant1.username} - {self.participant2.username}"
    
    def get_other_participant(self, user):
        """Retourne l'autre participant de la conversation"""
        if user == self.participant1:
            return self.participant2
        return self.participant1
    
    def get_last_message(self):
        """Retourne le dernier message"""
        return self.messages.order_by('-timestamp').first()
    
    def get_unread_count(self, user):
        """Retourne le nombre de messages non lus pour un utilisateur"""
        return self.messages.filter(sender__ne=user, read_by__user=user).count()

class DirectMessage(models.Model):
    """Message direct entre deux utilisateurs"""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_direct_messages')
    content = models.TextField(verbose_name="Contenu du message")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Date d'envoi")
    is_edited = models.BooleanField(default=False, verbose_name="Message édité")
    
    class Meta:
        verbose_name = "Message direct"
        verbose_name_plural = "Messages directs"
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.sender.username} -> {self.conversation.get_other_participant(self.sender).username}"
    
    def get_time_display(self):
        """Retourne l'heure formatée"""
        return self.timestamp.strftime('%H:%M')

class DirectMessageAttachment(models.Model):
    """Pièce jointe pour message direct"""
    message = models.ForeignKey(DirectMessage, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='chat_attachments/%Y/%m/', verbose_name="Fichier")
    filename = models.CharField(max_length=255, verbose_name="Nom du fichier")
    file_size = models.PositiveIntegerField(verbose_name="Taille du fichier")
    file_type = models.CharField(max_length=50, verbose_name="Type de fichier")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Date d'upload")
    
    class Meta:
        verbose_name = "Pièce jointe"
        verbose_name_plural = "Pièces jointes"
    
    def __str__(self):
        return f"{self.filename} - {self.message}"
    
    def get_file_size_display(self):
        """Retourne la taille formatée"""
        if self.file_size < 1024:
            return f"{self.file_size} o"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} Ko"
        else:
            return f"{self.file_size / (1024 * 1024):.1f} Mo"
    
    def is_image(self):
        """Vérifie si le fichier est une image"""
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
        return any(self.filename.lower().endswith(ext) for ext in image_extensions)
    
    def is_pdf(self):
        """Vérifie si le fichier est un PDF"""
        return self.filename.lower().endswith('.pdf')
    
    def is_document(self):
        """Vérifie si le fichier est un document Word/Excel/PowerPoint"""
        doc_extensions = ['.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx']
        return any(self.filename.lower().endswith(ext) for ext in doc_extensions)

class DirectMessageRead(models.Model):
    """Suivi des messages lus"""
    message = models.ForeignKey(DirectMessage, on_delete=models.CASCADE, related_name='read_by')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='read_direct_messages')
    read_at = models.DateTimeField(auto_now_add=True, verbose_name="Lu le")
    
    class Meta:
        verbose_name = "Message lu"
        verbose_name_plural = "Messages lus"
        unique_together = ['message', 'user']
