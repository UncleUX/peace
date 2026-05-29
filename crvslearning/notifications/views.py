from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from .models import Notification

User = get_user_model()

@login_required
def notification_list(request):
    notifications = request.user.notifications.all().order_by('-created_at')
    unread_count = request.user.notifications.filter(is_read=False).count()
    read_count = request.user.notifications.filter(is_read=True).count()
    
    # Gestion des filtres
    current_filter = request.GET.get('filter', 'all')
    current_filter_title = "Toutes les notifications"
    
    if current_filter == 'unread':
        notifications = notifications.filter(is_read=False)
        current_filter_title = "Notifications non lues"
    elif current_filter == 'read':
        notifications = notifications.filter(is_read=True)
        current_filter_title = "Notifications lues"
    elif current_filter == 'certifications':
        notifications = notifications.filter(message__icontains='certification')
        current_filter_title = "Certifications"
    elif current_filter == 'courses':
        notifications = notifications.filter(message__icontains='cours')
        current_filter_title = "Cours"
    elif current_filter == 'system':
        notifications = notifications.filter(message__icontains='système')
        current_filter_title = "Système"
    elif current_filter == 'important':
        notifications = notifications.filter(is_read=False)  # Pour l'instant, les non lues sont importantes
        current_filter_title = "Important"
    elif current_filter == 'archived':
        notifications = notifications.none()  # Pour l'instant, aucune archive
        current_filter_title = "Archivées"
    
    # Comptes pour chaque catégorie
    certifications_count = request.user.notifications.filter(message__icontains='certification').count()
    courses_count = request.user.notifications.filter(message__icontains='cours').count()
    system_count = request.user.notifications.filter(message__icontains='système').count()
    important_count = request.user.notifications.filter(is_read=False).count()
    archived_count = 0  # Pour l'instant
    
    total_count = request.user.notifications.count()
    
    return render(request, 'notifications/notifications_list.html', {
        'notifications': notifications,
        'unread_count': unread_count,
        'read_count': read_count,
        'total_count': total_count,
        'current_filter': current_filter,
        'current_filter_title': current_filter_title,
        'certifications_count': certifications_count,
        'courses_count': courses_count,
        'system_count': system_count,
        'important_count': important_count,
        'archived_count': archived_count,
    })

@login_required
def mark_as_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return redirect(notification.url or 'home')

@login_required
@require_POST
@csrf_protect
def delete_notification(request, notification_id):
    """Supprime une notification spécifique"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.delete()
    
    # Rediriger vers la liste des notifications
    return redirect('notifications:list')

@login_required
@require_POST
@csrf_protect
def delete_selected_notifications(request):
    """Supprime les notifications sélectionnées"""
    notification_ids = request.POST.getlist('notification_ids')
    if notification_ids:
        Notification.objects.filter(
            id__in=notification_ids,
            user=request.user
        ).delete()
    
    return redirect('notifications:list')

@login_required
@csrf_protect
def mark_all_as_read(request):
    """Marque toutes les notifications comme lues"""
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return redirect('notifications:list')

@login_required
@require_POST
@csrf_protect
def clear_all_notifications(request):
    """Supprime toutes les notifications de l'utilisateur"""
    # Confirmation requise
    request.user.notifications.all().delete()
    
    return redirect('notifications:list')
