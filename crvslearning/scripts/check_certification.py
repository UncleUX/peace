#!/usr/bin/env python
"""
Script pour vérifier pourquoi la certification ne se génère pas
"""

import subprocess
import sys

def check_user_certification(username):
    """Vérifier l'éligibilité à la certification"""
    
    print(f"🔍 Vérification de certification pour : {username}")
    
    # Script Django à exécuter
    django_script = f'''
from django.contrib.auth import get_user_model
from courses.models import LearningPath, LearningPathTemplate, Enrollment, LessonProgress, CourseCompletion
from certifications.utils import check_certification_eligibility, generate_automatic_certification

User = get_user_model()

try:
    user = User.objects.get(username='{username}')
    print(f"✅ Utilisateur trouvé: {{user.username}}")
    print(f"   Structure: {{user.get_structure_display()}}")
    
    # Vérifier le LearningPath
    try:
        learning_path = user.learning_path
        print(f"✅ LearningPath: {{learning_path.template.name if learning_path.template else 'NON'}}")
        print(f"   Certification obtenue: {{learning_path.certification_obtained}}")
        print(f"   Progression certification: {{learning_path.certification_progress}}%")
    except:
        print("❌ Aucun LearningPath")
        return
    
    # Vérifier le template
    if not learning_path.template:
        print("❌ Aucun template assigné")
        return
        
    template = learning_path.template
    print(f"📋 Template: {{template.name}} ({{template.level}})")
    print(f"   Cours dans template: {{template.courses.count()}}")
    
    # Vérifier les inscriptions
    enrollments = Enrollment.objects.filter(user=user)
    print(f"📚 Inscriptions: {{enrollments.count()}} cours")
    
    # Vérifier les cours complétés
    completed_courses = learning_path.completed_courses.filter(id__in=template.courses.all())
    print(f"✅ Cours complétés: {{completed_courses.count()}}/{{template.courses.count()}}")
    
    # Détail par cours
    for course in template.courses.all():
        is_completed = course in completed_courses.all()
        status = "✅ TERMINÉ" if is_completed else "❌ NON TERMINÉ"
        print(f"   - {{course.title[:50]}}... {{status}}")
        
        # Vérifier les leçons si cours non terminé
        if not is_completed:
            from courses.models import Lesson
            total_lessons = Lesson.objects.filter(module__course=course).count()
            completed_lessons = LessonProgress.objects.filter(
                user=user, 
                lesson__module__course=course, 
                is_fully_completed=True
            ).count()
            print(f"     Leçons: {{completed_lessons}}/{{total_lessons}} complétées")
    
    # Vérifier l'éligibilité
    print("\\n🎯 Vérification éligibilité:")
    eligibility, message = check_certification_eligibility(user, learning_path)
    print(f"   Éligible: {{'OUI' if eligibility else 'NON'}}")
    print(f"   Message: {{message}}")
    
    # Si éligible, générer la certification
    if eligibility:
        print("\\n🔧 Génération automatique...")
        certification, result_message = generate_automatic_certification(
            user, learning_path, template
        )
        if certification:
            print(f"✅ Certification générée: {{certification.title}}")
            print(f"   Code: {{certification.code}}")
            print(f"   Date: {{certification.issued_at}}")
        else:
            print(f"❌ Erreur génération: {{result_message}}")
    else:
        print("\\n💡 Solutions possibles:")
        print("   1. Compléter les cours manquants")
        print("   2. Marquer les leçons comme terminées")
        print("   3. Vérifier les prérequis du template")
        
except Exception as e:
    print(f"❌ Erreur: {{e}}")
    import traceback
    traceback.print_exc()
'''
    
    # Exécuter le script
    try:
        result = subprocess.run(
            ['python', 'manage.py', 'shell', '-c', django_script],
            cwd='crvslearning',
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print(result.stdout)
        if result.stderr:
            print("Erreurs:")
            print(result.stderr)
            
    except Exception as e:
        print(f"❌ Erreur d'exécution: {e}")

if __name__ == "__main__":
    # Vérifier les deux utilisateurs
    print("=" * 60)
    check_user_certification("essamba")
    print("=" * 60)
    check_user_certification("sigmund_freud")
