"""
Context processor pour les notifications
"""

def notifications(request):
    """
    Ajoute les notifications non lues au contexte de tous les templates
    """
    if request.user.is_authenticated:
        from .models import Notification
        
        unread_notifications = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).order_by('-created_at')[:5]  # 5 dernières notifications non lues
        
        unread_count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
        
        return {
            'unread_notifications': unread_notifications,
            'unread_notifications_count': unread_count,
        }
    
    return {
        'unread_notifications': [],
        'unread_notifications_count': 0,
    }
