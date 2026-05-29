from django.core.management.base import BaseCommand
from courses.models import LearningPathTemplate, Course
import json

class Command(BaseCommand):
    help = 'Génère un parcours d\'apprentissage structuré'

    def add_arguments(self, parser):
        parser.add_argument('--name', type=str, default='Parcours Agent État Civil')
        parser.add_argument('--structure', type=str, default='commune')
        parser.add_argument('--level', type=str, default='débutant')
        parser.add_argument('--json-file', type=str, help='Fichier JSON avec la structure')

    def handle(self, *args, **options):
        name = options['name']
        structure = options['structure']
        level = options['level']
        json_file = options.get('json_file')
        
        if json_file:
            # Charger depuis un fichier
            with open(json_file, 'r', encoding='utf-8') as f:
                sequence_data = json.load(f)
        else:
            # Utiliser la structure par défaut
            sequence_data = self.get_default_sequence(level)
        
        # Créer le template
        template = LearningPathTemplate.objects.create(
            name=name,
            description=f"Formation complète pour {structure}",
            structure=structure,
            level=level,
            sequence=sequence_data,
            total_duration_weeks=sequence_data.get("total_duration_weeks", 0),
            certification_required=sequence_data.get("certification_required", False),
            assessment_type=sequence_data.get("assessment_type", "mixed"),
            learning_outcomes=sequence_data.get("learning_outcomes", [])
        )
        
        # Ajouter les cours
        self.add_courses_to_template(template, sequence_data)
        
        self.stdout.write(
            self.style.SUCCESS(f'✅ Parcours "{name}" créé avec succès')
        )
        self.stdout.write(f'📚 {len(sequence_data.get("modules", []))} modules')
        self.stdout.write(f'⏱️ {sequence_data.get("total_duration_weeks", 0)} semaines')

    def get_default_sequence(self, level):
        """Retourne la séquence par défaut selon le niveau"""
        
        sequences = {
            "débutant": {
                "modules": [
                    {
                        "id": "module_fondamentaux",
                        "name": "Module Fondamentaux",
                        "category": "INTRODUCTION A L'ETAT CIVIL",
                        "courses": [16],
                        "order": 1,
                        "prerequisites": [],
                        "duration_weeks": 2,
                        "skills": ["base_concepts", "understanding"]
                    },
                    {
                        "id": "module_declarations",
                        "name": "Module Déclarations",
                        "category": "ENREGISTREMENT DES FAITS",
                        "courses": [10],
                        "order": 2,
                        "prerequisites": ["module_fondamentaux"],
                        "duration_weeks": 3,
                        "skills": ["form_filling", "procedures"]
                    }
                ],
                "total_duration_weeks": 5,
                "certification_required": False,
                "assessment_type": "quiz",
                "learning_outcomes": [
                    "Comprendre les fondamentaux de l'état civil",
                    "Maîtriser les déclarations de base"
                ]
            },
            "intermédiaire": {
                "modules": [
                    {
                        "id": "module_actes_complexes",
                        "name": "Module Actes Complexes",
                        "category": "ACTES AVANCÉS",
                        "courses": [12, 13],
                        "order": 1,
                        "prerequisites": [],
                        "duration_weeks": 3,
                        "skills": ["complex_certificates", "legal_documents"]
                    },
                    {
                        "id": "module_registres",
                        "name": "Module Registres",
                        "category": "GESTION DES REGISTRES",
                        "courses": [11],
                        "order": 2,
                        "prerequisites": ["module_actes_complexes"],
                        "duration_weeks": 2,
                        "skills": ["register_management", "archiving"]
                    }
                ],
                "total_duration_weeks": 5,
                "certification_required": True,
                "assessment_type": "mixed",
                "learning_outcomes": [
                    "Maîtriser les actes complexes",
                    "Gérer efficacement les registres"
                ]
            },
            "avancé": {
                "modules": [
                    {
                        "id": "module_digital",
                        "name": "Module Digital",
                        "category": "DIGITALISATION",
                        "courses": [14, 15],
                        "order": 1,
                        "prerequisites": [],
                        "duration_weeks": 3,
                        "skills": ["digital_tools", "statistical_analysis"]
                    },
                    {
                        "id": "module_expertise",
                        "name": "Module Expertise",
                        "category": "EXPERTISE JURIDIQUE",
                        "courses": [],
                        "order": 2,
                        "prerequisites": ["module_digital"],
                        "duration_weeks": 2,
                        "skills": ["legal_expertise", "advisory_role"]
                    }
                ],
                "total_duration_weeks": 5,
                "certification_required": True,
                "assessment_type": "practical_exam",
                "learning_outcomes": [
                    "Maîtriser les outils numériques",
                    "Assurer un rôle d'expertise"
                ]
            }
        }
        
        return sequences.get(level, sequences["débutant"])

    def add_courses_to_template(self, template, sequence_data):
        """Ajoute les cours au template"""
        all_course_ids = []
        for module in sequence_data.get("modules", []):
            all_course_ids.extend(module.get("courses", []))
        
        if all_course_ids:
            courses = Course.objects.filter(id__in=all_course_ids)
            template.courses.set(courses)
