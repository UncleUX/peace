#!/usr/bin/env python
"""
Test complet de certification pour test_auto_minsante
"""

import subprocess
import sys

def test_certification_complete():
    """Test complet de certification"""
    
    script = '''
from django.contrib.auth import get_user_model
from courses.models import LearningPath, CourseCompletion, Enrollment
from certifications.models import Certification
from django.utils import timezone

User = get_user_model()

print("=== TEST COMPLET DE CERTIFICATION ===")

# 1. Recuperer l'utilisateur et son parcours
user = User.objects.get(username="test_auto_minsante")
lp = LearningPath.objects.get(user=user)

print(f"Utilisateur: {user.username}")
print(f"Template: {lp.template.name}")
print(f"Cours dans template: {lp.template.courses.count()}")

# 2. Marquer tous les cours comme termines
print("\\n2. Marquage des cours comme termines...")
completed_count = 0
for course in lp.template.courses.all():
    # Creer ou mettre a jour CourseCompletion
    completion, created = CourseCompletion.objects.get_or_create(
        user=user,
        course=course,
        defaults={
            "completed_at": timezone.now(),
            "score": 85,  # Score > 80%
            "passed": True
        }
    )
    
    if created or not completion.completed_at:
        completion.completed_at = timezone.now()
        completion.score = 85
        completion.passed = True
        completion.save()
        completed_count += 1
        print(f"  ✅ {course.title} - Termine")
    else:
        print(f"  ℹ️  {course.title} - Deja termine")

print(f"Total cours termines: {completed_count}")

# 3. Mettre a jour le LearningPath
lp.completed_courses.add(*lp.template.courses.all())
lp.save()

# 4. Calculer la progression finale
total = lp.template.courses.count()
completed = lp.completed_courses.filter(id__in=lp.template.courses.all()).count()
rate = completed / total * 100

print(f"\\n3. Progression finale: {completed}/{total} ({rate:.1f}%)")
print(f"Seuil certification: {lp.template.certification_threshold}%")
print(f"Eligible certification: {rate >= lp.template.certification_threshold}")

# 5. Verifier si la certification a ete generee automatiquement
print("\\n4. Verification certification...")
certs = Certification.objects.filter(user=user)
print(f"Certifications trouvees: {certs.count()}")

for cert in certs:
    print(f"  🎓 {cert.code}")
    print(f"     Titre: {cert.title}")
    print(f"     Date: {cert.issued_at}")
    print(f"     Cours: {cert.course.title if cert.course else \"Parcours complet\"}")
    print(f"     Valide: {cert.is_valid}")

# 6. Verifier l'etat du LearningPath
lp.refresh_from_db()
print(f"\\n5. Etat final du LearningPath:")
print(f"  Certification obtenue: {lp.certification_obtained}")
print(f"  Date certification: {lp.certification_date}")

# 7. Si pas de certification, la generer manuellement
if not certs.exists() and rate >= lp.template.certification_threshold:
    print("\\n6. Generation manuelle de la certification...")
    try:
        from certifications.utils import generate_automatic_certification
        cert = generate_automatic_certification(user, lp.template)
        if cert:
            print(f"  ✅ Certification generee: {cert.code}")
            print(f"  ✅ Titre: {cert.title}")
        else:
            print("  ❌ Erreur generation certification")
    except Exception as e:
        print(f"  ❌ Exception: {e}")

print("\\n=== CONCLUSION FINALE ===")
if certs.exists():
    print("🎉 CERTIFICATION OBTENUE AVEC SUCCES !")
    print(f"📋 {certs.count()} certification(s) generee(s)")
else:
    if rate >= lp.template.certification_threshold:
        print("⚠️  Eligible mais certification non generee automatiquement")
    else:
        print("❌ Pas eligible pour certification")
'''
    
    try:
        result = subprocess.run(
            ['python3', 'manage.py', 'shell', '-c', script],
            cwd='crvslearning',
            capture_output=True,
            text=True,
            timeout=60
        )
        
        print("Resultat:")
        print(result.stdout)
        if result.stderr:
            print("Erreurs:")
            print(result.stderr)
            
    except Exception as e:
        print(f"Erreur execution: {e}")

if __name__ == "__main__":
    test_certification_complete()
