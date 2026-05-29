#!/usr/bin/env python
"""
Script de diagnostic pour vérifier pourquoi les popups n'apparaissent pas
"""
import os
import sys
import django

# Ajouter le chemin du projet
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configurer Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crvslearning.settings')
django.setup()

from django.contrib.auth import get_user_model
from tracking.models import CourseReminder, LearnerProgress
from courses.models import Course

User = get_user_model()

def debug_reminders():
    """Diagnostic complet du système de rappels"""
    print("🔍 Diagnostic du système de rappels...")
    
    # 1. Vérifier les utilisateurs
    print("\n👤 Utilisateurs dans la base de données :")
    users = User.objects.all()
    for user in users:
        print(f"   - {user.username} (role: {user.role})")
    
    # 2. Vérifier les apprenants spécifiquement
    print("\n🎓 Apprenants (role='learner') :")
    learners = User.objects.filter(role='learner')
    for learner in learners:
        print(f"   - {learner.username}")
    
    # 3. Vérifier les progressions
    print("\n📚 Progressions des apprenants :")
    progressions = LearnerProgress.objects.filter(user__role='learner').select_related('user', 'course')
    for progress in progressions:
        print(f"   - {progress.user.username} → {progress.course.title} ({progress.completion_percentage}%)")
    
    # 4. Vérifier les rappels
    print("\n🔔 Rappels existants :")
    reminders = CourseReminder.objects.all().select_related('user', 'course')
    for reminder in reminders:
        print(f"   - {reminder.user.username} → {reminder.course.title}")
        print(f"     Progression: {reminder.progress_percentage}%")
        print(f"     Actif: {reminder.is_active}")
        print(f"     Dernière activité: {reminder.last_activity}")
        print(f"     Doit rappeler: {reminder.should_remind_immediately()}")
    
    # 5. Vérifier l'utilisateur connecté actuel (cynthia.essomba)
    print("\n🎯 Vérification pour cynthia.essomba :")
    cynthia = User.objects.filter(username='cynthia.essomba').first()
    if cynthia:
        print(f"   Utilisateur trouvé: {cynthia.username} (role: {cynthia.role})")
        
        # Ses progressions
        cynthia_progress = LearnerProgress.objects.filter(user=cynthia).select_related('course')
        print(f"   Progressions: {cynthia_progress.count()}")
        for progress in cynthia_progress:
            print(f"     - {progress.course.title} ({progress.completion_percentage}%)")
        
        # Ses rappels
        cynthia_reminders = CourseReminder.objects.filter(user=cynthia).select_related('course')
        print(f"   Rappels: {cynthia_reminders.count()}")
        for reminder in cynthia_reminders:
            print(f"     - {reminder.course.title} (actif: {reminder.is_active}, doit: {reminder.should_remind_immediately()})")
    else:
        print("   ❌ Cynthia.essomba non trouvé")
    
    # 6. Test de l'API endpoint
    print("\n🌐 Test de l'API endpoint :")
    try:
        from tracking.views import get_course_reminders
        from django.test import RequestFactory
        
        # Créer une requête factice
        factory = RequestFactory()
        request = factory.get('/tracking/api/reminders/')
        
        if cynthia:
            request.user = cynthia
            
            # Appeler la vue
            response = get_course_reminders(request)
            
            if response.status_code == 200:
                import json
                data = json.loads(response.content.decode('utf-8'))
                print(f"   ✅ API fonctionne : {len(data.get('reminders', []))} rappels retournés")
                for reminder in data.get('reminders', []):
                    print(f"     - {reminder.get('course_title')} ({reminder.get('progress_percentage')}%)")
            else:
                print(f"   ❌ API erreur : {response.status_code}")
        else:
            print("   ❌ Pas d'utilisateur pour tester l'API")
            
    except Exception as e:
        print(f"   ❌ Erreur API : {str(e)}")
    
    # 7. Instructions
    print("\n📋 Instructions de test :")
    print("1. Si vous voyez des rappels ci-dessus, le problème est JavaScript")
    print("2. Si vous ne voyez pas de rappels, exécutez: python test_reminders.py")
    print("3. Testez l'API directement: http://localhost/tracking/api/reminders/ (connecté)")

if __name__ == '__main__':
    debug_reminders()
