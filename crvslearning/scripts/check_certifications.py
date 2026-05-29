#!/usr/bin/env python
"""
Vérifier les certifications existantes
"""

import subprocess
import sys

def check_certifications():
    """Vérifier les certifications"""
    
    script = '''
from certifications.models import Certification
from django.contrib.auth import get_user_model

User = get_user_model()

print("=== CERTIFICATIONS EXISTANTES ===")
certs = Certification.objects.all()
print(f"Total: {certs.count()}")

for cert in certs:
    print(f"User: {cert.user.username}, Course: {cert.course.title if cert.course else \"None\"}, Template: {cert.template.name if cert.template else \"None\"}, Level: {cert.level}")
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
    check_certifications()
