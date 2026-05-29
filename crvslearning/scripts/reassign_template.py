#!/usr/bin/env python
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crvslearning.settings')
django.setup()

from django.contrib.auth import get_user_model
from courses.models import LearningPath, LearningPathTemplate

User = get_user_model()

print("🔧 RÉASSIGNER UN TEMPLATE À sango.ku")
print("=" * 50)

try:
    user = User.objects.get(username="sango.ku")
    learning_path = user.learning_path
    
    print(f"👤 Utilisateur: {user.username}")
    print(f"📊 LearningPath ID: {learning_path.id}")
    print(f"🎯 Template actuel: {learning_path.template}")
    
    # Trouver le template "Agent Communal Débutant"
    try:
        template = LearningPathTemplate.objects.get(name="Agent Communal Débutant")
        
        print(f"\n🎯 Template trouvé:")
        print(f"📝 Nom: {template.name}")
        print(f"🆔 ID: {template.id}")
        print(f"🏢 Structure: {template.structure}")
        print(f"🎭 Niveau: {template.level}")
        print(f"📚 Cours: {template.courses.count()}")
        print(f"🎓 Certification requise: {getattr(template, 'certification_required', 'Non défini')}")
        
        # Assigner le template
        learning_path.template = template
        learning_path.save()
        
        print(f"\n✅ Template '{template.name}' assigné à {user.username}")
        
        # Vérifier la progression
        total_courses = template.courses.count()
        completed_courses = learning_path.completed_courses.filter(
            id__in=template.courses.all()
        ).count()
        
        progress_percentage = (completed_courses / total_courses * 100) if total_courses > 0 else 0
        
        print(f"\n📊 PROGRESSION:")
        print(f"📚 Total: {total_courses}")
        print(f"✅ Complétés: {completed_courses}")
        print(f"📊 Pourcentage: {progress_percentage:.1f}%")
        
        # Si la certification n'est pas activée, l'activer
        if not getattr(template, 'certification_required', False):
            print(f"\n🔧 ACTIVATION DE LA CERTIFICATION:")
            template.certification_required = True
            template.certification_threshold = 80
            template.auto_generate_certification = True
            template.certification_level = 'beginner'
            template.save()
            print(f"✅ Certification activée sur le template '{template.name}'")
        
        # Vérifier l'éligibilité
        if progress_percentage >= 80:
            print(f"\n✅ ÉLIGIBLE À LA CERTIFICATION !")
            
            try:
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
                    
            except ImportError:
                print("⚠️ Module certifications non disponible")
            except Exception as e:
                print(f"❌ Erreur certification: {e}")
        else:
            print(f"\n⏳ Non éligible (progression {progress_percentage:.1f}% < seuil 80%)")
        
    except LearningPathTemplate.DoesNotExist:
        print("❌ Template 'Agent Communal Débutant' non trouvé")
        
        # Lister les templates disponibles
        templates = LearningPathTemplate.objects.all()
        print(f"\n📋 Templates disponibles ({templates.count()}):")
        for t in templates:
            print(f"   🆔 {t.id}: {t.name} ({t.structure})")
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()

print("\n🚀 OPÉRATION TERMINÉE")
