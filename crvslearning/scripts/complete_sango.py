#!/usr/bin/env python
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crvslearning.settings')
django.setup()

from django.contrib.auth import get_user_model
from courses.models import LearningPath, LearningPathTemplate, Course, CourseCompletion

User = get_user_model()

print("🔧 COMPLÉTER LES COURS MANQUANTS POUR sango.ku")
print("=" * 50)

try:
    user = User.objects.get(username="sango.ku")
    learning_path = user.learning_path
    template = learning_path.template
    
    print(f"👤 Utilisateur: {user.username}")
    print(f"🎯 Template: {template.name}")
    
    # Récupérer les cours manquants
    template_courses = set(template.courses.all())
    completed_courses = set(learning_path.completed_courses.all())
    missing_courses = template_courses - completed_courses
    
    print(f"\n📚 COURS MANQUANTS ({len(missing_courses)}):")
    
    for course in missing_courses:
        print(f"   📖 {course.title}")
        
        # Créer une complétion de cours
        completion, created = CourseCompletion.objects.get_or_create(
            user=user,
            course=course,
            defaults={
                'completed_at': django.utils.timezone.now(),
                'score': 100,
                'max_score': 100
            }
        )
        
        if created:
            print(f"   ✅ CourseCompletion créé pour {course.title}")
        else:
            print(f"   ⚠️ CourseCompletion existait déjà pour {course.title}")
        
        # Ajouter au LearningPath
        learning_path.completed_courses.add(course)
        print(f"   ✅ Ajouté au LearningPath")
    
    # Sauvegarder le LearningPath
    learning_path.save()
    
    # Vérifier la progression finale
    total_courses = template.courses.count()
    completed_count = learning_path.completed_courses.count()
    progress_percentage = (completed_count / total_courses * 100) if total_courses > 0 else 0
    
    print(f"\n📊 PROGRESSION FINALE:")
    print(f"📚 Total: {total_courses}")
    print(f"✅ Complétés: {completed_count}")
    print(f"📊 Pourcentage: {progress_percentage:.1f}%")
    
    if progress_percentage >= 80:
        print(f"✅ ÉLIGIBLE À LA CERTIFICATION !")
        
        # Déclencher la vérification de certification
        from certifications.utils import check_certification_eligibility, generate_automatic_certification
        
        eligibility, message = check_certification_eligibility(user, learning_path)
        
        if eligibility:
            certification, result_message = generate_automatic_certification(
                user, learning_path, template
            )
            
            if certification:
                print(f"🎓 CERTIFICAT GÉNÉRÉ: {certification.title}")
                print(f"🔗 Code: {certification.code}")
                print(f"📅 Date: {certification.issued_at}")
                
                # Mettre à jour le LearningPath
                learning_path.certification_obtained = True
                learning_path.certification_date = certification.issued_at
                learning_path.save(update_fields=['certification_obtained', 'certification_date'])
                
                # Envoyer notification
                from notifications.models import Notification
                Notification.objects.create(
                    user=user,
                    sender="Système CRVS",
                    subject="🎓 Félicitations ! Certification obtenue",
                    message=f"""
Félicitations {user.get_full_name() or user.username} !

Votre certification a été générée automatiquement :
📜 {certification.title}
🎯 Niveau : {template.get_certification_level_display() or template.certification_level}
📅 Date : {certification.issued_at.strftime('%d/%m/%Y')}
🔗 Code : {certification.code}
📊 Progression : {progress_percentage:.1f}%

Votre certificat est maintenant disponible dans votre espace personnel.

Bravo pour votre excellent travail !

L'équipe CRVS Learning
                    """.strip(),
                    is_read=False
                )
                
                print(f"📬 Notification envoyée à {user.username}")
                print(f"🎉 PROBLÈME RÉSOLU POUR {user.username}!")
                
            else:
                print(f"❌ Erreur génération certification: {result_message}")
        else:
            print(f"❌ Non éligible: {message}")
    else:
        print(f"⏳ Toujours non éligible (seuil 80% non atteint)")
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()

print("\n🚀 OPÉRATION TERMINÉE")
