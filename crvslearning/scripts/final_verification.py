#!/usr/bin/env python
"""
Vérification finale de l'affichage des certifications
"""

import subprocess
import sys

def final_verification():
    """Vérification finale"""
    
    script = '''
from django.contrib.auth import get_user_model
from certifications.models import Certification

User = get_user_model()

user = User.objects.get(username="test_auto_minsante")
certs = Certification.objects.filter(user=user)

print("=== VERIFICATION FINALE ===")
print(f"Utilisateur: {user.username}")
print(f"Certifications: {certs.count()}")

for cert in certs:
    print(f"\\nCertification: {cert.display_name}")
    print(f"  Code: {cert.code}")
    print(f"  Template: {cert.template.name if cert.template else \"N/A\"}")
    print(f"  Course: {cert.course.title if cert.course else \"N/A\"}")
    print(f"  Level: {cert.level}")
    print(f"  Date: {cert.issued_at}")
    print(f"  PDF: {cert.pdf.url if cert.pdf else \"N/A\"}")
    print(f"  URL download: /certifications/download/{cert.code}/")
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
    final_verification()
