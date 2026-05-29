#!/usr/bin/env python
"""
Vérification finale de l'assignation pour uptime.scale
"""

import subprocess
import sys

def verify_uptime_final():
    """Vérification finale du template assigné"""
    
    print("Verification finale de l'assignation...")
    
    verify_script = '''
from django.contrib.auth import get_user_model
from courses.models import LearningPath

User = get_user_model()

# 1. Trouver uptime.scale
try:
    user = User.objects.get(username="uptime.scale")
    print(f"Utilisateur: {user.username}")
    print(f"Structure: {user.get_structure_display()}")
    
    # 2. Verifier son LearningPath
    try:
        lp = LearningPath.objects.get(user=user)
        print(f"Template: {lp.template.name if lp.template else 'Aucun'}")
        
        if lp.template:
            print(f"Structure template: {lp.template.get_structure_display()}")
            print(f"Niveau template: {lp.template.get_level_display()}")
            print(f"Cours: {lp.template.courses.count()}")
            print(f"Actif: {lp.template.is_active}")
            
            # 3. Verifier certification
            cert_req = getattr(lp.template, 'certification_required', False)
            auto_gen = getattr(lp.template, 'auto_generate_certification', False)
            print(f"Certification requise: {cert_req}")
            print(f"Generation auto: {auto_gen}")
            
            # 4. Verifier progression
            template_courses = lp.template.courses.all()
            completed_courses = lp.completed_courses.filter(id__in=template_courses)
            
            if template_courses.count() > 0:
                completion_rate = completed_courses.count() / template_courses.count() * 100
                print(f"Progression: {completion_rate:.1f}% ({completed_courses.count()}/{template_courses.count()})")
                print(f"Seuil: {lp.template.certification_threshold}%")
                
                if completion_rate >= lp.template.certification_threshold:
                    print("✅ ELIGIBLE pour certification!")
                else:
                    print("❌ Non eligible - Taux insuffisant")
            else:
                print("❌ Aucun cours dans le template")
                
        else:
            print("❌ Toujours aucun template")
            
    except LearningPath.DoesNotExist:
        print("❌ Aucun LearningPath trouve")
        
except User.DoesNotExist:
    print("❌ Utilisateur uptime.scale non trouve")
'''
    
    try:
        result = subprocess.run(
            ['python3', 'manage.py', 'shell', '-c', verify_script],
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
    verify_uptime_final()
