"""
Commande de debug pour vérifier les certifications
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from courses.models import LearningPath, LearningPathTemplate
from certifications.models import Certification

User = get_user_model()


class Command(BaseCommand):
    help = 'Debug des certifications - vérifie pourquoi 100% ne donne pas de certificat'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Nom d\'utilisateur à vérifier'
        )

    def handle(self, *args, **options):
        username = options.get('username')
        
        if not username:
            self.stdout.write(self.style.ERROR("❌ Spécifiez --username"))
            return
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"❌ Utilisateur {username} non trouvé"))
            return
        
        self.stdout.write(f"🔍 DEBUG CERTIFICATIONS POUR: {user.username}")
        self.stdout.write("=" * 60)
        
        # 1. Vérifier le LearningPath
        try:
            learning_path = user.learning_path
            self.stdout.write(f"📊 LearningPath: {learning_path}")
            
            if learning_path:
                self.stdout.write(f"   • Template: {learning_path.template}")
                self.stdout.write(f"   • Cours actuel: {learning_path.current_course}")
                self.stdout.write(f"   • Cours complétés: {learning_path.completed_courses.count()}")
                self.stdout.write(f"   • Certification obtenue: {learning_path.certification_obtained}")
                self.stdout.write(f"   • Date certification: {learning_path.certification_date}")
                self.stdout.write(f"   • Progression certification: {learning_path.certification_progress}%")
                
                # Vérifier si le template existe
                if learning_path.template:
                    total_courses = learning_path.template.courses.count()
                    completed_courses = learning_path.completed_courses.filter(id__in=learning_path.template.courses.all()).count()
                    completion_rate = (completed_courses / total_courses * 100) if total_courses > 0 else 0
                    
                    self.stdout.write(f"   • Taux completion: {completion_rate:.1f}% ({completed_courses}/{total_courses})")
                    
                    # Vérifier les seuils
                    if learning_path.template.level == 'beginner' and completion_rate >= 80:
                        self.stdout.write(self.style.SUCCESS("   ✅ DEVRAIT AVOIR UNE CERTIFICATION (débutant >= 80%)"))
                    elif learning_path.template.level == 'intermediate' and completion_rate >= 90:
                        self.stdout.write(self.style.SUCCESS("   ✅ DEVRAIT AVOIR UNE CERTIFICATION (intermédiaire >= 90%)"))
                    elif learning_path.template.level == 'advanced' and completion_rate >= 95:
                        self.stdout.write(self.style.SUCCESS("   ✅ DEVRAIT AVOIR UNE CERTIFICATION (avancé >= 95%)"))
                    else:
                        self.stdout.write(self.style.WARNING(f"   ⚠️  SEUIL NON ATTEINT ({learning_path.template.level} = {completion_rate:.1f}%)"))
                else:
                    self.stdout.write(self.style.WARNING("   ⚠️  AUCUN TEMPLATE ASSIGNÉ"))
            else:
                self.stdout.write(self.style.WARNING("   ⚠️  AUCUN LEARNING PATH"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Erreur LearningPath: {e}"))
        
        self.stdout.write("")
        
        # 2. Vérifier les certifications
        try:
            certifications = Certification.objects.filter(user=user).order_by('-issued_at')
            self.stdout.write(f"🎓 Certifications: {certifications.count()}")
            
            for i, cert in enumerate(certifications, 1):
                self.stdout.write(f"   {i}. {cert}")
                self.stdout.write(f"      • Code: {cert.code}")
                self.stdout.write(f"      • Niveau: {cert.get_level_display()}")
                self.stdout.write(f"      • Cours: {cert.course}")
                self.stdout.write(f"      • Date: {cert.issued_at}")
                self.stdout.write(f"      • Valide: {cert.is_valid}")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Erreur certifications: {e}"))
        
        self.stdout.write("")
        
        # 3. Vérifier l'éligibilité automatique
        try:
            if learning_path and learning_path.template:
                from certifications.utils import check_certification_eligibility
                
                eligibility, message = check_certification_eligibility(user, learning_path)
                self.stdout.write(f"🔍 Éligibilité: {eligibility}")
                self.stdout.write(f"   • Message: {message}")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Erreur éligibilité: {e}"))
        
        # 4. Tenter de générer manuellement
        try:
            if learning_path and learning_path.template:
                from certifications.utils import generate_automatic_certification
                
                certification, result_message = generate_automatic_certification(
                    user, learning_path.template
                )
                
                if certification:
                    self.stdout.write(self.style.SUCCESS(f"✅ Certification générée manuellement: {certification.code}"))
                    self.stdout.write(f"   • Message: {result_message}")
                else:
                    self.stdout.write(self.style.ERROR(f"❌ Erreur génération: {result_message}"))
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Erreur génération manuelle: {e}"))
        
        self.stdout.write("=" * 60)
