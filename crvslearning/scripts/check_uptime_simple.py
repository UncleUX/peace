#!/usr/bin/env python
"""
Script simple pour vérifier si l'utilisateur uptime.sale a un certificat
"""

import subprocess
import sys

def check_uptime_simple():
    """Vérification simple sans caractères Unicode"""
    
    print("Verification du certificat pour uptime.sale...")
    
    check_script = '''
from django.contrib.auth import get_user_model
from courses.models import LearningPath
from certifications.models import Certification

User = get_user_model()

# Chercher l utilisateur
try:
    user = User.objects.get(username="uptime.sale")
    print(f"Utilisateur trouve: {user.username}")
    print(f"Email: {user.email}")
    
except User.DoesNotExist:
    print("Utilisateur uptime.sale non trouve")
    
    # Chercher des utilisateurs similaires
    similar = User.objects.filter(username__icontains="uptime")
    if similar.exists():
        print("Utilisateurs similaires:")
        for u in similar:
            print(f"   - {u.username}")
    else:
        print("Aucun utilisateur similaire")
    exit()

# Verifier les certifications
certifications = Certification.objects.filter(user=user)
print(f"Nombre de certifications: {certifications.count()}")

if certifications.exists():
    print("CERTIFICATIONS TROUVEES:")
    for cert in certifications:
        print(f"  - Code: {cert.code}")
        print(f"    Cours: {cert.course.title}")
        print(f"    Niveau: {cert.get_level_display()}")
        print(f"    Date: {cert.issued_at}")
        print(f"    Titre: {cert.title}")
else:
    print("Aucune certification trouvee")

# Verifier le LearningPath
try:
    lp = LearningPath.objects.get(user=user)
    print(f"Certification obtenue: {lp.certification_obtained}")
    if lp.certification_obtained:
        print(f"Date: {lp.certification_date}")
except LearningPath.DoesNotExist:
    print("Aucun LearningPath trouve")

# Conclusion
if certifications.exists():
    print("RESULTAT: OUI - uptime.sale a une certification")
else:
    print("RESULTAT: NON - uptime.sale n a pas de certification")
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
    check_uptime_simple()
