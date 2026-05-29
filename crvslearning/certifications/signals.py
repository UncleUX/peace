"""
Signaux pour la gestion automatique des certifications
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from courses.models import LearningPath, CourseCompletion
from .utils import generate_automatic_certification, check_certification_eligibility

# Variable globale pour éviter les notifications multiples
CERTIFICATION_NOTIFICATION_CACHE = {}

# Dernier nettoyage du cache
LAST_CACHE_CLEANUP = None

def cleanup_notification_cache():
    """Nettoie le cache des notifications anciennes"""
    import datetime
    from django.utils import timezone
    
    global LAST_CACHE_CLEANUP
    now = timezone.now()
    
    # Nettoyer toutes les heures ou si le cache fait plus de 50 entrées
    should_cleanup = (
        LAST_CACHE_CLEANUP is None or 
        (now - LAST_CACHE_CLEANUP).seconds > 3600 or  # 1 heure
        len(CERTIFICATION_NOTIFICATION_CACHE) > 50  # 50 entrées max
    )
    
    if not should_cleanup:
        return
    
    keys_to_remove = []
    
    for key, timestamp in CERTIFICATION_NOTIFICATION_CACHE.items():
        # Supprimer les entrées de plus de 5 minutes
        if (now - timestamp).seconds > 300:
            keys_to_remove.append(key)
    
    for key in keys_to_remove:
        del CERTIFICATION_NOTIFICATION_CACHE[key]
    
    LAST_CACHE_CLEANUP = now
    
    if keys_to_remove:
        print(f"🧹 Nettoyage du cache notifications: {len(keys_to_remove)} entrées supprimées")
        print(f"📊 Cache restant: {len(CERTIFICATION_NOTIFICATION_CACHE)} entrées")
    else:
        print(f"🧹 Nettoyage du cache: aucune entrée à supprimer")

def should_send_notification(user, template):
    """
    Vérifie si une notification de certification doit être envoyée
    en vérifiant à la fois le cache en mémoire et la base de données
    """
    from django.utils import timezone
    from datetime import timedelta
    from .models import Certification
    from notifications.models import Notification
    
    # Nettoyer le cache périodiquement
    cleanup_notification_cache()
    
    # 1. Vérifier le cache en mémoire
    cache_key = f"{user.id}_{template.id}_{template.level}"
    now = timezone.now()
    
    if cache_key in CERTIFICATION_NOTIFICATION_CACHE:
        last_notification_time = CERTIFICATION_NOTIFICATION_CACHE[cache_key]
        if (now - last_notification_time).seconds < 300:  # 5 minutes
            print(f"⏰ Notification déjà envoyée récemment (cache mémoire) pour {cache_key}")
            return False
    
    # 2. Vérifier les notifications récentes
    recent_notification = Notification.objects.filter(
        user=user,
        subject__icontains="certification",
        message__icontains=template.title or template.name,
        created_at__gte=now - timedelta(minutes=30)  # 30 minutes
    ).first()
    
    if recent_notification:
        print(f"⏰ Notification de certification déjà envoyée récemment pour {user.username}")
        return False
    
    # 3. Vérifier les certifications existantes
    recent_certification = Certification.objects.filter(
        user=user,
        template=template,
        level=template.level,
        issued_at__gte=now - timedelta(minutes=30)  # 30 minutes
    ).first()
    
    if recent_certification:
        print(f"⏰ Certification déjà existante (base de données) pour {user.username}")
        return False
    
    # 4. Ajouter au cache
    CERTIFICATION_NOTIFICATION_CACHE[cache_key] = now
    print(f"✅ Notification autorisée pour {user.username} - {template.name}")
    return True


@receiver(post_save, sender=LearningPath)
def auto_certification_on_path_update(sender, instance, created, **kwargs):
    """
    Déclenche la vérification de certification automatique 
    quand le LearningPath est mis à jour
    """
    if created:
        return  # Pas de vérification pour les nouveaux parcours
    
    # Vérifier si l'utilisateur a un template assigné
    if not instance.template:
        return
    
    # Vérifier si on doit envoyer une notification
    if not should_send_notification(instance.user, instance.template):
        return
    
    # Vérifier l'éligibilité à la certification
    eligibility, message = check_certification_eligibility(instance.user, instance)
    
    if eligibility:
        certification, result_message = generate_automatic_certification(
                instance.user, 
                instance.template
            )
        
        if certification:
            print(f"🎓 Certification automatique générée: {certification}")
            
            # Envoyer UNE SEULE notification
            from courses.notifications import send_certification_earned_notification
            send_certification_earned_notification(instance.user, certification)
        else:
            print(f"⚠️ Erreur génération certification: {result_message}")
    else:
        print(f"ℹ️ Non éligible à la certification: {message}")


@receiver(post_save, sender=CourseCompletion)
def check_certification_on_course_completion(sender, instance, created, **kwargs):
    """
    Vérifie l'éligibilité à la certification 
    après chaque complétion de cours
    """
    if not created:
        return
    
    user = instance.user
    learning_path = user.learning_path
    
    if not learning_path or not learning_path.template:
        return
    
    # Vérifier si on doit envoyer une notification
    if not should_send_notification(user, learning_path.template):
        return
    
    # Vérifier si ce cours rend l'utilisateur éligible
    eligibility, message = check_certification_eligibility(user, learning_path)
    
    if eligibility:
        certification, result_message = generate_automatic_certification(
                user, 
                learning_path.template
            )
        
        if certification:
            print(f"🎓 Certification mise à jour: {certification}")
            
            # NE PAS envoyer de notification ici pour éviter les doublons
            print(f"ℹ️ Notification gérée par le signal LearningPath (éviter doublon)")
        else:
            print(f"⚠️ Erreur mise à jour certification: {result_message}")


@receiver(post_save, sender=LearningPath)
def track_certification_progress(sender, instance, created, **kwargs):
    """
    Suit la progression vers la certification
    """
    if not instance.template:
        return
    
    # Calculer la progression actuelle
    total_courses = instance.template.courses.count()
    completed_courses = instance.completed_courses.filter(id__in=instance.template.courses.all()).count()
    
    if total_courses > 0:
        progress_percentage = (completed_courses / total_courses) * 100
        
        # Mettre à jour les métadonnées du parcours
        instance.certification_progress = progress_percentage
        instance.last_certification_check = timezone.now()
        instance.save(update_fields=['certification_progress', 'last_certification_check'])
        
        print(f"📊 Progression certification: {progress_percentage:.1f}%")
