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

def clean_serge_reminders():
    print("🧹 NETTOYAGE DES RAPPELS INCORRECTS DE SERGE.EVEGA")
    print("=" * 60)
    
    try:
        # 1. Vérifier serge.evega
        serge_user = User.objects.get(username='serge.evega')
        print(f"👤 Utilisateur trouvé: {serge_user.username} (ID: {serge_user.id})")
        
        # 2. Lister tous les rappels de serge.evega
        serge_reminders = CourseReminder.objects.filter(user=serge_user)
        print(f"📚 Rappels actuels de serge.evega: {serge_reminders.count()}")
        
        for reminder in serge_reminders:
            print(f"   • {reminder.course.title} (ID: {reminder.course.id}) - {reminder.progress_percentage}%")
            
            # Vérifier si serge a vraiment une progression pour ce cours
            has_progress = LearnerProgress.objects.filter(
                user=serge_user,
                course=reminder.course
            ).exists()
            
            if not has_progress:
                print(f"      ❌ PAS DE PROGRESSION TROUVÉE - Suppression du rappel...")
                reminder.delete()
                print(f"      ✅ Rappel supprimé")
            else:
                progress = LearnerProgress.objects.get(user=serge_user, course=reminder.course)
                print(f"      ✅ Progression confirmée: {progress.completion_percentage}%")
        
        # 3. Vérifier les progressions réelles de serge.evega
        print(f"\n📊 Progressions réelles de serge.evega:")
        serge_progressions = LearnerProgress.objects.filter(
            user=serge_user,
            is_completed=False,
            completion_percentage__gt=0,
            completion_percentage__lt=100
        )
        
        print(f"   📈 Progressions incomplètes: {serge_progressions.count()}")
        
        for progress in serge_progressions:
            print(f"   • {progress.course.title} (ID: {progress.course.id}) - {progress.completion_percentage}%")
            
            # Créer un rappel correct s'il n'existe pas
            existing_reminder = CourseReminder.objects.filter(
                user=serge_user,
                course=progress.course
            ).exists()
            
            if not existing_reminder:
                reminder = CourseReminder.objects.create(
                    user=serge_user,
                    course=progress.course,
                    progress_percentage=progress.completion_percentage,
                    is_active=True,
                    last_activity=timezone.now() - timezone.timedelta(days=3),
                    reminder_count=0
                )
                print(f"      ✅ Rappel créé")
        
        # 4. Vérification finale
        print(f"\n🔍 VÉRIFICATION FINALE:")
        final_reminders = CourseReminder.objects.filter(user=serge_user)
        print(f"   📚 Rappels finaux de serge.evega: {final_reminders.count()}")
        
        for reminder in final_reminders:
            print(f"   • {reminder.course.title} (ID: {reminder.course.id}) - {reminder.progress_percentage}%")
        
        print(f"\n✅ Nettoyage terminé avec succès !")
        print(f"   serge.evega n'aura que les rappels de ses vrais cours")
        
    except User.DoesNotExist:
        print("❌ Utilisateur serge.evega non trouvé")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    clean_serge_reminders()
