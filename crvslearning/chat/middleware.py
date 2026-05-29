from django.utils import timezone
from .models import UserStatus

class UserOnlineMiddleware:
    """Middleware pour suivre les utilisateurs réellement en ligne"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Traiter la requête
        response = self.get_response(request)
        
        # Mettre à jour le statut de l'utilisateur connecté
        if request.user.is_authenticated:
            user_status, created = UserStatus.objects.get_or_create(
                user=request.user,
                defaults={'is_online': True, 'last_seen': timezone.now()}
            )
            
            # Mettre à jour le statut en ligne
            user_status.is_online = True
            user_status.last_seen = timezone.now()
            user_status.save(update_fields=['is_online', 'last_seen'])
        
        return response
