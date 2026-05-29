#!/usr/bin/env python
"""
Test complet de bout en bout sans manipulation directe de la base de données
"""

import subprocess
import sys

def test_end_to_end():
    """Test complet de bout en bout"""
    
    print("Test de bout en bout complet...")
    
    script = '''
from django.contrib.auth import get_user_model
from courses.models import LearningPath, LearningPathTemplate, CourseCompletion
from certifications.models import Certification
from django.utils import timezone

User = get_user_model()

# 1. Creer un nouvel utilisateur avec structure commune
new_user = User.objects.create_user(
    username='test_end_to_end_final',
    email='final@example.com',
    password='test123',
    first_name='Test',
    last_name='Final',
    structure='commune'
)

print('1. Utilisateur créé:', new_user.username)
print('   Structure:', new_user.get_structure_display())
print('   Email:', new_user.email)
print('   Mot de passe: test123')

# 2. Verifier si le signal a assigne le template automatiquement
try:
    lp = LearningPath.objects.get(user=new_user)
    if lp.template:
        print('2. Template assigné automatiquement:', lp.template.name)
        print('   Cours dans le template:', lp.template.courses.count())
        
        # 3. Simuler la completion des cours via les signaux
        print('3. Simulation de completion des cours...')
        
        for i, course in enumerate(lp.template.courses.all(), 1):
            print(f'   {i}. Completion du cours: {course.title}')
            
            # Creer la completion comme le ferait l'application
            completion = CourseCompletion.objects.create(
                user=new_user,
                course=course,
                completed_at=timezone.now(),
                completion_time=timezone.now()
            )
            
            # Ajouter au learning path
            lp.completed_courses.add(course)
            print(f'      ✅ Cours marqué comme terminé')
        
        # Sauvegarder le learning path
        lp.save()
        
        # 4. Calculer la progression
        total_courses = lp.template.courses.count()
        completed_courses = lp.completed_courses.filter(id__in=lp.template.courses.all()).count()
        completion_rate = completed_courses / total_courses * 100
        
        print(f'\\n4. Progression finale: {completion_rate:.1f}% ({completed_courses}/{total_courses})')
        print(f'   Seuil requis: {lp.template.certification_threshold}%')
        print(f'   Certification requise: {lp.template.certification_required}')
        print(f'   Generation auto: {lp.template.auto_generate_certification}')
        
        # 5. Verifier si la certification est générée automatiquement
        certs = Certification.objects.filter(user=new_user)
        print(f'\\n5. Certifications existantes: {certs.count()}')
        for cert in certs:
            print(f'   - {cert.code} ({cert.title})')
            print(f'     Date: {cert.issued_at}')
        
        # 6. Forcer la verification de certification
        if completion_rate >= lp.template.certification_threshold:
            print('\\n6. Test de generation automatique...')
            try:
                from certifications.utils import check_certification_eligibility, generate_automatic_certification
                eligible, message = check_certification_eligibility(new_user, lp)
                print(f'   Eligibilite: {eligible}')
                print(f'   Message: {message}')
                
                if eligible:
                    cert, gen_message = generate_automatic_certification(new_user, lp, lp.template)
                    print(f'   Generation: {gen_message}')
                    if cert:
                        print(f'   ✅ Certification generee: {cert.code}')
                    else:
                        print('   ❌ Erreur generation')
                        
            except Exception as e:
                print(f'   Erreur verification: {e}')
        else:
            print('\\n6. Non eligible pour certification')
            
    else:
        print('2. Aucun template assigné automatiquement')
        
except LearningPath.DoesNotExist:
    print('2. Aucun LearningPath trouvé')
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
    test_end_to_end()
