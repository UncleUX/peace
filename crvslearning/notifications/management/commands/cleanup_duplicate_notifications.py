from django.core.management.base import BaseCommand
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from notifications.models import Notification

class Command(BaseCommand):
    help = 'Nettoie les notifications de certification en double'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Simuler le nettoyage sans supprimer')
        parser.add_argument('--user', type=str, help='Nettoyer uniquement pour un utilisateur spécifique')
        parser.add_argument('--hours', type=int, default=24, help='Période en heures à vérifier (défaut: 24)')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        username = options['user']
        hours = options['hours']
        
        self.stdout.write(f"🧹 Nettoyage des notifications en double (période: {hours} heures)")
        
        if dry_run:
            self.stdout.write("🔍 MODE SIMULATION - Aucune suppression réelle")
        
        # Définir la période
        since_date = timezone.now() - timedelta(hours=hours)
        
        # Base de la requête
        notifications = Notification.objects.filter(
            created_at__gte=since_date
        )
        
        if username:
            notifications = notifications.filter(user__username=username)
            self.stdout.write(f"👤 Utilisateur: {username}")
        
        # Trouver les doublons
        duplicates = notifications.values(
            'user_id', 'subject', 'message'
        ).annotate(
            count=Count('id')
        ).filter(count__gt=1)
        
        total_duplicates = duplicates.count()
        
        if total_duplicates == 0:
            self.stdout.write(self.style.SUCCESS("✅ Aucun doublon trouvé"))
            return
        
        self.stdout.write(f"🔄 {total_duplicates} types de messages en double trouvés")
        
        total_deleted = 0
        
        for duplicate in duplicates:
            user_id = duplicate['user_id']
            subject = duplicate['subject']
            message = duplicate['message']
            
            # Récupérer toutes les notifications en double
            duplicate_notifications = Notification.objects.filter(
                user_id=user_id,
                subject=subject,
                message=message
            ).order_by('-created_at')
            
            # Garder la plus récente, supprimer les autres
            to_delete = duplicate_notifications[1:]  # Garder le premier (plus récent)
            
            if to_delete.exists():
                count = to_delete.count()
                total_deleted += count
                
                if dry_run:
                    self.stdout.write(f"🔍 SIMULATION: Supprimerait {count} notifications pour le message: {subject[:50]}...")
                else:
                    to_delete.delete()
                    self.stdout.write(self.style.SUCCESS(f"✅ Supprimé {count} notifications en double: {subject[:50]}..."))
        
        if dry_run:
            self.stdout.write(f"🔍 SIMULATION: Total à supprimer: {total_deleted} notifications")
        else:
            self.stdout.write(self.style.SUCCESS(f"🎯 Total supprimé: {total_deleted} notifications en double"))
        
        # Afficher les statistiques après nettoyage
        if not dry_run:
            remaining = notifications.count()
            self.stdout.write(f"📊 Notifications restantes: {remaining}")
