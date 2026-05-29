from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from notifications.models import Notification
from django.utils import timezone
from django.core.files.base import ContentFile
import os

User = get_user_model()

class Command(BaseCommand):
    help = 'Envoyer une notification avec pièce jointe'

    def add_arguments(self, parser):
        parser.add_argument('--user', type=str, help='Nom d utilisateur (username)')
        parser.add_argument('--all', action='store_true', help='Envoyer à tous les utilisateurs')
        parser.add_argument('--subject', type=str, required=True, help='Sujet de la notification')
        parser.add_argument('--message', type=str, required=True, help='Message de la notification')
        parser.add_argument('--url', type=str, default='/dashboard/', help='URL de redirection (défaut: /dashboard/)')
        parser.add_argument('--sender', type=str, default='Administration CRVS', help='Nom de l expéditeur')
        parser.add_argument('--attachment', type=str, required=True, help='Chemin du fichier à joindre')

    def handle(self, *args, **options):
        subject = options['subject']
        message = options['message']
        url = options['url']
        sender = options['sender']
        attachment_path = options['attachment']
        
        # Vérifier si le fichier existe
        if not os.path.exists(attachment_path):
            self.stdout.write(self.style.ERROR(f"❌ Fichier non trouvé: {attachment_path}"))
            return
        
        if options['all']:
            self.send_to_all_users(subject, message, url, sender, attachment_path)
        elif options['user']:
            self.send_to_user(options['user'], subject, message, url, sender, attachment_path)
        else:
            self.stdout.write(self.style.ERROR('Veuillez spécifier --user ou --all'))

    def send_to_user(self, username, subject, message, url, sender, attachment_path):
        """Envoyer une notification avec pièce jointe à un utilisateur spécifique"""
        try:
            user = User.objects.get(username=username)
            
            notification = Notification.objects.create(
                user=user,
                sender=sender,
                subject=subject,
                message=message,
                url=url,
                created_at=timezone.now()
            )
            
            # Ajouter la pièce jointe
            with open(attachment_path, 'rb') as f:
                filename = os.path.basename(attachment_path)
                notification.attachment.save(filename, ContentFile(f.read()))
                notification.save()
            
            self.stdout.write(self.style.SUCCESS(
                f"✅ Notification avec pièce jointe envoyée à {username}: {subject}"
            ))
            self.stdout.write(f"📧 ID: {notification.id}")
            self.stdout.write(f"📎 Pièce jointe: {filename}")
            
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"❌ Utilisateur '{username}' non trouvé"))

    def send_to_all_users(self, subject, message, url, sender, attachment_path):
        """Envoyer une notification avec pièce jointe à tous les utilisateurs"""
        users = User.objects.all()
        count = 0
        
        for user in users:
            notification = Notification.objects.create(
                user=user,
                sender=sender,
                subject=subject,
                message=message,
                url=url,
                created_at=timezone.now()
            )
            
            # Ajouter la pièce jointe
            with open(attachment_path, 'rb') as f:
                filename = os.path.basename(attachment_path)
                notification.attachment.save(filename, ContentFile(f.read()))
                notification.save()
            
            count += 1
        
        self.stdout.write(self.style.SUCCESS(
            f"✅ Notification avec pièce jointe envoyée à {count} utilisateurs: {subject}"
        ))
        self.stdout.write(f"📎 Pièce jointe partagée: {os.path.basename(attachment_path)}")
