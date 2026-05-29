#!/usr/bin/env python
"""
Vérifier pourquoi uptime.sale n'a pas de certification malgré avoir fini les cours
"""

import subprocess
import sys

def check_uptime_completion():
    """Vérifier l'état de complétion et certification pour uptime.sale"""
    
    print("Verification de la situation de uptime.sale...")
    
    check_script = '''
from django.contrib.auth import get_user_model
from courses.models import LearningPath, CourseCompletion
from certifications.models import Certification

User = get_user_model()

# 1. Trouver uptime.sale
try:
    user = User.objects.get(username="uptime.sale")
    print(f"Utilisateur: {user.username}")
    print(f"Structure: {user.get_structure_display()}")
    
    # 2. Verifier son LearningPath
    try:
        lp = LearningPath.objects.get(user=user)
        print(f"\\nLearningPath:")
        print(f"  Template: {lp.template.name if lp.template else 'Aucun'}")
        print(f"  Certification obtenue: {lp.certification_obtained}")
        print(f"  Date certification: {lp.certification_date}")
        
        if lp.template:
            # 3. Verifier les cours du template
            template_courses = lp.template.courses.all()
            print(f"\\nCours du template: {template_courses.count()}")
            
            # 4. Verifier les cours termines
            completed_courses = lp.completed_courses.filter(id__in=template_courses)
            print(f"Cours termines: {completed_courses.count()}")
            
            # 5. Calculer le pourcentage
            if template_courses.count() > 0:
                completion_rate = completed_courses.count() / template_courses.count() * 100
                print(f"Taux de completion: {completion_rate:.1f}%")
                print(f"Seuil requis: {lp.template.certification_threshold}%")
                
                # 6. Verifier si eligible
                if completion_rate >= lp.template.certification_threshold:
                    print("✅ ELIGIBLE pour certification!")
                    
                    # 7. Verifier si certification activee
                    if lp.template.certification_required and lp.template.auto_generate_certification:
                        print("✅ Certification automatique activee")
                        
                        # 8. Verifier les certifications existantes
                        certifications = Certification.objects.filter(user=user)
                        print(f"Certifications existantes: {certifications.count()}")
                        
                        if certifications.count() == 0:
                            print("❌ Aucune certification trouvee - PROBLEME!")
                            print("\\nCauses possibles:")
                            print("1. Signal non declenche")
                            print("2. Erreur dans generation")
                            print("3. Template non configure")
                            
                            # 9. Essayer de generer manuellement
                            print("\\nTentative de generation manuelle...")
                            from certifications.utils import generate_automatic_certification
                            try:
                                cert, message = generate_automatic_certification(user, lp, lp.template)
                                print(f"Resultat: {message}")
                                if cert:
                                    print("✅ Certification generee avec succes!")
                            except Exception as e:
                                print(f"❌ Erreur generation: {e}")
                        else:
                            print("✅ Certifications existent")
                    else:
                        print("❌ Certification automatique non activee")
                        print(f"  certification_required: {lp.template.certification_required}")
                        print(f"  auto_generate_certification: {lp.template.auto_generate_certification}")
                else:
                    print(f"❌ NON ELIGIBLE - Taux insuffisant")
            else:
                print("❌ Aucun cours dans le template")
        else:
            print("❌ Aucun template assigne")
            
    except LearningPath.DoesNotExist:
        print("❌ Aucun LearningPath trouve")
        
except User.DoesNotExist:
    print("❌ Utilisateur uptime.sale non trouve")
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
    check_uptime_completion()
