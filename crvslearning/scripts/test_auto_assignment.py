#!/usr/bin/env python
"""
Script pour tester l'assignation automatique
"""

import subprocess
import sys

def test_auto_assignment():
    """Tester l'assignation automatique pour différentes structures"""
    
    print("🧪 Test de l'assignation automatique")
    print("=" * 50)
    
    # Test pour un utilisateur de la commune
    test_script = '''
from django.contrib.auth import get_user_model
from courses.models import LearningPath, LearningPathTemplate, Enrollment
from courses.views_learning_path import try_auto_assignment

User = get_user_model()

# Test 1: Utilisateur de la commune sans parcours
try:
    # Créer un utilisateur de test si nécessaire
    user, created = User.objects.get_or_create(
        username='test_commune',
        defaults={
            'email': 'test@commune.com',
            'structure': 'commune',
            'first_name': 'Test',
            'last_name': 'Commune'
        }
    )
    
    if created:
        print(f"✅ Utilisateur de test créé: {user.username}")
    
    # Supprimer son LearningPath existant pour le test
    LearningPath.objects.filter(user=user).delete()
    Enrollment.objects.filter(user=user).delete()
    print("🗑️ Anciennes données supprimées pour le test")
    
    # Tester l'assignation automatique
    assigned_template = try_auto_assignment(user)
    
    if assigned_template:
        print(f"✅ Auto-assignation réussie: {assigned_template.name}")
        
        # Vérifier les inscriptions
        enrollments = Enrollment.objects.filter(user=user)
        print(f"📚 Inscriptions: {enrollments.count()} cours")
        
        # Vérifier le LearningPath
        learning_path = user.learning_path
        print(f"🎯 Template assigné: {learning_path.template.name if learning_path.template else 'None'}")
        print(f"📖 Cours actuel: {learning_path.current_course.title if learning_path.current_course else 'None'}")
        
    else:
        print("❌ Auto-assignation échouée")
        
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
'''
    
    # Exécuter le test
    try:
        result = subprocess.run(
            ['python', 'manage.py', 'shell', '-c', test_script],
            cwd='crvslearning',
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print("Résultat du test:")
        print(result.stdout)
        if result.stderr:
            print("Erreurs:")
            print(result.stderr)
            
    except Exception as e:
        print(f"❌ Erreur d'exécution: {e}")

if __name__ == "__main__":
    test_auto_assignment()
