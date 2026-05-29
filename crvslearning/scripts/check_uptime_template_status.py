#!/usr/bin/env python
"""
Vérifier si uptime.scale a maintenant un template assigné
"""

import subprocess
import sys

def check_uptime_template_status():
    """Vérifier le statut du template pour uptime.scale"""
    
    print("Verification du statut du template pour uptime.scale...")
    
    check_script = '''
from django.contrib.auth import get_user_model
from courses.models import LearningPath, LearningPathTemplate

User = get_user_model()

# 1. Trouver uptime.scale
try:
    user = User.objects.get(username="uptime.scale")
    print(f"Utilisateur: {user.username}")
    print(f"Structure: {user.get_structure_display()}")
    
    # 2. Verifier son LearningPath
    try:
        lp = LearningPath.objects.get(user=user)
        print(f"\\nLearningPath:")
        print(f"  Template: {lp.template.name if lp.template else 'AUCUN'}")
        print(f"  Template ID: {lp.template.id if lp.template else 'None'}")
        
        if lp.template:
            print(f"  Structure template: {lp.template.get_structure_display()}")
            print(f"  Niveau template: {lp.template.get_level_display()}")
            print(f"  Cours: {lp.template.courses.count()}")
            print(f"  Actif: {lp.template.is_active}")
            
            # 3. Verifier certification
            cert_req = getattr(lp.template, 'certification_required', False)
            auto_gen = getattr(lp.template, 'auto_generate_certification', False)
            print(f"  Certification requise: {cert_req}")
            print(f"  Generation auto: {auto_gen}")
            
            # 4. Verifier progression
            template_courses = lp.template.courses.all()
            completed_courses = lp.completed_courses.filter(id__in=template_courses)
            
            if template_courses.count() > 0:
                completion_rate = completed_courses.count() / template_courses.count() * 100
                print(f"  Progression: {completion_rate:.1f}% ({completed_courses.count()}/{template_courses.count()})")
                print(f"  Seuil: {lp.template.certification_threshold}%")
                
                if completion_rate >= lp.template.certification_threshold:
                    print("  ✅ ELIGIBLE pour certification!")
                else:
                    print("  ❌ Non eligible - Taux insuffisant")
            else:
                print("  ❌ Aucun cours dans le template")
                
        else:
            print("  ❌ TOUJOURS AUCUN TEMPLATE!")
            print("  Le signal ne fonctionne pas correctement")
            
    except LearningPath.DoesNotExist:
        print("❌ Aucun LearningPath trouve")
        
except User.DoesNotExist:
    print("❌ Utilisateur uptime.scale non trouve")
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
    check_uptime_template_status()
