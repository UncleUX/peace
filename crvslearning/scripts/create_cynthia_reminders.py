#!/usr/bin/env python

import os
import sys

# Ajouter le chemin du projet
sys.path.append('e:/ELEARNING/crvslearning')

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crvslearning.settings')

import django
django.setup()

from django.contrib.auth.models import User
from tracking.models import CourseReminder, LearnerProgress
from courses.models import Course
from django.utils import timezone

def create_cynthia_reminders():
    print("🔧 CRÉATION DE RAPPELS POUR cynthia.essomba")
    print("=" * 60)
    
    try:
        # 1. Vérifier l'utilisateur
        user = User.objects.get(username='cynthia.essomba')
        print(f"✅ Utilisateur trouvé: {user.username} (ID: {user.id})")
        
        # 2. Trouver le cours "CADRE REGLEMENTAIRE ET LEGISLATIF"
        course = Course.objects.filter(title__icontains="cadre").first()
        if not course:
            # Prendre le premier cours disponible
            course = Course.objects.first()
            print(f"⚠️ Cours 'cadre' non trouvé, utilisation du premier cours: {course.title}")
        else:
            print(f"✅ Cours trouvé: {course.title} (ID: {course.id})")
        
        # 3. Créer ou mettre à jour la progression
        progress, created = LearnerProgress.objects.get_or_create(
            user=user,
            course=course,
            defaults={
                'completion_percentage': 35.0,
                'is_completed': False,
                'last_accessed': timezone.now() - timezone.timedelta(days=5),
                'current_lesson': None
            }
        )
        
        if created:
            print(f"✅ Progression créée: {course.title} - 35%")
        else:
            print(f"📝 Progression mise à jour: {course.title} - 35%")
        
        # 4. Créer ou mettre à jour le rappel
        reminder, created = CourseReminder.objects.get_or_create(
            user=user,
            course=course,
            defaults={
                'progress_percentage': 35.0,
                'is_active': True,
                'last_activity': timezone.now() - timezone.timedelta(days=5),
                'current_lesson': None,
                'reminder_count': 0
            }
        )
        
        if created:
            print(f"✅ Rappel créé: {course.title} - 35%")
        else:
            print(f"📝 Rappel mis à jour: {course.title} - 35%")
        
        # 5. Mettre à jour les dates pour forcer le rappel
        progress.last_accessed = timezone.now() - timezone.timedelta(days=5)
        progress.save()
        
        reminder.last_activity = timezone.now() - timezone.timedelta(days=5)
        reminder.save()
        
        print(f"📅 Dates mises à jour: activité il y a 5 jours")
        
        # 6. Vérifier le résultat
        print(f"\n🎯 VÉRIFICATION FINALE:")
        print(f"   Utilisateur: {user.username}")
        print(f"   Cours: {course.title} (ID: {course.id})")
        print(f"   Progression: 35%")
        print(f"   Rappel actif: {reminder.is_active}")
        print(f"   Doit rappeler immédiatement: {reminder.should_remind_immediately()}")
        print(f"   URL du cours: /courses/{course.id}/")
        
        print(f"\n🚀 RAPPELS CRÉÉS AVEC SUCCÈS !")
        print(f"   cynthia.essomba devrait maintenant voir le popup")
        print(f"   avec redirection vers /courses/{course.id}/")
        
    except User.DoesNotExist:
        print("❌ Utilisateur cynthia.essomba non trouvé")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_cynthia_reminders()
