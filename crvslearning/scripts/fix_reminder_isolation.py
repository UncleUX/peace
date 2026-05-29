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

def fix_reminder_isolation():
    print("🔧 CORRECTION DE L'ISOLATION DES RAPPELS")
    print("=" * 60)
    
    try:
        # 1. Nettoyer tous les rappels existants
        print("🗑️ Suppression de tous les rappels existants...")
        deleted_count, _ = CourseReminder.objects.all().delete()
        print(f"   ✅ {deleted_count} rappels supprimés")
        
        # 2. Créer des rappels corrects pour chaque utilisateur
        print("\n📚 Création des rappels corrects...")
        
        # Récupérer tous les utilisateurs avec des progressions
        users_with_progress = LearnerProgress.objects.filter(
            is_completed=False,
            completion_percentage__gt=0,
            completion_percentage__lt=100
        ).select_related('user', 'course').values('user_id', 'course_id', 'completion_percentage').distinct()
        
        print(f"   📊 Utilisateurs avec progressions incomplètes: {users_with_progress.count()}")
        
        for progress_data in users_with_progress:
            user_id = progress_data['user_id']
            course_id = progress_data['course_id']
            completion_percentage = progress_data['completion_percentage']
            
            # Récupérer les objets complets
            user = User.objects.get(id=user_id)
            course = Course.objects.get(id=course_id)
            
            # Créer un rappel correct
            reminder = CourseReminder.objects.create(
                user=user,
                course=course,
                progress_percentage=completion_percentage,
                is_active=True,
                last_activity=timezone.now() - timezone.timedelta(days=3),
                reminder_count=0
            )
            
            print(f"   ✅ Rappel créé: {user.username} → {course.title} ({completion_percentage}%)")
        
        # 3. Vérification finale
        print("\n🔍 VÉRIFICATION FINALE:")
        all_reminders = CourseReminder.objects.all()
        print(f"   📊 Total rappels: {all_reminders.count()}")
        
        for reminder in all_reminders:
            print(f"   • {reminder.user.username} → {reminder.course.title} ({reminder.progress_percentage}%)")
        
        print(f"\n✅ Isolation corrigée avec succès !")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_reminder_isolation()
