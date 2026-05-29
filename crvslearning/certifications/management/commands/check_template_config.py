from django.core.management.base import BaseCommand
from courses.models import LearningPathTemplate, LearningPath
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Vérifier la configuration des templates et certification'

    def handle(self, *args, **options):
        print("🔍 VÉRIFICATION DE LA CONFIGURATION DES TEMPLATES")
        
        # Vérifier tous les templates
        templates = LearningPathTemplate.objects.all()
        print(f"\n📋 Templates trouvés: {templates.count()}")
        
        for template in templates:
            print(f"\n🎯 Template: {template.name}")
            print(f"📊 Niveau: {template.level}")
            print(f"📚 Cours: {template.courses.count()}")
            print(f"📋 Sequence: {template.sequence}")
            
            if template.sequence:
                cert_required = template.sequence.get("certification_required", False)
                print(f"🎓 Certification requise: {cert_required}")
                
                if not cert_required:
                    print("❌ PROBLÈME: La certification n'est PAS activée!")
                else:
                    print("✅ Certification activée")
            else:
                print("❌ PROBLÈME: Aucune séquence définie!")
        
        # Vérifier le LearningPath de sango ku
        try:
            user = User.objects.get(username='sango ku')
            learning_path = LearningPath.objects.get(user=user)
            
            print(f"\n👤 LearningPath de {user.username}:")
            print(f"🎯 Template: {learning_path.template.name if learning_path.template else 'AUCUN'}")
            print(f"✅ Cours complétés: {learning_path.completed_courses.count()}")
            print(f"🎓 Certification obtenue: {learning_path.certification_obtained}")
            
            if learning_path.template:
                template = learning_path.template
                total_courses = template.courses.count()
                completed_courses = learning_path.completed_courses.filter(
                    id__in=template.courses.all()
                ).count()
                
                print(f"\n📊 Progression:")
                print(f"📚 Total cours: {total_courses}")
                print(f"✅ Cours complétés: {completed_courses}")
                print(f"📊 Pourcentage: {(completed_courses / total_courses * 100):.1f}%" if total_courses > 0 else "0%")
                
                if completed_courses >= total_courses:
                    print("✅ PARCOURS TERMINÉ - Devrait avoir une certification!")
                else:
                    print(f"❌ Parcours non terminé - manque {total_courses - completed_courses} cours")
            else:
                print("❌ Aucun template assigné!")
                
        except Exception as e:
            print(f"❌ Erreur: {e}")
