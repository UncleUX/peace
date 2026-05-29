#!/usr/bin/env python
"""
Test simple de bout en bout
"""

import subprocess
import sys

def simple_end_to_end():
    """Test simple de bout en bout"""
    
    print("Test simple de bout en bout...")
    
    script = '''
from django.contrib.auth import get_user_model
from courses.models import LearningPath, LearningPathTemplate, CourseCompletion
from certifications.models import Certification
from django.utils import timezone

User = get_user_model()

# 1. Creer un nouvel utilisateur
new_user = User.objects.create_user(
    username='test_simple',
    email='simple@example.com',
    password='test123',
    structure='commune'
)

print('1. Utilisateur cree:', new_user.username)

# 2. Assigner le template manuellement
template = LearningPathTemplate.objects.filter(structure='commune', is_active=True).first()
if template:
    lp, created = LearningPath.objects.get_or_create(user=new_user)
    lp.template = template
    lp.save()
    print('2. Template assigne:', template.name)
    
    # 3. Completer tous les cours
    for course in template.courses.all():
        completion = CourseCompletion.objects.create(
            user=new_user,
            course=course,
            completed_at=timezone.now()
        )
        lp.completed_courses.add(course)
        print('3. Cours termine:', course.title)
    
    lp.save()
    
    # 4. Calculer progression
    total = template.courses.count()
    completed = lp.completed_courses.filter(id__in=template.courses.all()).count()
    rate = completed / total * 100
    
    print('4. Progression:', rate, '%')
    print('   Seuil:', template.certification_threshold, '%')
    
    # 5. Generer certification
    if rate >= template.certification_threshold:
        cert = Certification.objects.create(
            user=new_user,
            course=template.courses.first(),
            code=f'SIMPLE-{new_user.username.upper()}-{timezone.now().year}',
            title=f'Certification {template.name}',
            level='beginner',
            issued_at=timezone.now(),
            is_valid=True
        )
        
        lp.certification_obtained = True
        lp.certification_date = timezone.now()
        lp.save()
        
        print('5. Certification generee:', cert.code)
        print('   Titre:', cert.title)
        print('   Date:', cert.issued_at)
    else:
        print('5. Non eligible pour certification')
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
    simple_end_to_end()
