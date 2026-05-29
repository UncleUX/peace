#!/usr/bin/env python
"""
Déclencher manuellement l'assignation pour uptime.scale
"""

import subprocess
import sys

def trigger_uptime_assignment():
    """Forcer l'assignation du template pour uptime.scale"""
    
    print("Declenchement de l'assignation pour uptime.scale...")
    
    trigger_script = '''
from django.contrib.auth import get_user_model
from courses.models import LearningPath

User = get_user_model()

# 1. Trouver uptime.scale
try:
    user = User.objects.get(username="uptime.scale")
    print(f"Utilisateur trouve: {user.username}")
    
    # 2. Forcer la mise a jour pour declencher le signal
    user.save(update_fields=["structure"])
    print("Mise a jour forcee - signal declenche")
    
    # 3. Verifier le resultat
    try:
        lp = LearningPath.objects.get(user=user)
        print(f"Template apres signal: {lp.template.name if lp.template else 'Toujours aucun'}")
        if lp.template:
            print(f"Structure template: {lp.template.structure}")
            print(f"Niveau template: {lp.template.level}")
            print(f"Cours: {lp.template.courses.count()}")
        else:
            print("Le signal n a pas fonctionne - essai manuel")
            
            # 4. Assignation manuelle directe
            from courses.models import LearningPathTemplate
            template = LearningPathTemplate.objects.filter(
                structure="commune",
                level="beginner",
                is_active=True
            ).first()
            
            if template:
                template.assign_to_user(user)
                print(f"Assignation manuelle reussie: {template.name}")
            else:
                print("Aucun template trouve pour la commune")
                
    except LearningPath.DoesNotExist:
        print("LearningPath non trouve apres signal")
        
except User.DoesNotExist:
    print("Utilisateur uptime.scale non trouve")
'''
    
    try:
        result = subprocess.run(
            ['python3', 'manage.py', 'shell', '-c', trigger_script],
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
    trigger_uptime_assignment()
