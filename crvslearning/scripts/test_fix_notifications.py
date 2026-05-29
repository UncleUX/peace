#!/usr/bin/env python
"""
Test de la correction du bug de notifications massives
"""

import subprocess
import sys

def test_fix_notifications():
    """Test de la correction"""
    
    script = '''
from django.contrib.auth import get_user_model
from courses.models import LearningPath, CourseCompletion
from django.utils import timezone

User = get_user_model()

print("=== TEST CORRECTION BUG NOTIFICATIONS ===")

# 1. Creer un nouvel utilisateur de test
username = f"test_fix_bug_{int(timezone.now().timestamp())}"
user = User.objects.create_user(
    username=username,
    email=f"{username}@example.com",
    password="test123",
    structure="commune"
)
print(f"Utilisateur créé: {username}")

# 2. Verifier l assignation automatique
from courses.models import LearningPath
lp = LearningPath.objects.get(user=user)
print(f"Template assigné: {lp.template.name if lp.template else \"Aucun\"}")

# 3. Creer un seul CourseCompletion pour tester
course = lp.template.courses.first()
completion = CourseCompletion.objects.create(
    user=user,
    course=course,
    completed_at=timezone.now()
)
print(f"CourseCompletion créé pour: {course.title}")

# 4. Compter les notifications apres ce seul cours
from notifications.models import Notification
notifications = Notification.objects.filter(user=user)
print(f"Total notifications après 1 cours: {notifications.count()}")

# 5. Afficher les notifications
for notif in notifications.order_by("-created_at"):
    print(f"  📧 {notif.subject} - {notif.created_at.strftime(\"%H:%M:%S\")}")

print("\\n=== TEST TERMINÉ ===")
print("Si vous voyez peu de notifications, le bug est corrigé !")
'''
    
    try:
        result = subprocess.run(
            ['python3', 'manage.py', 'shell', '-c', script],
            cwd='crvslearning',
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print("Resultat:")
        print(result.stdout)
        if result.stderr:
            print("Erreurs:")
            print(result.stderr)
            
    except Exception as e:
        print(f"Erreur execution: {e}")

if __name__ == "__main__":
    test_fix_notifications()
