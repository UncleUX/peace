from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from chat.models import UserStatus

class Command(BaseCommand):
    help = 'Marque les utilisateurs comme hors ligne après inactivité'
    
    def handle(self, *args, **options):
        # Marquer comme hors ligne les utilisateurs inactifs depuis 5 minutes
        threshold = timezone.now() - timedelta(minutes=5)
        
        offline_users = UserStatus.objects.filter(
            last_seen__lt=threshold,
            is_online=True
        )
        
        count = offline_users.count()
        offline_users.update(is_online=False)
        
        self.stdout.write(
            self.style.SUCCESS(f'{count} utilisateurs marqués comme hors ligne')
        )
