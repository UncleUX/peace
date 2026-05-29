#!/usr/bin/env python
"""
Compléter le parcours de test_notification et vérifier la certification
"""

import subprocess
import sys

def complete_test_parcours():
    """Compléter le parcours et vérifier la certification"""
    
    print("Completion du parcours de test_notification...")
    
    complete_script = '''
from django.contrib.auth import get_user_model
from courses.models import LearningPath, CourseCompletion
from certifications.models import Certification
from django.utils import timezone

User = get_user_model()
user = User.objects.get(username="test_notification")
lp = LearningPath.objects.get(user=user)

print(f"Utilisateur: {user.username}")
print(f"Template: {lp.template.name if lp.template else 'Aucun'}")

if lp.template:
    print(f"Cours dans template: {lp.template.courses.count()}")
    
    # Marquer tous les cours comme termines
    for course in lp.template.courses.all():
        completion, created = CourseCompletion.objects.get_or_create(
            user=user,
            course=course,
            defaults={"completed_at": timezone.now()}
        )
        if created:
            lp.completed_courses.add(course)
            print(f"✅ Cours termine: {course.title}")
        else:
            print(f"ℹ️ Cours deja termine: {course.title}")

    # Calculer la progression
    total_courses = lp.template.courses.count()
    completed_courses = lp.completed_courses.filter(id__in=lp.template.courses.all()).count()
    completion_rate = completed_courses / total_courses * 100

    print(f"\\nProgression: {completion_rate:.1f}% ({completed_courses}/{total_courses})")
    
    # Verifier la configuration du template
    cert_req = getattr(lp.template, "certification_required", False)
    auto_gen = getattr(lp.template, "auto_generate_certification", False)
    threshold = getattr(lp.template, "certification_threshold", 80)
    
    print(f"Seuil requis: {threshold}%")
    print(f"Certification requise: {cert_req}")
    print(f"Generation auto: {auto_gen}")

    if completion_rate >= threshold:
        print("✅ ELIGIBLE pour certification!")
        
        # Forcer la verification de certification
        lp.certification_obtained = False
        lp.save()
        
        # Declencher la verification manuelle
        try:
            from certifications.utils import check_certification_eligibility
            eligible, message = check_certification_eligibility(user, lp)
            print(f"Verification: {message}")
            
            # Verifier les certifications
            certs = Certification.objects.filter(user=user)
            print(f"Certifications existantes: {certs.count()}")
            for cert in certs:
                print(f"  - {cert.code} ({cert.course.title})")
                
        except Exception as e:
            print(f"Erreur verification: {e}")
            
            # Essayer de generer manuellement
            try:
                from certifications.utils import generate_automatic_certification
                cert, message = generate_automatic_certification(user, lp, lp.template)
                print(f"Generation manuelle: {message}")
                if cert:
                    print(f"✅ Certification generee: {cert.code}")
            except Exception as e2:
                print(f"Erreur generation: {e2}")
    else:
        print("❌ Non eligible")
else:
    print("❌ Aucun template assigne")
'''
    
    try:
        result = subprocess.run(
            ['python3', 'manage.py', 'shell', '-c', complete_script],
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
    complete_test_parcours()
