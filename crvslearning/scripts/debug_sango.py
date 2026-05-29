#!/usr/bin/env python
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crvslearning.settings')
django.setup()

from django.contrib.auth import get_user_model
from courses.models import LearningPath, LearningPathTemplate

User = get_user_model()

print("🔍 DÉBOGAGE COMPLET DE sango.ku")
print("=" * 50)

try:
    user = User.objects.get(username="sango.ku")
    print(f"✅ Utilisateur: {user.username}")
    print(f"📧 Email: {user.email}")
    print(f"🏢 Structure: {getattr(user, 'structure', 'Non définie')}")
    
    # Vérifier le LearningPath
    learning_path = user.learning_path
    print(f"\n📊 LEARNINGPATH:")
    print(f"🆔 ID: {learning_path.id}")
    print(f"🎯 Template: {learning_path.template}")
    print(f"📚 Cours complétés: {learning_path.completed_courses.count()}")
    
    if learning_path.template:
        template = learning_path.template
        print(f"\n🎯 TEMPLATE:")
        print(f"🆔 ID: {template.id}")
        print(f"📝 Nom: {template.name}")
        print(f"🏢 Structure: {template.structure}")
        print(f"🎭 Niveau: {template.level}")
        print(f"📚 Cours dans template: {template.courses.count()}")
        print(f"🎓 Certification requise: {getattr(template, 'certification_required', 'Non défini')}")
        print(f"📊 Seuil: {getattr(template, 'certification_threshold', 'Non défini')}")
        print(f"🤖 Auto-génération: {getattr(template, 'auto_generate_certification', 'Non défini')}")
        
        # Lister les cours du template
        print(f"\n📚 COURS DU TEMPLATE:")
        template_courses = list(template.courses.all())
        for i, course in enumerate(template_courses, 1):
            print(f"   {i}. {course.title}")
        
        # Lister les cours complétés
        print(f"\n✅ COURS COMPLÉTÉS:")
        completed_courses = list(learning_path.completed_courses.all())
        for i, course in enumerate(completed_courses, 1):
            print(f"   {i}. {course.title}")
        
        # Vérifier quels cours manquent
        template_course_ids = set(template.courses.values_list('id', flat=True))
        completed_course_ids = set(learning_path.completed_courses.values_list('id', flat=True))
        missing_course_ids = template_course_ids - completed_course_ids
        
        print(f"\n❌ COURS MANQUANTS:")
        if missing_course_ids:
            missing_courses = template.courses.filter(id__in=missing_course_ids)
            for i, course in enumerate(missing_courses, 1):
                print(f"   {i}. {course.title}")
        else:
            print("   ✅ Aucun cours manquant")
        
        # Calculer la progression correcte
        total_courses = template.courses.count()
        completed_count = len(completed_course_ids)
        progress_percentage = (completed_count / total_courses * 100) if total_courses > 0 else 0
        
        print(f"\n📊 PROGRESSION RÉELLE:")
        print(f"📚 Total: {total_courses}")
        print(f"✅ Complétés: {completed_count}")
        print(f"📊 Pourcentage: {progress_percentage:.1f}%")
        
        # Vérifier les autres templates
        print(f"\n🔍 TOUS LES TEMPLATES COMMUNE:")
        commune_templates = LearningPathTemplate.objects.filter(structure='commune')
        for t in commune_templates:
            print(f"   - {t.name} (ID: {t.id})")
    
    else:
        print("❌ Aucun template assigné")
        
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()

print("\n🚀 FIN DU DÉBOGAGE")
