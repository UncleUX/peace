from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from notifications.models import Notification

User = get_user_model()

class Command(BaseCommand):
    help = 'Nettoie les notifications en double pour un utilisateur spécifique'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Nom d utilisateur à nettoyer')
        parser.add_argument('--all', action='store_true', help='Nettoyer toutes les notifications en double')

    def handle(self, *args, **options):
        if options['username']:
            self.cleanup_user_notifications(options['username'])
        elif options['all']:
            self.cleanup_all_notifications()
        else:
            self.stdout.write(self.style.ERROR('Veuillez spécifier --username ou --all'))

    def cleanup_user_notifications(self, username):
        """Nettoie les notifications en double pour un utilisateur spécifique"""
        try:
            user = User.objects.get(username=username)
            
            # Compter les notifications avant nettoyage
            total_notifications = user.notifications.count()
            self.stdout.write(f"📊 Utilisateur: {username}")
            self.stdout.write(f"📧 Total notifications: {total_notifications}")
            
            # Grouper par message pour trouver les doublons
            from django.db.models import Count
            duplicates = user.notifications.values(
                'message', 'subject'
            ).annotate(
                count=Count('id')
            ).filter(count__gt=1)
            
            if duplicates:
                self.stdout.write(f"🔄 {duplicates.count()} types de messages en double trouvés")
                
                # Supprimer les doublons (garder le plus récent)
                for duplicate in duplicates:
                    notifications_to_delete = user.notifications.filter(
                        message=duplicate['message'],
                        subject=duplicate['subject']
                    ).order_by('-created_at')[1:]  # Garder le plus récent
                    
                    count = notifications_to_delete.count()
                    if count > 0:
                        notifications_to_delete.delete()
                        self.stdout.write(self.style.SUCCESS(f"✅ Supprimé {count} notifications en double: {duplicate['message'][:50]}..."))
            else:
                self.stdout.write(self.style.SUCCESS("✅ Aucun doublon trouvé"))
            
            # Compter après nettoyage
            remaining_notifications = user.notifications.count()
            self.stdout.write(f"📧 Notifications restantes: {remaining_notifications}")
            
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"❌ Utilisateur '{username}' non trouvé"))

    def cleanup_all_notifications(self):
        """Nettoie toutes les notifications en double"""
        self.stdout.write("🧹 Nettoyage de toutes les notifications en double...")
        
        from django.db.models import Count
        duplicates = Notification.objects.values(
            'user', 'message', 'subject'
        ).annotate(
            count=Count('id')
        ).filter(count__gt=1)
        
        if duplicates:
            self.stdout.write(f"🔄 {duplicates.count()} types de messages en double trouvés")
            
            total_deleted = 0
            for duplicate in duplicates:
                notifications_to_delete = Notification.objects.filter(
                    user_id=duplicate['user'],
                    message=duplicate['message'],
                    subject=duplicate['subject']
                ).order_by('-created_at')[1:]  # Garder le plus récent
                
                count = notifications_to_delete.count()
                if count > 0:
                    notifications_to_delete.delete()
                    total_deleted += count
                    self.stdout.write(self.style.SUCCESS(f"✅ Supprimé {count} notifications en double"))
            
            self.stdout.write(self.style.SUCCESS(f"🎯 Total supprimé: {total_deleted} notifications"))
        else:
            self.stdout.write(self.style.SUCCESS("✅ Aucun doublon trouvé"))
