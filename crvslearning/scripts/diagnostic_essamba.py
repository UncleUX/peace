#!/usr/bin/env python
"""
Script de diagnostic pour l'utilisateur essamba
À exécuter depuis le répertoire crvslearning: python ../diagnostic_essamba.py
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crvslearning.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'crvslearning'))

# Initialiser Django
django.setup()

from django.contrib.auth import get_user_model
from courses.models import LearningPath, LearningPathTemplate, Enrollment
from certifications.models import Certification

User = get_user_model()

def diagnose_user(username):
    """Diagnostic complet pour un utilisateur"""
    print(f"=== DIAGNOSTIC pour {username} ===")
    
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        print(f"❌ Utilisateur {username} non trouvé")
        return
    
    # 1. Informations de base
    print(f"✅ Utilisateur trouvé: {user.username}")
    print(f"   Email: {user.email}")
    print(f"   Structure: {user.get_structure_display()} (code: {user.structure})")
    print(f"   Rôle: {user.get_role_display()}")
    
    # 2. Vérifier le LearningPath
    try:
        learning_path = user.learning_path
        print(f"✅ LearningPath trouvé")
        print(f"   - Template: {learning_path.template}")
        print(f"   - Current course: {learning_path.current_course}")
        print(f"   - Completed courses: {learning_path.completed_courses.count()}")
        print(f"   - Certification obtenue: {learning_path.certification_obtained}")
        if learning_path.certification_date:
            print(f"   - Date certification: {learning_path.certification_date}")
    except LearningPath.DoesNotExist:
        print("❌ Aucun LearningPath trouvé")
        learning_path = LearningPath.objects.create(user=user)
        print("✅ LearningPath créé automatiquement")
    
    # 3. Templates disponibles
    templates = LearningPathTemplate.objects.filter(structure=user.structure, is_active=True)
    print(f"\n📋 Templates disponibles pour {user.structure}: {templates.count()}")
    
    suitable_template = None
    for template in templates:
        print(f"   - {template.name} ({template.level}) - {template.courses.count()} cours")
        if not suitable_template and template.level in ['beginner', 'intermediate', 'advanced']:
            suitable_template = template
    
    # 4. Inscriptions
    enrollments = Enrollment.objects.filter(user=user)
    print(f"\n📚 Inscriptions aux cours: {enrollments.count()}")
    for enrollment in enrollments:
        print(f"   - {enrollment.course.title} (inscrit le {enrollment.enrolled_at})")
    
    # 5. Certifications
    certifications = Certification.objects.filter(user=user)
    print(f"\n🎓 Certifications: {certifications.count()}")
    for cert in certifications:
        print(f"   - {cert.title} ({cert.level}) - {cert.issued_at}")
    
    # 6. Corrections automatiques
    print(f"\n=== CORRECTIONS AUTOMATIQUES ===")
    
    learning_path = user.learning_path  # Rafraîchir après création éventuelle
    
    # Problème 1: Pas de template assigné
    if not learning_path.template:
        print("⚠️  Aucun template assigné")
        
        if suitable_template:
            print(f"🔧 Assignation du template: {suitable_template.name}")
            
            # Inscrire l'utilisateur à tous les cours du template
            for course in suitable_template.courses.all():
                enrollment, created = Enrollment.objects.get_or_create(
                    user=user, 
                    course=course
                )
                if created:
                    print(f"  ✅ Inscrit à: {course.title}")
            
            # Assigner le template
            learning_path.template = suitable_template
            if suitable_template.courses.exists():
                learning_path.current_course = suitable_template.courses.first()
            learning_path.save()
            
            print("✅ Template assigné avec succès")
        else:
            print("❌ Aucun template approprié trouvé")
    
    # Problème 2: Pas d'inscriptions mais template disponible
    if not enrollments.exists() and learning_path.template:
        print("⚠️  Aucune inscription aux cours")
        print("🔧 Inscription automatique aux cours du template...")
        for course in learning_path.template.courses.all():
            enrollment, created = Enrollment.objects.get_or_create(
                user=user, 
                course=course
            )
            if created:
                print(f"  ✅ Inscrit à: {course.title}")
    
    # Problème 3: Vérifier l'éligibilité à la certification
    if learning_path.template and learning_path.completed_courses.exists():
        from certifications.utils import check_certification_eligibility, generate_automatic_certification
        
        eligibility, message = check_certification_eligibility(user, learning_path)
        print(f"🎯 Éligibilité certification: {message}")
        
        if eligibility:
            certification, result_message = generate_automatic_certification(
                user, learning_path, learning_path.template
            )
            if certification:
                print(f"✅ Certification générée: {certification}")
            else:
                print(f"❌ Erreur génération certification: {result_message}")
    
    print("\n=== RÉSUMÉ FINAL ===")
    learning_path = user.learning_path  # Rafraîchir une dernière fois
    print(f"Template assigné: {'✅' if learning_path.template else '❌'}")
    print(f"Inscriptions: {enrollments.count()} cours")
    print(f"Cours complétés: {learning_path.completed_courses.count()}")
    print(f"Certification: {'✅' if learning_path.certification_obtained else '❌'}")
    
    if learning_path.template:
        total_courses = learning_path.template.courses.count()
        completed_courses = learning_path.completed_courses.filter(id__in=learning_path.template.courses.all()).count()
        progress = (completed_courses / total_courses * 100) if total_courses > 0 else 0
        print(f"Progression: {progress:.1f}% ({completed_courses}/{total_courses})")

if __name__ == "__main__":
    diagnose_user("essamba")
