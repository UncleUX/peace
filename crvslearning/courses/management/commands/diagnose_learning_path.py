from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from courses.models import LearningPath, LearningPathTemplate, Enrollment
from certifications.models import Certification

User = get_user_model()

class Command(BaseCommand):
    help = 'Diagnostiquer et réparer les problèmes de parcours d'apprentissage'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Nom d\'utilisateur à diagnostiquer')
        parser.add_argument('--fix', action='store_true', help='Appliquer les corrections automatiquement')

    def handle(self, *args, **options):
        username = options.get('username')
        if not username:
            self.stdout.write(self.style.ERROR('Veuillez spécifier un nom d\'utilisateur avec --username'))
            return

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Utilisateur {username} non trouvé'))
            return

        self.stdout.write(f'=== DIAGNOSTIC pour {user.username} ===')
        
        # 1. Vérifier les informations de base
        self.stdout.write(f'Email: {user.email}')
        self.stdout.write(f'Structure: {user.get_structure_display()} (code: {user.structure})')
        self.stdout.write(f'Rôle: {user.get_role_display()}')
        
        # 2. Vérifier le LearningPath
        try:
            learning_path = user.learning_path
            self.stdout.write(self.style.SUCCESS('✅ LearningPath trouvé'))
            self.stdout.write(f'  - Template: {learning_path.template}')
            self.stdout.write(f'  - Current course: {learning_path.current_course}')
            self.stdout.write(f'  - Completed courses: {learning_path.completed_courses.count()}')
            self.stdout.write(f'  - Certification obtenue: {learning_path.certification_obtained}')
            if learning_path.certification_date:
                self.stdout.write(f'  - Date certification: {learning_path.certification_date}')
        except LearningPath.DoesNotExist:
            self.stdout.write(self.style.WARNING('❌ Aucun LearningPath trouvé'))
            if options.get('fix'):
                learning_path = LearningPath.objects.create(user=user)
                self.stdout.write(self.style.SUCCESS('✅ LearningPath créé'))

        # 3. Vérifier les templates disponibles
        templates = LearningPathTemplate.objects.filter(structure=user.structure, is_active=True)
        self.stdout.write(f'\n📋 Templates disponibles pour {user.structure}: {templates.count()}')
        
        for template in templates:
            self.stdout.write(f'  - {template.name} ({template.level}) - {template.courses.count()} cours')
            
        # 4. Vérifier les inscriptions
        enrollments = Enrollment.objects.filter(user=user)
        self.stdout.write(f'\n📚 Inscriptions aux cours: {enrollments.count()}')
        for enrollment in enrollments:
            self.stdout.write(f'  - {enrollment.course.title} (inscrit le {enrollment.enrolled_at})')
            
        # 5. Vérifier les certifications
        certifications = Certification.objects.filter(user=user)
        self.stdout.write(f'\n🎓 Certifications: {certifications.count()}')
        for cert in certifications:
            self.stdout.write(f'  - {cert.title} ({cert.level}) - {cert.issued_at}')
            
        # 6. Diagnostic et corrections
        self.stdout.write(f'\n=== DIAGNOSTIC ===')
        
        learning_path = user.learning_path
        
        # Problème 1: Pas de template assigné
        if not learning_path.template:
            self.stdout.write(self.style.WARNING('⚠️  Aucun template assigné'))
            
            # Chercher le template approprié
            suitable_template = None
            for template in templates:
                if template.level == 'beginner':
                    suitable_template = template
                    break
                elif template.level == 'intermediate':
                    suitable_template = template
                elif template.level == 'advanced':
                    suitable_template = template
                    
            if suitable_template and options.get('fix'):
                self.stdout.write(f'🔧 Assignation du template: {suitable_template.name}')
                suitable_template.assign_to_user(user)
                self.stdout.write(self.style.SUCCESS('✅ Template assigné avec succès'))
            elif suitable_template:
                self.stdout.write(f'💡 Template recommandé: {suitable_template.name}')
            else:
                self.stdout.write(self.style.ERROR('❌ Aucun template approprié trouvé'))
                
        # Problème 2: Pas d'inscriptions
        if not enrollments.exists() and learning_path.template:
            self.stdout.write(self.style.WARNING('⚠️  Aucune inscription aux cours'))
            if options.get('fix') and learning_path.template:
                self.stdout.write('🔧 Inscription automatique aux cours du template...')
                for course in learning_path.template.courses.all():
                    enrollment, created = Enrollment.objects.get_or_create(
                        user=user, 
                        course=course
                    )
                    if created:
                        self.stdout.write(f'  ✅ Inscrit à: {course.title}')
                        
        # Problème 3: Vérifier l'éligibilité à la certification
        if learning_path.template and learning_path.completed_courses.exists():
            from certifications.utils import check_certification_eligibility, generate_automatic_certification
            
            eligibility, message = check_certification_eligibility(user, learning_path)
            self.stdout.write(f'🎯 Éligibilité certification: {message}')
            
            if eligibility and options.get('fix'):
                certification, result_message = generate_automatic_certification(
                    user, learning_path, learning_path.template
                )
                if certification:
                    self.stdout.write(self.style.SUCCESS(f'✅ Certification générée: {certification}'))
                else:
                    self.stdout.write(self.style.ERROR(f'❌ Erreur génération certification: {result_message}'))
                    
        self.stdout.write('\n=== FIN DU DIAGNOSTIC ===')
