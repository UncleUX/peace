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

def admin_fix_reminders():
    print("🔧 CORRECTION ADMINISTRATIVE DES RAPPELS")
    print("=" * 60)
    
    try:
        # 1. Trouver serge.evega
        try:
            serge_user = User.objects.get(username='serge.evega')
            print(f"👤 Utilisateur trouvé: {serge_user.username} (ID: {serge_user.id})")
        except User.DoesNotExist:
            print("❌ Utilisateur serge.evega non trouvé")
            return
        
        # 2. Supprimer TOUS les rappels de serge.evega
        serge_reminders = CourseReminder.objects.filter(user=serge_user)
        count_deleted = serge_reminders.count()
        serge_reminders.delete()
        print(f"🗑️ {count_deleted} rappels de serge.evega supprimés")
        
        # 3. Vérifier ses progressions réelles
        serge_progressions = LearnerProgress.objects.filter(
            user=serge_user,
            is_completed=False,
            completion_percentage__gt=0,
            completion_percentage__lt=100
        ).select_related('course')
        
        print(f"📊 Progressions incomplètes de serge.evega: {serge_progressions.count()}")
        
        # 4. Créer les rappels corrects uniquement pour les progressions existantes
        for progress in serge_progressions:
            print(f"   • {progress.course.title} - {progress.completion_percentage}%")
            
            # Créer un rappel correct
            reminder = CourseReminder.objects.create(
                user=serge_user,
                course=progress.course,
                progress_percentage=progress.completion_percentage,
                is_active=True,
                last_activity=timezone.now() - timezone.timedelta(days=3),
                reminder_count=0
            )
            print(f"      ✅ Rappel créé")
        
        # 5. Vérification finale
        final_reminders = CourseReminder.objects.filter(user=serge_user)
        print(f"\n🔍 VÉRIFICATION FINALE:")
        print(f"   📚 Rappels finaux de serge.evega: {final_reminders.count()}")
        
        for reminder in final_reminders:
            print(f"   • {reminder.course.title} (ID: {reminder.course.id}) - {reminder.progress_percentage}%")
        
        print(f"\n✅ Correction terminée !")
        print(f"   serge.evega n'a maintenant que les rappels de ses vrais cours")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    admin_fix_reminders()
