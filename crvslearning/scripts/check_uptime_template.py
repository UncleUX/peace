#!/usr/bin/env python
"""
Vérifier le template assigné à uptime.sale
"""

import subprocess
import sys

def check_uptime_template():
    """Vérifier le template de uptime.sale"""
    
    print("Verification du template de uptime.sale...")
    
    check_script = '''
from django.contrib.auth import get_user_model
from courses.models import LearningPath, LearningPathTemplate

User = get_user_model()

# Chercher uptime.sale
try:
    user = User.objects.get(username="uptime.sale")
    
    # Verifier son LearningPath
    try:
        lp = LearningPath.objects.get(user=user)
        
        if lp.template:
            template = lp.template
            print(f"Template assigne: {template.name}")
            print(f"Certification requise: {template.certification_required}")
            print(f"Seuil: {template.certification_threshold}%")
            print(f"Auto-generation: {template.auto_generate_certification}")
            print(f"Niveau certification: {template.certification_level}")
            
            # Si certification non active, l activer
            if not template.certification_required:
                print("\\nACTIVATION DE LA CERTIFICATION:")
                template.certification_required = True
                template.certification_threshold = 80
                template.auto_generate_certification = True
                template.certification_level = "beginner"
                template.save()
                print("Certification activee pour ce template!")
                
        else:
            print("Aucun template assigne")
            
    except LearningPath.DoesNotExist:
        print("Aucun LearningPath trouve")
        
except User.DoesNotExist:
    print("Utilisateur uptime.sale non trouve")
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
    check_uptime_template()
