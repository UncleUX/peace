#!/usr/bin/env python
"""
Vérification simple des parcours pour la structure commune
"""

import subprocess
import sys

def check_commune_simple():
    """Vérification simple sans caractères Unicode"""
    
    print("Verification des parcours pour la structure commune...")
    
    check_script = '''
from courses.models import LearningPathTemplate

# Templates pour la structure commune
commune_templates = LearningPathTemplate.objects.filter(structure="commune")
print(f"Total parcours commune: {commune_templates.count()}")

if commune_templates.exists():
    print("Parcours trouves:")
    for template in commune_templates:
        status = "Actif" if template.is_active else "Inactif"
        print(f"  - {template.name} ({template.level}) - {status}")
        print(f"    Cours: {template.courses.count()}")
        cert_req = getattr(template, "certification_required", False)
        print(f"    Certification: {cert_req}")
else:
    print("Aucun parcours trouve pour la structure commune")

# Templates multi-structures
multi_templates = LearningPathTemplate.objects.filter(structure="multi_structure", is_active=True)
print(f"Parcours multi-structures: {multi_templates.count()}")

if multi_templates.exists():
    print("Parcours multi-structures disponibles:")
    for template in multi_templates[:3]:
        print(f"  - {template.name} ({template.level})")

# Conclusion
if commune_templates.exists():
    print("RESULTAT: OUI - Il y a des parcours pour la commune")
else:
    print("RESULTAT: NON - Aucun parcours specifique pour la commune")
    if multi_templates.exists():
        print("SOLUTION: Utiliser les parcours multi-structures")
'''
    
    try:
        result = subprocess.run(
            ['python3', 'manage.py', 'shell', '-c', check_script],
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
    check_commune_simple()
