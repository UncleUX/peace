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

def check_cynthia_complete():
    print("🔍 VÉRIFICATION COMPLÈTE - cynthia.essomba")
    print("=" * 60)
    
    try:
        # 1. Vérifier l'utilisateur
        user = User.objects.get(username='cynthia.essomba')
        print(f"✅ Utilisateur: {user.username} (ID: {user.id})")
        print(f"   Role: {getattr(user, 'role', 'Non défini')}")
        
        # 2. Vérifier les progressions
        progressions = LearnerProgress.objects.filter(user=user)
        print(f"\n📚 PROGRESSIONS ({progressions.count()}):")
        
        for prog in progressions:
            print(f"   • {prog.course.title} (ID: {prog.course.id})")
            print(f"     Progression: {prog.completion_percentage}%")
            print(f"     Complété: {prog.is_completed}")
            print(f"     Dernier accès: {prog.last_accessed}")
            print(f"     Actif: {not prog.is_completed}")
        
        # 3. Vérifier les rappels
        reminders = CourseReminder.objects.filter(user=user)
        print(f"\n🔔 RAPPELS ({reminders.count()}):")
        
        for reminder in reminders:
            print(f"   • {reminder.course.title} (ID: {reminder.course.id})")
            print(f"     Progression: {reminder.progress_percentage}%")
            print(f"     Actif: {reminder.is_active}")
            print(f"     Dernière activité: {reminder.last_activity}")
            print(f"     Doit rappeler immédiatement: {reminder.should_remind_immediately()}")
            print(f"     Doit rappeler (3 jours): {reminder.should_remind()}")
        
        # 4. Vérifier les cours disponibles
        courses = Course.objects.all()
        print(f"\n📋 TOUS LES COURS DISPONIBLES ({courses.count()}):")
        
        for course in courses:
            print(f"   • {course.title} (ID: {course.id})")
        
        # 5. Déterminer quel cours cynthia devrait reprendre
        print(f"\n🎯 ANALYSE POUR CYNTHIA.ESSOMBA:")
        
        if reminders.exists():
            reminder = reminders.first()
            print(f"   ✅ Rappel trouvé: {reminder.course.title} (ID: {reminder.course.id})")
            print(f"   📊 Progression: {reminder.progress_percentage}%")
            print(f"   🔗 URL: /courses/{reminder.course.id}/")
            print(f"   🎯 CIBLE PRINCIPALE: Ce cours")
            
        elif progressions.exists():
            prog = progressions.filter(is_completed=False).first()
            if prog:
                print(f"   ✅ Progression trouvée: {prog.course.title} (ID: {prog.course.id})")
                print(f"   📊 Progression: {prog.completion_percentage}%")
                print(f"   🔗 URL: /courses/{prog.course.id}/")
                print(f"   🎯 CIBLE PRINCIPALE: Ce cours")
            else:
                print(f"   ❌ Toutes les progressions sont complétées")
        else:
            print(f"   ❌ Aucune progression ni rappel trouvé")
        
        # 6. Vérifier si "CADRE REGLEMENTAIRE ET LEGISLATIF" existe
        cadre_course = Course.objects.filter(title__icontains="cadre").first()
        if cadre_course:
            print(f"\n📋 COURS 'CADRE' TROUVÉS:")
            for course in Course.objects.filter(title__icontains="cadre"):
                print(f"   • {course.title} (ID: {course.id})")
        else:
            print(f"\n❌ Aucun cours avec 'cadre' dans le titre trouvé")
            
    except User.DoesNotExist:
        print("❌ Utilisateur cynthia.essomba non trouvé")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_cynthia_complete()
