#!/usr/bin/env python
"""
Test de l'affichage des certifications dans le profil
"""

import subprocess
import sys

def test_certification_display():
    """Test de l'affichage"""
    
    script = '''
from django.contrib.auth import get_user_model
from certifications.models import Certification

User = get_user_model()

print("=== TEST AFFICHAGE CERTIFICATIONS ===")

user = User.objects.get(username="test_auto_minsante")
print(f"Utilisateur: {user.username}")

certs = Certification.objects.filter(user=user)
print(f"Total certifications: {certs.count()}")

for cert in certs:
    print(f"\\nCertification:")
    print(f"  Code: {cert.code}")
    print(f"  Display name: {cert.display_name}")
    print(f"  Course: {cert.course.title if cert.course else \"N/A\"}")
    print(f"  Template: {cert.template.name if cert.template else \"N/A\"}")
    print(f"  Level: {cert.level}")
    print(f"  Date: {cert.issued_at}")
    print(f"  PDF: {cert.pdf.url if cert.pdf else \"N/A\"}")

# Mettre à jour la certification existante
if certs.exists():
    cert = certs.first()
    if cert.course and not cert.template:
        from courses.models import LearningPath
        lp = LearningPath.objects.get(user=user)
        if lp.template:
            cert.template = lp.template
            cert.title = f"Certification {lp.template.level.upper()} - {lp.template.name}"
            cert.save()
            print(f"\\n✅ Certification mise à jour avec le template: {lp.template.name}")
            print(f"   Nouveau display name: {cert.display_name}")
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
    test_certification_display()
