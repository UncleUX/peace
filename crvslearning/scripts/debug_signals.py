#!/usr/bin/env python
"""
Script pour debugger les signaux d'assignation automatique
"""

import subprocess
import sys

def debug_signals():
    """Debug des signaux"""
    
    script = '''
from django.contrib.auth import get_user_model
from courses.models import LearningPath, LearningPathTemplate
from django.db.models.signals import post_save
from django.dispatch import receiver

User = get_user_model()

print("=== DEBUG DES SIGNAUX ===")

# 1. Verifier si les signaux sont connectes
print("\\n1. Verification des signaux connectes:")
from django.dispatch import Signal
from courses.signals import create_learning_path, assign_learning_path_template

print(f"Signal create_learning_path: {create_learning_path}")
print(f"Signal assign_learning_path_template: {assign_learning_path_template}")

# 2. Creer un utilisateur de test
print("\\n2. Creation utilisateur de test...")
try:
    test_user = User.objects.create_user(
        username='debug_user_123',
        email='debug@example.com',
        password='test123',
        structure='commune'
    )
    print(f"Utilisateur cree: {test_user.username}")
    print(f"Structure: {test_user.structure}")
except Exception as e:
    print(f"Erreur creation utilisateur: {e}")

# 3. Verifier si LearningPath a ete cree
print("\\n3. Verification LearningPath:")
try:
    lp = LearningPath.objects.get(user=test_user)
    print(f"LearningPath trouve: {lp}")
    print(f"Template assigne: {lp.template}")
except LearningPath.DoesNotExist:
    print("Aucun LearningPath trouve")
except Exception as e:
    print(f"Erreur verification LearningPath: {e}")

# 4. Verifier les templates disponibles
print("\\n4. Templates disponibles pour structure 'commune':")
templates = LearningPathTemplate.objects.filter(
    structure='commune',
    is_active=True
)
print(f"Templates principaux: {templates.count()}")
for t in templates:
    print(f"  - {t.name}")

additional_templates = LearningPathTemplate.objects.filter(
    is_active=True
).filter(additional_structures__icontains='commune')
print(f"Templates additionnels: {additional_templates.count()}")
for t in additional_templates:
    print(f"  - {t.name} (additionnels: {t.additional_structures})")

# 5. Forcer manuellement le signal
print("\\n5. Test manuel du signal:")
try:
    from courses.signals import assign_learning_path_template
    assign_learning_path_template(sender=User, instance=test_user, created=True)
    print("Signal execute manuellement")
except Exception as e:
    print(f"Erreur signal manuel: {e}")
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
    debug_signals()
