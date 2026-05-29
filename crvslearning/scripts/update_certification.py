#!/usr/bin/env python
"""
Mettre à jour la certification avec le template
"""

import subprocess
import sys

def update_certification():
    """Mettre à jour la certification"""
    
    script = '''
from django.contrib.auth import get_user_model
from certifications.models import Certification
from courses.models import LearningPath

User = get_user_model()

user = User.objects.get(username="test_auto_minsante")
cert = Certification.objects.filter(user=user).first()

if cert and not cert.template:
    lp = LearningPath.objects.get(user=user)
    if lp.template:
        cert.template = lp.template
        cert.title = f"Certification {lp.template.level.upper()} - {lp.template.name}"
        cert.save()
        print(f"Certification mise a jour avec le template: {lp.template.name}")
        print(f"Nouveau display name: {cert.display_name}")
    else:
        print("Aucun template trouve dans le LearningPath")
else:
    if cert and cert.template:
        print(f"Certification a deja un template: {cert.template.name}")
        print(f"Display name: {cert.display_name}")
    else:
        print("Aucune certification trouvee")
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
    update_certification()
