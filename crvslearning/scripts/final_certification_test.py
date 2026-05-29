#!/usr/bin/env python
"""
Test final de certification pour test_notification
"""

import subprocess
import sys

def final_certification_test():
    """Test final de certification"""
    
    print("Test final de certification...")
    
    script = '''
from django.contrib.auth import get_user_model
from courses.models import LearningPath, CourseCompletion
from certifications.models import Certification
from django.utils import timezone

User = get_user_model()
user = User.objects.get(username="test_notification")
lp = LearningPath.objects.get(user=user)

print("Utilisateur:", user.username)
print("Template:", lp.template.name)
print("Cours dans template:", lp.template.courses.count())

# Marquer tous les cours comme termines
completed_count = 0
for course in lp.template.courses.all():
    completion, created = CourseCompletion.objects.get_or_create(
        user=user,
        course=course,
        defaults={"completed_at": timezone.now()}
    )
    if created:
        lp.completed_courses.add(course)
        completed_count += 1
        print("Cours termine:", course.title)
    else:
        print("Cours deja termine:", course.title)

# Mettre a jour le learning path
lp.save()

# Calculer la progression
total_courses = lp.template.courses.count()
completed_courses = lp.completed_courses.filter(id__in=lp.template.courses.all()).count()
completion_rate = completed_courses / total_courses * 100

print("Progression:", completion_rate, "%")
print("Seuil requis:", lp.template.certification_threshold, "%")

# Verifier les certifications
certs = Certification.objects.filter(user=user)
print("Certifications existantes:", certs.count())
for cert in certs:
    print("  -", cert.code, "(", cert.course.title, ")")
    
print("Cours termines:", completed_count, "sur", total_courses)
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
    final_certification_test()
