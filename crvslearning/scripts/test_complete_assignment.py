#!/usr/bin/env python
"""
Test complet de bout en bout de l'assignation automatique
"""

import subprocess
import sys

def test_complete_assignment():
    """Test complet d'assignation automatique"""
    
    script = '''
from django.contrib.auth import get_user_model
from courses.models import LearningPath, LearningPathTemplate
import time

User = get_user_model()

print("=== TEST COMPLET D'ASSIGNATION AUTOMATIQUE ===")

# 1. Nettoyer les utilisateurs de test
print("\\n1. Nettoyage des utilisateurs de test...")
User.objects.filter(username__startswith='test_auto_').delete()
print("Utilisateurs de test supprimes")

# 2. Verifier les templates disponibles
print("\\n2. Verification des templates disponibles...")
templates = LearningPathTemplate.objects.filter(is_active=True)
print(f"Templates actifs: {templates.count()}")
for t in templates:
    print(f"  - {t.name} (structure: {t.structure}, additionnels: {t.additional_structures})")

# 3. Creer un utilisateur pour chaque structure
test_structures = ['commune', 'minsante', 'bunec']
created_users = []

for struct in test_structures:
    username = f'test_auto_{struct}_{int(time.time())}'
    print(f"\\n3. Creation utilisateur {username} avec structure {struct}...")
    
    try:
        user = User.objects.create_user(
            username=username,
            email=f'{username}@example.com',
            password='test123',
            structure=struct
        )
        created_users.append(user)
        print(f"  ✅ Utilisateur {username} cree")
        
        # Attendre un peu pour que le signal se declenche
        time.sleep(0.5)
        
        # Verifier si le LearningPath a ete cree
        try:
            lp = LearningPath.objects.get(user=user)
            if lp.template:
                print(f"  ✅ Template assigne: {lp.template.name}")
                print(f"  ✅ Structure template: {lp.template.structure}")
                print(f"  ✅ Disponible pour {struct}: {lp.template.is_available_for_structure(struct)}")
            else:
                print(f"  ❌ Aucun template assigne")
        except LearningPath.DoesNotExist:
            print(f"  ❌ Aucun LearningPath trouve")
            
    except Exception as e:
        print(f"  ❌ Erreur creation utilisateur: {e}")

# 4. Test avec structure additionnelle
print("\\n4. Test avec structure additionnelle...")
if templates.exists():
    template = templates.first()
    template.additional_structures = 'consultant,partenaire'
    template.save()
    print(f"Template {template.name} mis a jour avec structures additionnelles: {template.additional_structures}")
    
    # Creer utilisateur avec structure additionnelle
    username = f'test_auto_consultant_{int(time.time())}'
    try:
        user = User.objects.create_user(
            username=username,
            email=f'{username}@example.com',
            password='test123',
            structure='consultant'
        )
        time.sleep(0.5)
        
        try:
            lp = LearningPath.objects.get(user=user)
            if lp.template:
                print(f"  ✅ Template assigne via structures additionnelles: {lp.template.name}")
            else:
                print(f"  ❌ Aucun template assigne via structures additionnelles")
        except LearningPath.DoesNotExist:
            print(f"  ❌ Aucun LearningPath trouve pour structure additionnelle")
            
    except Exception as e:
        print(f"  ❌ Erreur creation utilisateur structure additionnelle: {e}")

# 5. Resume
print("\\n5. RESUME DU TEST:")
print(f"Utilisateurs crees: {len(created_users)}")
success_count = 0
for user in created_users:
    try:
        lp = LearningPath.objects.get(user=user)
        if lp.template:
            success_count += 1
            print(f"  ✅ {user.username} -> {lp.template.name}")
        else:
            print(f"  ❌ {user.username} -> Aucun template")
    except:
        print(f"  ❌ {user.username} -> Erreur verification")

print(f"\\nTaux de reussite: {success_count}/{len(created_users)} ({success_count/len(created_users)*100:.1f}%)")

if success_count == len(created_users):
    print("🎉 L'ASSIGNATION AUTOMATIQUE FONCTIONNE PARFAITEMENT !")
else:
    print("⚠️ L'assignation automatique a des problèmes")
'''
    
    try:
        result = subprocess.run(
            ['python3', 'manage.py', 'shell', '-c', script],
            cwd='crvslearning',
            capture_output=True,
            text=True,
            timeout=60
        )
        
        print("Resultat:")
        print(result.stdout)
        if result.stderr:
            print("Erreurs:")
            print(result.stderr)
            
    except Exception as e:
        print(f"Erreur execution: {e}")

if __name__ == "__main__":
    test_complete_assignment()
