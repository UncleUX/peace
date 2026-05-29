from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.core.files.storage import default_storage
from .models import Notification

User = get_user_model()

@staff_member_required
def send_notification_form(request):
    """Vue pour envoyer une notification depuis l'admin"""
    if request.method == 'POST':
        username = request.POST.get('username')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        url = request.POST.get('url', '/dashboard/')
        sender = request.POST.get('sender', 'Administration CRVS')
        
        if username == 'all':
            # Envoyer à tous les utilisateurs
            users = User.objects.all()
            count = 0
            for user in users:
                Notification.objects.create(
                    user=user,
                    subject=subject,
                    message=message,
                    url=url,
                    created_at=timezone.now()
                )
                count += 1
            messages.success(request, f"✅ Notification envoyée à {count} utilisateurs")
        else:
            # Envoyer à un utilisateur spécifique
            try:
                user = User.objects.get(username=username)
                Notification.objects.create(
                    user=user,
                    subject=subject,
                    message=message,
                    url=url,
                    created_at=timezone.now()
                )
                messages.success(request, f"✅ Notification envoyée à {user.get_full_name() or user.username}")
            except User.DoesNotExist:
                messages.error(request, f"❌ Utilisateur '{username}' non trouvé")
        
        return HttpResponseRedirect(reverse('admin:notifications_notification_changelist'))
    
    return render(request, 'admin/send_notification.html')

@staff_member_required
def bulk_notification_form(request):
    """Vue pour envoyer des notifications en masse"""
    if request.method == 'POST':
        usernames = request.POST.getlist('usernames', [])
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        url = request.POST.get('url', '/dashboard/')
        sender = request.POST.get('sender', 'Administration CRVS')
        
        count = 0
        for username in usernames:
            try:
                user = User.objects.get(username=username)
                Notification.objects.create(
                    user=user,
                    subject=subject,
                    message=message,
                    url=url,
                    created_at=timezone.now()
                )
                count += 1
            except User.DoesNotExist:
                continue
        
        messages.success(request, f"✅ {count} notifications envoyées avec succès")
        return HttpResponseRedirect(reverse('admin:notifications_notification_changelist'))
    
    # Récupérer tous les utilisateurs pour le formulaire
    users = User.objects.all().order_by('username')
    return render(request, 'admin/bulk_notification.html', {'users': users})

@staff_member_required
def notification_with_attachment_form(request):
    """Vue pour envoyer une notification avec pièce jointe"""
    if request.method == 'POST':
        username = request.POST.get('username')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        url = request.POST.get('url', '/dashboard/')
        sender = request.POST.get('sender', 'Administration CRVS')
        attachment = request.FILES.get('attachment')
        
        if username == 'all':
            # Envoyer à tous les utilisateurs
            users = User.objects.all()
            count = 0
            for user in users:
                notification = Notification.objects.create(
                    user=user,
                    subject=subject,
                    message=message,
                    url=url,
                    created_at=timezone.now()
                )
                # Ajouter la pièce jointe si fournie
                if attachment:
                    notification.attachment = attachment
                    notification.save()
                count += 1
            messages.success(request, f"✅ Notification avec pièce jointe envoyée à {count} utilisateurs")
        else:
            # Envoyer à un utilisateur spécifique
            try:
                user = User.objects.get(username=username)
                notification = Notification.objects.create(
                    user=user,
                    subject=subject,
                    message=message,
                    url=url,
                    created_at=timezone.now()
                )
                # Ajouter la pièce jointe si fournie
                if attachment:
                    notification.attachment = attachment
                    notification.save()
                    
                messages.success(request, f"✅ Notification avec pièce jointe envoyée à {user.get_full_name() or user.username}")
            except User.DoesNotExist:
                messages.error(request, f"❌ Utilisateur '{username}' non trouvé")
        
        return HttpResponseRedirect(reverse('admin:notifications_notification_changelist'))
    
    return render(request, 'admin/notification_with_attachment.html')

@staff_member_required
def bulk_notification_with_attachment_form(request):
    """Vue pour envoyer des notifications en masse avec pièces jointes"""
    if request.method == 'POST':
        usernames = request.POST.getlist('usernames', [])
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        url = request.POST.get('url', '/dashboard/')
        sender = request.POST.get('sender', 'Administration CRVS')
        attachment = request.FILES.get('attachment')
        
        count = 0
        for username in usernames:
            try:
                user = User.objects.get(username=username)
                notification = Notification.objects.create(
                    user=user,
                    subject=subject,
                    message=message,
                    url=url,
                    created_at=timezone.now()
                )
                # Ajouter la pièce jointe si fournie
                if attachment:
                    notification.attachment = attachment
                    notification.save()
                count += 1
            except User.DoesNotExist:
                continue
        
        messages.success(request, f"✅ {count} notifications avec pièces jointes envoyées avec succès")
        return HttpResponseRedirect(reverse('admin:notifications_notification_changelist'))
    
    # Récupérer tous les utilisateurs pour le formulaire
    users = User.objects.all().order_by('username')
    return render(request, 'admin/bulk_notification_with_attachment.html', {'users': users})
