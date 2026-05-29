from django.core.management.base import BaseCommand
from courses.models import LearningPathTemplate, Course
import json
from datetime import datetime

class Command(BaseCommand):
    help = 'Valide les cours et génère des séquences automatiquement'

    def add_arguments(self, parser):
        parser.add_argument('--course-ids', type=str, required=True, help='IDs des cours séparés par virgules')
        parser.add_argument('--name', type=str, help='Nom du parcours (optionnel)')
        parser.add_argument('--structure', type=str, default='commune', help='Structure cible')
        parser.add_argument('--level', type=str, default='débutant', help='Niveau du parcours')
        parser.add_argument('--output', type=str, help='Fichier de sortie JSON (optionnel)')
        parser.add_argument('--dry-run', action='store_true', help='Simulation sans sauvegarder')
        parser.add_argument('--interactive', action='store_true', help='Mode interactif')

    def handle(self, *args, **options):
        course_ids_str = options['course_ids']
        name = options.get('name')
        structure = options['structure']
        level = options['level']
        output_file = options.get('output')
        dry_run = options['dry_run']
        interactive = options['interactive']
        
        self.stdout.write('🔍 VALIDATION ET GÉNÉRATION DE SÉQUENCE')
        self.stdout.write('=' * 60)
        
        # Parser les IDs
        try:
            course_ids = [int(id.strip()) for id in course_ids_str.split(',')]
        except ValueError:
            self.stdout.write(self.style.ERROR('❌ Format d\'IDs invalide. Utilisez: --course-ids "1,2,3"'))
            return
        
        # Étape 1: Validation des cours
        self.stdout.write('\n📋 ÉTAPE 1: VALIDATION DES COURS')
        self.stdout.write('-' * 40)
        
        courses = Course.objects.filter(id__in=course_ids)
        validation_results = self.validate_courses(courses, course_ids)
        
        if not validation_results['all_valid']:
            self.stdout.write(self.style.ERROR('❌ Validation échouée'))
            for error in validation_results['errors']:
                self.stdout.write(f'   • {error}')
            return
        
        self.stdout.write(self.style.SUCCESS('✅ Tous les cours sont valides'))
        self.stdout.write(f'   📚 {validation_results["count"]} cours trouvés')
        
        # Étape 2: Analyse et classification
        self.stdout.write('\n📊 ÉTAPE 2: ANALYSE DES COURS')
        self.stdout.write('-' * 40)
        
        analysis = self.analyze_courses(courses)
        self.display_analysis(analysis)
        
        # Étape 3: Génération de la séquence
        self.stdout.write('\n🚀 ÉTAPE 3: GÉNÉRATION DE SÉQUENCE')
        self.stdout.write('-' * 40)
        
        sequence_data = self.generate_sequence(analysis, structure, level)
        
        # Étape 4: Validation de la séquence
        self.stdout.write('\n✅ ÉTAPE 4: VALIDATION DE SÉQUENCE')
        self.stdout.write('-' * 40)
        
        sequence_validation = self.validate_sequence(sequence_data)
        self.display_sequence_validation(sequence_validation)
        
        if not sequence_validation['valid']:
            self.stdout.write(self.style.ERROR('❌ Séquence invalide'))
            return
        
        # Étape 5: Sauvegarde ou affichage
        if not dry_run:
            self.save_sequence(sequence_data, name, structure, level, courses, output_file)
        else:
            self.display_sequence(sequence_data, name)
        
        # Mode interactif
        if interactive:
            self.interactive_mode(sequence_data, courses)

    def validate_courses(self, courses, course_ids):
        """Valide les cours fournis"""
        
        results = {
            'all_valid': True,
            'count': 0,
            'errors': [],
            'valid_courses': []
        }
        
        found_ids = []
        for course_id in course_ids:
            try:
                course = courses.get(id=course_id)
                if course and course.is_published:
                    results['valid_courses'].append(course)
                    found_ids.append(course_id)
                    results['count'] += 1
                else:
                    results['errors'].append(f'Course {course_id}: non publié ou inexistant')
                    results['all_valid'] = False
            except Course.DoesNotExist:
                results['errors'].append(f'Course {course_id}: inexistant')
                results['all_valid'] = False
        
        missing_ids = [id for id in course_ids if id not in found_ids]
        if missing_ids:
            results['errors'].append(f'Cours manquants: {missing_ids}')
            results['all_valid'] = False
        
        return results

    def analyze_courses(self, courses):
        """Analyse et classe les cours"""
        
        analysis = {
            'courses': list(courses),
            'categories': {},
            'difficulty_levels': {},
            'themes': {},
            'prerequisites': {},
            'recommended_order': []
        }
        
        for course in courses:
            # Classification par catégorie
            category = self.classify_course(course)
            if category not in analysis['categories']:
                analysis['categories'][category] = []
            analysis['categories'][category].append(course)
            
            # Classification par niveau
            difficulty = self.estimate_difficulty(course)
            if difficulty not in analysis['difficulty_levels']:
                analysis['difficulty_levels'][difficulty] = []
            analysis['difficulty_levels'][difficulty].append(course)
            
            # Classification par thème
            themes = self.extract_themes(course)
            for theme in themes:
                if theme not in analysis['themes']:
                    analysis['themes'][theme] = []
                analysis['themes'][theme].append(course)
        
        # Génération de l'ordre recommandé
        analysis['recommended_order'] = self.generate_optimal_order(analysis)
        
        return analysis

    def classify_course(self, course):
        """Classifie un cours dans une catégorie"""
        
        title = course.title.lower()
        
        if any(keyword in title for keyword in ['cadre', 'réglementaire', 'loi', 'légal', 'législatif']):
            return 'Fondamentaux Juridiques'
        elif any(keyword in title for keyword in ['déclaration', 'naissance', 'décès', 'mariage', 'divorce']):
            return 'Déclarations et Enregistrements'
        elif any(keyword in title for keyword in ['acte', 'certificat', 'extrait', 'reconnaissance']):
            return 'Établissement d\'Actes'
        elif any(keyword in title for keyword in ['registre', 'archiv', 'conservation', 'tenue']):
            return 'Gestion des Registres'
        elif any(keyword in title for keyword in ['statistique', 'donnée', 'rapport', 'indicateur']):
            return 'Production Statistique'
        elif any(keyword in title for keyword in ['digital', 'numérique', 'informatique', 'automatisation']):
            return 'Digitalisation et Outils'
        else:
            return 'Compétences Transversales'

    def estimate_difficulty(self, course):
        """Estime la difficulté d'un cours"""
        
        title = course.title.lower()
        
        if any(keyword in title for keyword in ['fondamentaux', 'introduction', 'base']):
            return 'Débutant'
        elif any(keyword in title for keyword in ['pratique', 'application', 'gestion']):
            return 'Intermédiaire'
        elif any(keyword in title for keyword in ['avancé', 'expertise', 'stratégique', 'complexe']):
            return 'Avancé'
        else:
            return 'Intermédiaire'

    def extract_themes(self, course):
        """Extrait les thèmes d'un cours"""
        
        title = course.title.lower()
        themes = []
        
        theme_keywords = {
            'Juridique': ['loi', 'juridique', 'légal', 'réglementaire'],
            'Procédural': ['procédure', 'processus', 'démarche'],
            'Technique': ['technique', 'outil', 'méthode'],
            'Relationnel': ['relation', 'communication', 'accueil'],
            'Administratif': ['administratif', 'gestion', 'organisation']
        }
        
        for theme, keywords in theme_keywords.items():
            if any(keyword in title for keyword in keywords):
                themes.append(theme)
        
        return themes if themes else ['Général']

    def generate_optimal_order(self, analysis):
        """Génère l'ordre optimal des cours"""
        
        # Logique d'ordonnancement
        order = []
        
        # 1. Commencer par les fondamentaux
        if 'Fondamentaux Juridiques' in analysis['categories']:
            order.extend(analysis['categories']['Fondamentaux Juridiques'])
        
        # 2. Enchaîner avec les déclarations
        if 'Déclarations et Enregistrements' in analysis['categories']:
            order.extend(analysis['categories']['Déclarations et Enregistrements'])
        
        # 3. Puis les actes
        if 'Établissement d\'Actes' in analysis['categories']:
            order.extend(analysis['categories']['Établissement d\'Actes'])
        
        # 4. Gestion des registres
        if 'Gestion des Registres' in analysis['categories']:
            order.extend(analysis['categories']['Gestion des Registres'])
        
        # 5. Digitalisation et outils
        if 'Digitalisation et Outils' in analysis['categories']:
            order.extend(analysis['categories']['Digitalisation et Outils'])
        
        # 6. Statistiques en dernier
        if 'Production Statistique' in analysis['categories']:
            order.extend(analysis['categories']['Production Statistique'])
        
        # Ajouter les cours non classés à la fin
        classified_ids = [c.id for category_courses in analysis['categories'].values() for c in category_courses]
        unclassified = [c for c in analysis['courses'] if c.id not in classified_ids]
        order.extend(unclassified)
        
        return order

    def generate_sequence(self, analysis, structure, level):
        """Génère la séquence validée"""
        
        modules = []
        total_weeks = 0
        
        for i, course in enumerate(analysis['recommended_order'], 1):
            # Déterminer la catégorie et les compétences
            category = self.classify_course(course)
            skills = self.generate_skills_for_category(category, course)
            
            # Calculer la durée selon la difficulté
            difficulty = self.estimate_difficulty(course)
            duration_weeks = self.calculate_duration(difficulty, i)
            
            module = {
                'id': f'module_{i}_{category.lower().replace(" ", "_")}',
                'name': f'Module {i} - {course.title[:40]}',
                'category': category,
                'courses': [course.id],
                'order': i,
                'prerequisites': self.generate_prerequisites(i, analysis['recommended_order'][:i]),
                'duration_weeks': duration_weeks,
                'skills': skills,
                'description': f'Module basé sur {course.title}',
                'objectives': self.generate_objectives(category, course),
                'difficulty_level': difficulty,
                'estimated_hours': duration_weeks * 7 * 8,  # 8h par jour
                'resources': self.generate_resources(category)
            }
            
            modules.append(module)
            total_weeks += duration_weeks
        
        return {
            'modules': modules,
            'total_duration_weeks': total_weeks,
            'certification_required': len(analysis['courses']) > 2,
            'assessment_type': self.determine_assessment_type(analysis),
            'learning_outcomes': self.generate_learning_outcomes(analysis),
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'course_count': len(analysis['courses']),
                'structure': structure,
                'level': level,
                'generation_method': 'automatic_validation'
            }
        }

    def generate_skills_for_category(self, category, course):
        """Génère les compétences selon la catégorie"""
        
        skills_map = {
            'Fondamentaux Juridiques': ['base_concepts', 'understanding', 'legal_framework', 'institutional_knowledge'],
            'Déclarations et Enregistrements': ['form_filling', 'procedures', 'document_processing', 'data_verification'],
            'Établissement d\'Actes': ['certificate_creation', 'legal_writing', 'document_drafting', 'signature_procedures'],
            'Gestion des Registres': ['record_keeping', 'archiving', 'data_management', 'indexing_methods'],
            'Production Statistique': ['statistical_analysis', 'data_collection', 'report_generation', 'performance_indicators'],
            'Digitalisation et Outils': ['digital_tools', 'computer_skills', 'automation', 'software_usage'],
            'Compétences Transversales': ['communication', 'teamwork', 'problem_solving', 'professional_ethics']
        }
        
        return skills_map.get(category, ['general_skills'])

    def generate_prerequisites(self, current_order, previous_courses):
        """Génère les prérequis logiques"""
        
        if current_order == 1:
            return []
        
        # Logique de prérequis
        if current_order <= 3:
            # Les 3 premiers modules peuvent avoir le module 1 comme prérequis
            return [f'module_1_{previous_courses[0].title.lower().replace(" ", "_")}']
        else:
            # Modules avancés nécessitent les modules précédents
            prereqs = []
            for i in range(min(current_order - 1, 3)):
                prereqs.append(f'module_{i+1}_{previous_courses[i].title.lower().replace(" ", "_")}')
            return prereqs

    def calculate_duration(self, difficulty, order):
        """Calcule la durée selon la difficulté et la position"""
        
        base_durations = {
            'Débutant': 2.0,
            'Intermédiaire': 1.5,
            'Avancé': 1.0
        }
        
        base_duration = base_durations.get(difficulty, 1.5)
        
        # Ajuster selon la position (modules avancés plus courts)
        if order > 3:
            return base_duration * 0.8
        return base_duration

    def generate_objectives(self, category, course):
        """Génère les objectifs d'apprentissage"""
        
        objectives_map = {
            'Fondamentaux Juridiques': [
                f'Comprendre les fondamentaux de {course.title}',
                'Maîtriser le cadre juridique de base',
                'Identifier les acteurs et procédures'
            ],
            'Déclarations et Enregistrements': [
                f'Maîtriser les techniques de {course.title}',
                'Appliquer les procédures correctes',
                'Traiter les documents administratifs'
            ],
            'Établissement d\'Actes': [
                f'Savoir rédiger les actes liés à {course.title}',
                'Appliquer les règles de forme et de fond',
                'Gérer les signatures et authentifications'
            ]
        }
        
        return objectives_map.get(category, [f'Maîtriser {course.title}'])

    def generate_resources(self, category):
        """Génère les ressources recommandées"""
        
        resources_map = {
            'Fondamentaux Juridiques': ['code_civil', 'textes_lois', 'guide_procedures'],
            'Déclarations et Enregistrements': ['formulaires_types', 'guide_declarations', 'checklists'],
            'Établissement d\'Actes': ['modeles_actes', 'guide_redaction', 'formulaires_types'],
            'Gestion des Registres': ['guide_registres', 'procedures_archivage', 'software_tools'],
            'Production Statistique': ['guide_statistiques', 'templates_rapports', 'software_analyse']
        }
        
        return resources_map.get(category, ['documentation_generale'])

    def determine_assessment_type(self, analysis):
        """Détermine le type d'évaluation recommandé"""
        
        course_count = len(analysis['courses'])
        has_advanced = any('Avancé' in levels for levels in analysis['difficulty_levels'].values())
        
        if course_count <= 2:
            return 'quiz'
        elif has_advanced:
            return 'practical_exam'
        else:
            return 'mixed'

    def generate_learning_outcomes(self, analysis):
        """Génère les objectifs d'apprentissage globaux"""
        
        outcomes = []
        
        # Ajouter les objectifs par catégorie
        for category in analysis['categories']:
            if category == 'Fondamentaux Juridiques':
                outcomes.extend([
                    'Comprendre le cadre juridique et institutionnel',
                    'Maîtriser les concepts fondamentaux de l\'état civil'
                ])
            elif category == 'Déclarations et Enregistrements':
                outcomes.extend([
                    'Maîtriser les procédures de déclaration',
                    'Traiter efficacement les demandes des usagers'
                ])
            elif category == 'Établissement d\'Actes':
                outcomes.extend([
                    'Savoir rédiger et délivrer les actes conformes',
                    'Appliquer les règles de forme et de fond'
                ])
        
        # Ajouter les objectifs transversaux
        outcomes.extend([
            'Développer des compétences professionnelles',
            'Assurer la qualité et la conformité des services'
        ])
        
        return list(set(outcomes))  # Éviter les doublons

    def validate_sequence(self, sequence_data):
        """Valide la structure de la séquence"""
        
        validation = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        modules = sequence_data.get('modules', [])
        
        # Validation 1: Ordres uniques
        orders = [m.get('order') for m in modules]
        if len(set(orders)) != len(orders):
            validation['errors'].append('Ordres dupliqués dans les modules')
            validation['valid'] = False
        
        # Validation 2: Prérequis valides
        module_ids = [m.get('id') for m in modules]
        for module in modules:
            prereqs = module.get('prerequisites', [])
            for prereq in prereqs:
                if prereq not in module_ids:
                    validation['errors'].append(f'Prérequis invalide {prereq} pour le module {module.get("id")}')
                    validation['valid'] = False
        
        # Validation 3: Cohérence des durées
        total_weeks = sequence_data.get('total_duration_weeks', 0)
        calculated_weeks = sum(m.get('duration_weeks', 0) for m in modules)
        if abs(total_weeks - calculated_weeks) > 0.1:
            validation['warnings'].append(f'Incohérence de durée: {total_weeks} vs {calculated_weeks}')
        
        # Validation 4: Champs requis
        required_fields = ['modules', 'total_duration_weeks']
        for field in required_fields:
            if field not in sequence_data:
                validation['errors'].append(f'Champ requis manquant: {field}')
                validation['valid'] = False
        
        return validation

    def display_analysis(self, analysis):
        """Affiche les résultats de l'analyse"""
        
        self.stdout.write('📊 RÉSULTATS DE L\'ANALYSE:')
        
        # Catégories trouvées
        self.stdout.write(f'   📂 Catégories identifiées: {len(analysis["categories"])}')
        for category, courses in analysis['categories'].items():
            self.stdout.write(f'      • {category}: {len(courses)} cours')
        
        # Niveaux de difficulté
        self.stdout.write(f'   🎯 Niveaux de difficulté: {len(analysis["difficulty_levels"])}')
        for level, courses in analysis['difficulty_levels'].items():
            self.stdout.write(f'      • {level}: {len(courses)} cours')
        
        # Ordre recommandé
        self.stdout.write(f'   📋 Ordre recommandé: {len(analysis["recommended_order"])} cours')
        for i, course in enumerate(analysis['recommended_order'], 1):
            self.stdout.write(f'      {i}. {course.title} (ID: {course.id})')

    def display_sequence_validation(self, validation):
        """Affiche les résultats de la validation de séquence"""
        
        self.stdout.write('✅ RÉSULTATS DE LA VALIDATION:')
        
        if validation['valid']:
            self.stdout.write(self.style.SUCCESS('   ✅ Séquence VALIDE'))
            self.stdout.write('   • Structure cohérente')
            self.stdout.write('   • Prérequis valides')
            self.stdout.write('   • Ordres corrects')
        else:
            self.stdout.write(self.style.ERROR('   ❌ Séquence INVALIDE'))
            for error in validation['errors']:
                self.stdout.write(self.style.ERROR(f'   • Erreur: {error}'))
        
        if validation['warnings']:
            self.stdout.write(self.style.WARNING('   ⚠️  Avertissements:'))
            for warning in validation['warnings']:
                self.stdout.write(self.style.WARNING(f'   • {warning}'))

    def display_sequence(self, sequence_data, name=None):
        """Affiche la séquence générée"""
        
        display_name = name or 'Séquence Générée'
        self.stdout.write(f'\n📋 {display_name}:')
        self.stdout.write('-' * 50)
        
        modules = sequence_data.get('modules', [])
        
        for module in modules:
            self.stdout.write(f'\n📚 Module {module["order"]}: {module["name"]}')
            self.stdout.write(f'   📂 Catégorie: {module["category"]}')
            self.stdout.write(f'   📚 Cours: {module["courses"]}')
            self.stdout.write(f'   ⏱️  Durée: {module["duration_weeks"]} semaines')
            self.stdout.write(f'   🎯 Compétences: {", ".join(module["skills"])}')
            if module.get('prerequisites'):
                self.stdout.write(f'   🔗 Prérequis: {", ".join(module["prerequisites"])}')
        
        self.stdout.write(f'\n📊 Métriques globales:')
        self.stdout.write(f'   • Total modules: {len(modules)}')
        self.stdout.write(f'   • Durée totale: {sequence_data.get("total_duration_weeks", 0)} semaines')
        self.stdout.write(f'   • Certification: {"Oui" if sequence_data.get("certification_required") else "Non"}')
        self.stdout.write(f'   • Évaluation: {sequence_data.get("assessment_type", "non défini")}')

    def save_sequence(self, sequence_data, name, structure, level, courses, output_file):
        """Sauvegarde la séquence dans la base de données"""
        
        # Nom par défaut
        if not name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            name = f'Parcours Généré_{timestamp}'
        
        # Créer le template
        template = LearningPathTemplate.objects.create(
            name=name,
            description=f'Parcours généré automatiquement le {datetime.now().strftime("%Y-%m-%d %H:%M")} ({structure})',
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
        
        self.stdout.write(self.style.SUCCESS(f'✅ Template "{name}" sauvegardé dans la base de données!'))
        
        # Sauvegarder en fichier si demandé
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(sequence_data, f, indent=2, ensure_ascii=False)
            self.stdout.write(f'💾 Séquence sauvegardée dans: {output_file}')

    def interactive_mode(self, sequence_data, courses):
        """Mode interactif pour modifier la séquence"""
        
        self.stdout.write('\n🔄 MODE INTERACTIF')
        self.stdout.write('Commandes disponibles:')
        self.stdout.write('  • "edit <module_id>" : Modifier un module')
        self.stdout.write('  • "swap <pos1> <pos2>" : Échanger deux modules')
        self.stdout.write('  • "add <course_id>" : Ajouter un cours')
        self.stdout.write('  • "save" : Sauvegarder et quitter')
        self.stdout.write('  • "quit" : Quitter sans sauvegarder')
        
        # Ici vous pourriez implémenter une boucle interactive
        # Pour l'instant, on affiche juste les options
        self.stdout.write('\n💡 Pour une vraie interaction, implémentez une boucle d\'entrée utilisateur')
