from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class ChatRoom(models.Model):
    """Modèle pour les salons de discussion"""
    name = models.CharField(max_length=100, verbose_name="Nom du salon")
    description = models.TextField(blank=True, verbose_name="Description")
    participants = models.ManyToManyField(User, related_name='chat_rooms', verbose_name="Participants")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    is_private = models.BooleanField(default=False, verbose_name="Salon privé")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_rooms', verbose_name="Créé par")
    
    class Meta:
        verbose_name = "Salon de discussion"
        verbose_name_plural = "Salons de discussion"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def get_last_message(self):
        """Retourne le dernier message du salon"""
        return self.messages.order_by('-timestamp').first()

class Message(models.Model):
    """Modèle pour les messages"""
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages', verbose_name="Salon")
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages', verbose_name="Expéditeur")
    content = models.TextField(verbose_name="Contenu du message")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Date d'envoi")
    is_edited = models.BooleanField(default=False, verbose_name="Message édité")
    reply_to = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies', verbose_name="Réponse à")
    
    class Meta:
        verbose_name = "Message"
        verbose_name_plural = "Messages"
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.sender.username} - {self.timestamp.strftime('%H:%M')}"
    
    def get_time_display(self):
        """Retourne l'heure formatée"""
        return self.timestamp.strftime('%H:%M')

class MessageAttachment(models.Model):
    """Modèle pour les pièces jointes des messages"""
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='attachments', verbose_name="Message")
    file = models.FileField(upload_to='chat_attachments/%Y/%m/', verbose_name="Fichier")
    filename = models.CharField(max_length=255, verbose_name="Nom du fichier")
    file_size = models.PositiveIntegerField(verbose_name="Taille du fichier")
    file_type = models.CharField(max_length=50, verbose_name="Type de fichier")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Date d'upload")
    
    class Meta:
        verbose_name = "Pièce jointe"
        verbose_name_plural = "Pièces jointes"
        ordering = ['-uploaded_at']
    
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

class MessageRead(models.Model):
    """Modèle pour suivre les messages lus"""
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='read_by', verbose_name="Message")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='read_messages', verbose_name="Utilisateur")
    read_at = models.DateTimeField(auto_now_add=True, verbose_name="Lu le")
    
    class Meta:
        verbose_name = "Message lu"
        verbose_name_plural = "Messages lus"
        unique_together = ['message', 'user']
    
    def __str__(self):
        return f"{self.user.username} a lu {self.message}"

class UserStatus(models.Model):
    """Modèle pour suivre le statut en ligne des utilisateurs"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='chat_status', verbose_name="Utilisateur")
    is_online = models.BooleanField(default=False, verbose_name="En ligne")
    last_seen = models.DateTimeField(default=timezone.now, verbose_name="Dernière activité")
    current_room = models.ForeignKey(ChatRoom, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Salon actuel")
    
    class Meta:
        verbose_name = "Statut utilisateur"
        verbose_name_plural = "Statuts utilisateurs"
    
    def __str__(self):
        return f"{self.user.username} - {'En ligne' if self.is_online else 'Hors ligne'}"
    
    def update_last_seen(self):
        """Met à jour la dernière activité"""
        self.last_seen = timezone.now()
        self.save(update_fields=['last_seen'])
