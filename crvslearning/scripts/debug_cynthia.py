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

def debug_cynthia():
    print("🔍 DIAGNOSTIC COMPLET - cynthia.essomba")
    print("=" * 60)
    
    try:
        # 1. Vérifier l'utilisateur
        user = User.objects.get(username='cynthia.essomba')
        print(f"✅ Utilisateur: {user.username} (ID: {user.id}, Role: {user.role})")
        
        # 2. Vérifier les progressions
        progressions = LearnerProgress.objects.filter(user=user)
        print(f"\n📚 Progressions ({progressions.count()}):")
        
        for prog in progressions:
            print(f"   • {prog.course.title} (ID: {prog.course.id})")
            print(f"     Progression: {prog.completion_percentage}%")
            print(f"     Dernier accès: {prog.last_accessed}")
            print(f"     Complété: {prog.is_completed}")
        
        # 3. Vérifier les rappels
        reminders = CourseReminder.objects.filter(user=user)
        print(f"\n🔔 Rappels ({reminders.count()}):")
        
        for reminder in reminders:
            print(f"   • {reminder.course.title} (ID: {reminder.course.id})")
            print(f"     Progression: {reminder.progress_percentage}%")
            print(f"     Actif: {reminder.is_active}")
            print(f"     Dernière activité: {reminder.last_activity}")
            print(f"     Doit rappeler immédiatement: {reminder.should_remind_immediately()}")
        
        # 4. Vérifier les cours disponibles
        courses = Course.objects.all()
        print(f"\n📋 Tous les cours disponibles ({courses.count()}):")
        
        for course in courses:
            print(f"   • {course.title} (ID: {course.id})")
        
        # 5. Trouver le premier cours existant
        if courses.exists():
            first_course = courses.first()
            print(f"\n🎯 Premier cours trouvé: {first_course.title} (ID: {first_course.id})")
            print(f"   URL du cours: /courses/{first_course.id}/")
        
        # 6. Vérifier quel cours cynthia devrait reprendre
        if reminders.exists():
            reminder = reminders.first()
            print(f"\n🚀 Cours à reprendre selon les rappels:")
            print(f"   • {reminder.course.title} (ID: {reminder.course.id})")
            print(f"   • URL: /courses/{reminder.course.id}/")
        elif progressions.exists():
            prog = progressions.first()
            print(f"\n🚀 Cours à reprendre selon les progressions:")
            print(f"   • {prog.course.title} (ID: {prog.course.id})")
            print(f"   • URL: /courses/{prog.course.id}/")
        else:
            print(f"\n❌ Aucun cours à reprendre trouvé")
            
    except User.DoesNotExist:
        print("❌ Utilisateur cynthia.essomba non trouvé")
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    debug_cynthia()
