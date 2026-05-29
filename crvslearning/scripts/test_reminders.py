#!/usr/bin/env python
"""
Script de test pour créer des rappels de cours et vérifier le système
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
from django.utils import timezone
from datetime import timedelta
from tracking.models import CourseReminder, LearnerProgress
from courses.models import Course, Lesson, Module

User = get_user_model()

def create_reminders_for_all_learners():
    """Crée des rappels pour TOUS les utilisateurs apprenants"""
    print("🎓 Création de rappels pour tous les apprenants...")
    
    try:
        # Récupérer tous les utilisateurs avec le rôle 'apprenant'
        learners = User.objects.filter(role='learner')
        print(f"📊 Nombre d'apprenants trouvés : {learners.count()}")
        
        if learners.count() == 0:
            print("❌ Aucun apprenant trouvé. Création d'un apprenant de test...")
            learner = User.objects.create_user(
                username='apprenant_test',
                email='learner@test.com',
                password='testpass123',
                role='learner'
            )
            learners = User.objects.filter(role='learner')
            print(f"✅ Apprenant de test créé : {learner.username}")
        
        total_reminders_created = 0
        
        for learner in learners:
            print(f"\n👤 Traitement de l'apprenant : {learner.username}")
            
            # Récupérer toutes les progressions incomplètes de cet apprenant
            incomplete_progress = LearnerProgress.objects.filter(
                user=learner,
                completion_percentage__lt=100,
                completion_percentage__gt=0  # Seulement les cours commencés
            ).select_related('course')
            
            print(f"   📚 Cours inachevés : {incomplete_progress.count()}")
            
            if incomplete_progress.count() == 0:
                # Si aucun cours inachevé, créer une progression de test
                course = Course.objects.first()
                if course:
                    learner_progress, created = LearnerProgress.objects.get_or_create(
                        user=learner,
                        course=course,
                        defaults={
                            'completion_percentage': 35.0,
                            'last_accessed': timezone.now() - timedelta(days=2),
                            'is_completed': False
                        }
                    )
                    if created:
                        print(f"   ✅ Progression de test créée : {course.title}")
                    incomplete_progress = LearnerProgress.objects.filter(
                        user=learner,
                        completion_percentage__lt=100
                    ).select_related('course')
            
            # Créer des rappels pour chaque cours inachevé
            for progress in incomplete_progress:
                reminder = CourseReminder.update_or_create_reminder(
                    user=learner,
                    course=progress.course
                )
                
                # Forcer une date d'activité passée pour le test
                reminder.last_activity = timezone.now() - timedelta(days=2)
                reminder.save()
                
                print(f"   🔔 Rappel créé : {progress.course.title} ({progress.completion_percentage}%)")
                total_reminders_created += 1
        
        print(f"\n✅ Total de rappels créés : {total_reminders_created}")
        return total_reminders_created
        
    except Exception as e:
        print(f"❌ Erreur lors de la création des rappels : {str(e)}")
        return 0

def test_reminder_logic():
    """Test la logique des rappels"""
    print("\n🧪 Test de la logique des rappels...")
    
    try:
        # Récupérer tous les rappels
        reminders = CourseReminder.objects.all()
        print(f"📊 Nombre total de rappels : {reminders.count()}")
        
        for reminder in reminders:
            print(f"\n🔔 Rappel : {reminder}")
            print(f"   - Utilisateur : {reminder.user.username}")
            print(f"   - Cours : {reminder.course.title}")
            print(f"   - Progression : {reminder.progress_percentage}%")
            print(f"   - Actif : {reminder.is_active}")
            print(f"   - Doit rappeler : {reminder.should_remind(days_threshold=3)}")
            
            # Tester la prochaine leçon
            next_lesson = reminder.get_next_lesson()
            if next_lesson:
                print(f"   - Prochaine leçon : {next_lesson.title}")
            else:
                print(f"   - Prochaine leçon : Non définie")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test : {str(e)}")
        return False

def check_middleware_integration():
    """Vérifie l'intégration des middlewares"""
    print("\n⚙️ Vérification des middlewares...")
    
    try:
        from crvslearning.settings import MIDDLEWARE
        
        required_middlewares = [
            'tracking.middleware.ActivityTrackingMiddleware',
            'tracking.middleware.CourseReminderMiddleware'
        ]
        
        for middleware in required_middlewares:
            if middleware in MIDDLEWARE:
                print(f"✅ {middleware}")
            else:
                print(f"❌ {middleware} - MANQUANT")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification : {str(e)}")
        return False

def main():
    """Fonction principale de test"""
    print("🚀 Démarrage du test du système de rappels universel...")
    
    # 1. Créer des rappels pour TOUS les apprenants
    total_reminders = create_reminders_for_all_learners()
    
    # 2. Tester la logique
    test_reminder_logic()
    
    # 3. Vérifier les middlewares
    check_middleware_integration()
    
    # 4. Instructions pour l'utilisateur
    print("\n📋 Instructions pour tester l'interface :")
    print("1. Démarrez le serveur Django : python manage.py runserver")
    print("2. Connectez-vous avec N'IMPORTE QUEL utilisateur apprenant")
    print("3. Allez sur votre profil : /users/profile/")
    print("4. Vous devriez voir les popups de rappel pour vos cours inachevés !")
    
    print(f"\n🎯 Système universel créé :")
    print(f"   - Total de rappels créés : {total_reminders}")
    print(f"   - Pour TOUS les utilisateurs avec role='apprenant'")
    print(f"   - Chaque apprenant voit où il s'est arrêté")
    print(f"   - Chaque apprenant sait où reprendre")

if __name__ == '__main__':
    main()
