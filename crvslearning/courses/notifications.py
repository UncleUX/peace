"""
Notifications pour les certifications
"""

from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from certifications.models import Certification  # ✅ CORRECT - Importer depuis certifications


def send_certification_notification(user, certification):
    """
    Envoie une notification interne et email pour une certification
    AVEC DÉDOUBLONNAGE AMÉLIORÉ POUR ÉVITER LES DOUBLONS
    """
    from notifications.models import Notification
    from django.utils import timezone
    from datetime import timedelta
    
    # Vérifier si une notification similaire existe déjà (récemment)
    recent_threshold = timezone.now() - timedelta(minutes=10)  # 10 minutes
    existing_notification = Notification.objects.filter(
        user=user,
        message__contains=f"certification {certification.get_level_display()}",
        created_at__gte=recent_threshold
    ).first()
    
    if existing_notification:
        print(f"ℹ️ Notification déjà envoyée récemment pour {user.username}")
        return  # Ne pas créer de doublon
    
    # Vérifier aussi si le message contient déjà le code de certification
    code_notification = Notification.objects.filter(
        user=user,
        message__contains=certification.code,
        created_at__gte=recent_threshold
    ).first()
    
    if code_notification:
        print(f"ℹ️ Notification avec code {certification.code} déjà envoyée")
        return  # Ne pas créer de doublon
    
    # Créer la notification interne
    try:
        Notification.objects.create(
            user=user,
            message=f"🎓 Félicitations ! Vous avez obtenu la certification {certification.get_level_display()} : {certification.title}",
            url=f'/certifications/{certification.id}/'
        )
        print(f"✅ Notification interne créée pour {user.username}")
    except Exception as e:
        print(f"❌ Erreur création notification interne: {e}")
    
    # Envoyer l'email
    send_certification_earned_notification(user, certification)


def send_certification_earned_notification(user, certification):
    """
    Envoie une notification quand une certification est obtenue
    """
    from django.utils import timezone
    from datetime import timedelta
    from django.conf import settings
    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    from notifications.models import Notification  # ✅ AJOUTER CET IMPORT
    
    subject = f"🎓 Félicitations ! Certification {certification.get_level_display()} obtenue"
    
    # Vérifier si une notification similaire existe déjà (récemment)
    recent_threshold = timezone.now() - timedelta(minutes=30)  # 30 minutes
    existing_notification = Notification.objects.filter(
        user=user,
        subject__icontains="certification",
        message__contains=f"{certification.get_level_display()}",
        created_at__gte=recent_threshold
    ).first()
    
    if existing_notification:
        print(f"ℹ️ Notification de certification déjà envoyée récemment pour {user.username}")
        return  # Ne pas créer de doublon
    
    # Vérifier aussi si le message contient déjà le code de certification
    code_notification = Notification.objects.filter(
        user=user,
        message__contains=certification.code,
        created_at__gte=recent_threshold
    ).first()
    
    if code_notification:
        print(f"ℹ️ Notification avec code {certification.code} déjà envoyée")
        return  # Ne pas créer de doublon
    
    # Vérifier si une notification avec le même titre existe déjà
    title_notification = Notification.objects.filter(
        user=user,
        message__contains=certification.title,
        created_at__gte=recent_threshold
    ).first()
    
    if title_notification:
        print(f"ℹ️ Notification pour {certification.title} déjà envoyée")
        return  # Ne pas créer de doublon
    
    # Créer la notification interne
    try:
        Notification.objects.create(
            user=user,
            sender="CRVS Learning",
            subject=subject,
            message=f"🎓 Félicitations ! Vous avez obtenu la certification {certification.get_level_display()} : {certification.title}",
            url=f'/certifications/{certification.id}/'
        )
        print(f"✅ Notification interne créée pour {user.username}")
    except Exception as e:
        print(f"❌ Erreur création notification interne: {e}")
    
    # Envoyer l'email
    context = {
        'user': user,
        'certification': certification,
        'site_name': 'CRVS Learning',
        'certificate_url': f"{getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')}/certifications/download/{certification.code}/",
        'login_url': f"{getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')}/login/",
        'site_url': getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000'),
    }
    
    html_message = render_to_string('certifications/emails/certification_earned.html', context)
    text_message = render_to_string('certifications/emails/certification_earned.txt', context)
    
    try:
        send_mail(
            subject=subject,
            message=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False
        )
        print(f"✅ Email de certification envoyé à {user.email}")
    except Exception as e:
        print(f"❌ Erreur envoi email certification: {e}")


def send_certification_updated_notification(user, certification):
    """
    Envoie une notification quand une certification est mise à jour
    """
    subject = f"🔄 Certification mise à jour : {certification.title}"
    
    context = {
        'user': user,
        'certification': certification,
        'site_name': 'CRVS Learning',
    }
    
    html_message = render_to_string('certifications/emails/certification_updated.html', context)
    text_message = render_to_string('certifications/emails/certification_updated.txt', context)
    
    try:
        send_mail(
            subject=subject,
            message=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False
        )
        print(f"✅ Email de mise à jour envoyé à {user.email}")
    except Exception as e:
        print(f"❌ Erreur envoi email mise à jour: {e}")


def send_certification_reminder_notification(user, learning_path):
    """
    Envoie un rappel pour encourager à terminer le parcours
    """
    from .utils import check_certification_eligibility
    
    eligibility, message = check_certification_eligibility(user, learning_path)
    
    if not eligibility:
        return  # Pas de rappel si déjà éligible
    
    subject = "📚 Continuez votre progression vers la certification"
    
    context = {
        'user': user,
        'learning_path': learning_path,
        'message': message,
        'site_name': 'CRVS Learning',
    }
    
    html_message = render_to_string('certifications/emails/certification_reminder.html', context)
    text_message = render_to_string('certifications/emails/certification_reminder.txt', context)
    
    try:
        send_mail(
            subject=subject,
            message=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False
        )
        print(f"✅ Email de rappel envoyé à {user.email}")
    except Exception as e:
        print(f"❌ Erreur envoi email rappel: {e}")
