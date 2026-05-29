from django.core.management.base import BaseCommand
from courses.models import LearningPathTemplate, Course
import json

class Command(BaseCommand):
    help = 'Génère automatiquement une séquence à partir des cours sélectionnés'

    def add_arguments(self, parser):
        parser.add_argument('--name', type=str, required=True, help='Nom du parcours')
        parser.add_argument('--course-ids', type=str, required=True, help='IDs des cours séparés par des virgules')
        parser.add_argument('--structure', type=str, default='commune', help='Structure cible')
        parser.add_argument('--level', type=str, default='débutant', help='Niveau du parcours')
        parser.add_argument('--weeks-per-course', type=float, default=1.5, help='Semaines par cours')
        parser.add_argument('--dry-run', action='store_true', help='Simuler sans sauvegarder')

    def handle(self, *args, **options):
        name = options['name']
        course_ids_str = options['course_ids']
        structure = options['structure']
        level = options['level']
        weeks_per_course = options['weeks_per_course']
        dry_run = options['dry_run']
        
        # Parser les IDs des cours
        try:
            course_ids = [int(id.strip()) for id in course_ids_str.split(',')]
        except ValueError:
            self.stdout.write(self.style.ERROR('❌ IDs de cours invalides. Utilisez: --course-ids "1,2,3"'))
            return
        
        self.stdout.write(f'🚀 Génération de séquence pour {len(course_ids)} cours...')
        self.stdout.write('-' * 50)
        
        # Vérifier que les cours existent
        courses = Course.objects.filter(id__in=course_ids, is_published=True)
        
        if courses.count() != len(course_ids):
            found_ids = list(courses.values_list('id', flat=True))
            missing_ids = [id for id in course_ids if id not in found_ids]
            self.stdout.write(self.style.WARNING(f'⚠️  Cours manquants: {missing_ids}'))
            self.stdout.write(self.style.WARNING(f'📚 Cours trouvés: {found_ids}'))
        
        if courses.count() == 0:
            self.stdout.write(self.style.ERROR('❌ Aucun cours valide trouvé'))
            return
        
        # Générer la séquence automatique
        sequence_data = self.generate_sequence_from_courses(courses, weeks_per_course)
        
        # Afficher la séquence générée
        self.stdout.write('📋 SÉQUENCE GÉNÉRÉE:')
        for i, module in enumerate(sequence_data['modules'], 1):
            course_names = ', '.join([c.title for c in module['courses']])
            self.stdout.write(f'  {i}. {module["name"]}')
            self.stdout.write(f'     Cours: {course_names}')
            self.stdout.write(f'     Durée: {module["duration_weeks"]} semaines')
            self.stdout.write(f'     Compétences: {", ".join(module["skills"])}')
            self.stdout.write('')
        
        if not dry_run:
            # Créer le template
            template = self.create_template(
                name, 
                sequence_data, 
                structure, 
                level,
                courses
            )
            
            if template:
                self.stdout.write(self.style.SUCCESS(f'✅ Template "{name}" créé avec succès!'))
                self.stdout.write(f'   📊 {len(sequence_data["modules"])} modules')
                self.stdout.write(f'   ⏱️ {sequence_data["total_duration_weeks"]} semaines')
                self.stdout.write(f'   📚 {courses.count()} cours associés')
            else:
                self.stdout.write(self.style.WARNING('⚠️  Template existe déjà'))
        else:
            self.stdout.write(self.style.WARNING('🔍 MODE SIMULATION - Aucune sauvegarde'))

    def generate_sequence_from_courses(self, courses, weeks_per_course=1.5):
        """Génère une séquence structurée à partir des cours"""
        
        modules = []
        total_weeks = 0
        
        for i, course in enumerate(courses, 1):
            # Déterminer la catégorie et les compétences selon le type de cours
            category, skills = self.get_category_and_skills(course)
            
            module = {
                'id': f'module_auto_{i}',
                'name': f'Module {i} - {course.title[:30]}',
                'category': category,
                'courses': [course.id],
                'order': i,
                'prerequisites': [f'module_auto_{i-1}'] if i > 1 else [],
                'duration_weeks': weeks_per_course,
                'skills': skills,
                'description': f'Module basé sur {course.title}',
                'objectives': [
                    f'Maîtriser {course.title}',
                    f'Appliquer les compétences de {category}'
                ]
            }
            
            modules.append(module)
            total_weeks += weeks_per_course
        
        return {
            'modules': modules,
            'total_duration_weeks': round(total_weeks, 1),
            'certification_required': len(courses) > 2,  # Certification si plus de 2 cours
            'assessment_type': 'mixed' if len(courses) > 2 else 'quiz',
            'learning_outcomes': [
                f'Maîtriser les {len(courses)} cours sélectionnés',
                'Développer les compétences pratiques',
                'Appliquer les connaissances théoriques'
            ],
            'generation_method': 'automatic_from_courses',
            'source_courses': [c.id for c in courses]
        }

    def get_category_and_skills(self, course):
        """Détermine la catégorie et les compétences selon le cours"""
        
        title_lower = course.title.lower()
        
        # Logique de classification basée sur le titre
        if any(keyword in title_lower for keyword in ['cadre', 'réglementaire', 'loi', 'légal']):
            return 'CADRE RÉGLEMENTAIRE', ['base_concepts', 'understanding', 'legal_framework']
        
        elif any(keyword in title_lower for keyword in ['déclaration', 'naissance', 'décès', 'mariage']):
            return 'DÉCLARATIONS', ['form_filling', 'procedures', 'document_processing']
        
        elif any(keyword in title_lower for keyword in ['acte', 'certificat', 'extrait']):
            return 'ACTES', ['certificate_creation', 'document_management', 'legal_writing']
        
        elif any(keyword in title_lower for keyword in ['registre', 'archiv', 'conservation']):
            return 'REGISTRES', ['record_keeping', 'archiving', 'data_management']
        
        elif any(keyword in title_lower for keyword in ['statistique', 'donnée', 'rapport']):
            return 'STATISTIQUES', ['data_analysis', 'reporting', 'performance_indicators']
        
        elif any(keyword in title_lower for keyword in ['digital', 'numérique', 'informatique']):
            return 'DIGITALISATION', ['digital_tools', 'computer_skills', 'automation']
        
        else:
            return 'COMPÉTENCES TRANSVERSALES', ['communication', 'teamwork', 'problem_solving']

    def create_template(self, name, sequence_data, structure, level, courses):
        """Crée le template dans la base de données"""
        
        # Vérifier si le template existe déjà
        if LearningPathTemplate.objects.filter(name=name).exists():
            return None
        
        # Créer le template
        template = LearningPathTemplate.objects.create(
            name=name,
            description=f"Parcours généré automatiquement à partir de {len(courses)} cours ({structure})",
            structure=structure,
            level=level,
            sequence=sequence_data,
            total_duration_weeks=sequence_data["total_duration_weeks"],
            certification_required=sequence_data["certification_required"],
            assessment_type=sequence_data["assessment_type"],
            learning_outcomes=sequence_data["learning_outcomes"],
            is_active=True
        )
        
        # Associer les cours
        template.courses.set(courses)
        
        return template
