#!/usr/bin/env python
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crvslearning.settings')
django.setup()

from django.contrib.auth.models import User
from tracking.models import CourseReminder, LearnerProgress
from courses.models import Course

def check_cynthia_reminders():
    """Vérifier les rappels de cynthia.essomba"""
    
    print("🔍 Vérification des rappels pour cynthia.essomba")
    print("=" * 60)
    
    try:
        # Vérifier l'utilisateur
        user = User.objects.get(username='cynthia.essomba')
        print(f"✅ Utilisateur trouvé: {user.username} (ID: {user.id})")
        
        # Vérifier les progressions
        progressions = LearnerProgress.objects.filter(user=user)
        print(f"\n📚 Progressions trouvées: {progressions.count()}")
        
        for progress in progressions:
            print(f"   - Cours: {progress.course.title} (ID: {progress.course.id})")
            print(f"     Progression: {progress.completion_percentage}%")
            print(f"     Dernier accès: {progress.last_accessed}")
            print(f"     Complété: {progress.is_completed}")
        
        # Vérifier les rappels
        reminders = CourseReminder.objects.filter(user=user)
        print(f"\n🔔 Rappels trouvés: {reminders.count()}")
        
        for reminder in reminders:
            print(f"   - Cours: {reminder.course.title} (ID: {reminder.course.id})")
            print(f"     Progression: {reminder.progress_percentage}%")
            print(f"     Actif: {reminder.is_active}")
            print(f"     Dernière activité: {reminder.last_activity}")
            print(f"     Doit rappeler immédiatement: {reminder.should_remind_immediately()}")
            print(f"     Doit rappeler (3 jours): {reminder.should_remind()}")
        
        # Vérifier les cours disponibles
        all_courses = Course.objects.all()
        print(f"\n📋 Tous les cours disponibles: {all_courses.count()}")
        
        for course in all_courses:
            print(f"   - {course.title} (ID: {course.id})")
        
        # Test de l'API
        print(f"\n🌐 Test de l'API pour cynthia.essomba:")
        from django.test import Client
        client = Client()
        
        # Simuler une connexion
        user_client = Client()
        user_client.force_login(user)
        
        response = user_client.get('/tracking/api/reminders/')
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Données retournées: {data}")
            if data.get('reminders'):
                for i, reminder in enumerate(data['reminders']):
                    print(f"   Rappel {i+1}:")
                    print(f"     - Course ID: {reminder.get('course_id')}")
                    print(f"     - Course Title: {reminder.get('course_title')}")
                    print(f"     - Progress: {reminder.get('progress_percentage')}%")
        else:
            print(f"   Erreur: {response.content}")
            
    except User.DoesNotExist:
        print("❌ Utilisateur cynthia.essomba non trouvé")
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    check_cynthia_reminders()
