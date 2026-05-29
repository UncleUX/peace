"""
Management command pour améliorer les templates avec multi-catégories
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q
from courses.models import LearningPathTemplate, Course, Category


class Command(BaseCommand):
    help = 'Améliore les templates existants avec multi-catégories'

    def handle(self, *args, **options):
        self.stdout.write("🚀 Amélioration des templates avec multi-catégories...")
        
        # Améliorer les templates existants
        enhanced_templates = self.enhance_existing_templates()
        
        # Créer des catégories additionnelles
        categories_created = self.create_additional_categories()
        
        # Afficher le résumé
        self.stdout.write(self.style.SUCCESS(f"\n✅ {len(enhanced_templates)} templates améliorés !"))
        self.stdout.write(self.style.SUCCESS(f"✅ {len(categories_created)} catégories créées !"))
        
        for template in enhanced_templates:
            self.stdout.write(f"   📚 {template.name} - {template.categories.count()} catégories")
        
        self.stdout.write("\n🎯 Templates multi-catégories prêts !")

    def create_additional_categories(self):
        """Crée des catégories additionnelles pour enrichir les parcours"""
        categories_data = [
            {
                "name": "Compétences Relationnelles",
                "slug": "competences-relationnelles",
                "description": "Soft skills et communication"
            },
            {
                "name": "Digitalisation",
                "slug": "digitalisation",
                "description": "Outils numériques et transformation digitale"
            },
            {
                "name": "Législation Avancée",
                "slug": "legislation-avancee",
                "description": "Cadre juridique et législation avancée"
            },
            {
                "name": "Qualité et Standards",
                "slug": "qualite-standards",
                "description": "Contrôle qualité et normes"
            },
            {
                "name": "Gestion de Projet",
                "slug": "gestion-projet",
                "description": "Management de projet et planification"
            },
            {
                "name": "Analyse de Données",
                "slug": "analyse-donnees",
                "description": "Statistiques et analyse de données"
            },
            {
                "name": "Communication Inter-administrative",
                "slug": "communication-inter-admin",
                "description": "Coordination entre administrations"
            },
            {
                "name": "Innovation Pédagogique",
                "slug": "innovation-pedagogique",
                "description": "Méthodes pédagogiques innovantes"
            }
        ]
        
        created_categories = []
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                slug=cat_data["slug"],
                defaults={
                    "name": cat_data["name"],
                    "description": cat_data["description"]
                }
            )
            if created:
                created_categories.append(category)
                self.stdout.write(f"   📁 Catégorie créée : {category.name}")
        
        return created_categories

    def enhance_existing_templates(self):
        """Améliore les templates existants avec plus de catégories"""
        enhanced_templates = []
        
        # Améliorer Agent Commune Débutant
        template1 = self.enhance_commune_beginner_template()
        if template1:
            enhanced_templates.append(template1)
        
        # Améliorer Agent Commune Intermédiaire
        template2 = self.enhance_commune_intermediate_template()
        if template2:
            enhanced_templates.append(template2)
        
        # Améliorer Agent Polyvalent Multi-structures
        template3 = self.enhance_multi_structure_template()
        if template3:
            enhanced_templates.append(template3)
        
        return enhanced_templates

    def enhance_commune_beginner_template(self):
        """Améliore le template Agent Commune Débutant avec plus de catégories"""
        try:
            template = LearningPathTemplate.objects.get(
                name="Agent Commune Débutant",
                structure="commune",
                level="beginner"
            )
            
            # Récupérer toutes les catégories pertinentes
            categories_to_add = []
            
            # Catégories existantes
            intro_category = Category.objects.filter(name__icontains="introduction").first()
            forms_category = Category.objects.filter(name__icontains="enregistrement").first()
            
            # Nouvelles catégories
            relationnelles_category = Category.objects.filter(slug="competences-relationnelles").first()
            digital_category = Category.objects.filter(slug="digitalisation").first()
            communication_category = Category.objects.filter(slug="communication-inter-admin").first()
            
            for cat in [intro_category, forms_category, relationnelles_category, digital_category, communication_category]:
                if cat:
                    categories_to_add.append(cat)
            
            # Ajouter les catégories au template
            if categories_to_add:
                template.categories.set(categories_to_add)
                
                # Mettre à jour la séquence pour inclure les nouvelles catégories
                available_courses = Course.objects.filter(category__in=categories_to_add)
                
                if available_courses.exists():
                    template.courses.set(available_courses[:5])
                    
                    template.sequence = {
                        "modules": [
                            {
                                "id": "module_fondamentaux",
                                "name": "Module Fondamentaux",
                                "category": intro_category.name if intro_category else "Introduction",
                                "courses": list(available_courses.filter(category=intro_category).values_list('id', flat=True)[:2]),
                                "order": 1,
                                "prerequisites": [],
                                "duration_weeks": 2,
                                "skills": ["base_concepts", "understanding"]
                            },
                            {
                                "id": "module_pratique",
                                "name": "Module Pratique",
                                "category": forms_category.name if forms_category else "Formulaires",
                                "courses": list(available_courses.filter(category=forms_category).values_list('id', flat=True)[:2]),
                                "order": 2,
                                "prerequisites": ["module_fondamentaux"],
                                "duration_weeks": 2,
                                "skills": ["form_filling", "procedures"]
                            },
                            {
                                "id": "module_relationnel",
                                "name": "Module Relationnel",
                                "category": relationnelles_category.name if relationnelles_category else "Compétences Relationnelles",
                                "courses": list(available_courses.filter(category=relationnelles_category).values_list('id', flat=True)[:1]),
                                "order": 3,
                                "prerequisites": ["module_fondamentaux"],
                                "duration_weeks": 1,
                                "skills": ["communication", "customer_service"]
                            },
                            {
                                "id": "module_digital",
                                "name": "Module Digital",
                                "category": digital_category.name if digital_category else "Digitalisation",
                                "courses": list(available_courses.filter(category=digital_category).values_list('id', flat=True)[:1]),
                                "order": 4,
                                "prerequisites": ["module_pratique"],
                                "duration_weeks": 1,
                                "skills": ["digital_tools", "computer_skills"]
                            }
                        ],
                        "total_duration_weeks": 6,
                        "certification_required": True,
                        "assessment_type": "mixed",
                        "learning_outcomes": [
                            "Comprendre les fondamentaux de l'état civil",
                            "Maîtriser les formulaires de base",
                            "Développer des compétences relationnelles",
                            "Utiliser les outils numériques"
                        ]
                    }
                    
                    template.save()
                    self.stdout.write(f"   ✅ Template amélioré : {template.name}")
                    return template
            
        except LearningPathTemplate.DoesNotExist:
            self.stdout.write(self.style.WARNING("⚠️ Template Agent Commune Débutant non trouvé"))
            return None
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Erreur amélioration template Commune Débutant: {e}"))
            return None

    def enhance_commune_intermediate_template(self):
        """Améliore le template Agent Commune Intermédiaire"""
        try:
            template = LearningPathTemplate.objects.get(
                name="Agent Commune Intermédiaire",
                structure="commune",
                level="intermediate"
            )
            
            # Récupérer les catégories
            categories_to_add = []
            
            intro_category = Category.objects.filter(name__icontains="introduction").first()
            forms_category = Category.objects.filter(name__icontains="enregistrement").first()
            archive_category = Category.objects.filter(name__icontains="archiv").first()
            legislation_category = Category.objects.filter(slug="legislation-avancee").first()
            quality_category = Category.objects.filter(slug="qualite-standards").first()
            project_category = Category.objects.filter(slug="gestion-projet").first()
            
            for cat in [intro_category, forms_category, archive_category, legislation_category, quality_category, project_category]:
                if cat:
                    categories_to_add.append(cat)
            
            if categories_to_add:
                template.categories.set(categories_to_add)
                
                available_courses = Course.objects.filter(category__in=categories_to_add)
                
                if available_courses.exists():
                    template.courses.set(available_courses[:8])
                    
                    template.sequence = {
                        "modules": [
                            {
                                "id": "module_perfectionnement",
                                "name": "Module Perfectionnement",
                                "category": forms_category.name if forms_category else "Formulaires",
                                "courses": list(available_courses.filter(category=forms_category).values_list('id', flat=True)[:3]),
                                "order": 1,
                                "prerequisites": [],
                                "duration_weeks": 3,
                                "skills": ["advanced_forms", "complex_cases"]
                            },
                            {
                                "id": "module_archives",
                                "name": "Module Archives",
                                "category": archive_category.name if archive_category else "Archives",
                                "courses": list(available_courses.filter(category=archive_category).values_list('id', flat=True)[:2]),
                                "order": 2,
                                "prerequisites": ["module_perfectionnement"],
                                "duration_weeks": 2,
                                "skills": ["archive_management", "document_preservation"]
                            },
                            {
                                "id": "module_legislation",
                                "name": "Module Législation",
                                "category": legislation_category.name if legislation_category else "Législation",
                                "courses": list(available_courses.filter(category=legislation_category).values_list('id', flat=True)[:1]),
                                "order": 3,
                                "prerequisites": ["module_perfectionnement"],
                                "duration_weeks": 2,
                                "skills": ["legal_framework", "compliance"]
                            },
                            {
                                "id": "module_qualite",
                                "name": "Module Qualité",
                                "category": quality_category.name if quality_category else "Qualité",
                                "courses": list(available_courses.filter(category=quality_category).values_list('id', flat=True)[:1]),
                                "order": 4,
                                "prerequisites": ["module_perfectionnement", "module_archives"],
                                "duration_weeks": 1,
                                "skills": ["quality_control", "standards"]
                            },
                            {
                                "id": "module_projet",
                                "name": "Module Projet",
                                "category": project_category.name if project_category else "Gestion de Projet",
                                "courses": list(available_courses.filter(category=project_category).values_list('id', flat=True)[:1]),
                                "order": 5,
                                "prerequisites": ["module_legislation"],
                                "duration_weeks": 2,
                                "skills": ["project_management", "planning"]
                            }
                        ],
                        "total_duration_weeks": 10,
                        "certification_required": True,
                        "assessment_type": "practical",
                        "learning_outcomes": [
                            "Maîtriser les formulaires complexes",
                            "Gérer les archives efficacement",
                            "Comprendre le cadre législatif",
                            "Assurer la qualité des services",
                            "Gérer des projets d'amélioration"
                        ]
                    }
                    
                    template.save()
                    self.stdout.write(f"   ✅ Template amélioré : {template.name}")
                    return template
            
        except LearningPathTemplate.DoesNotExist:
            self.stdout.write(self.style.WARNING("⚠️ Template Agent Commune Intermédiaire non trouvé"))
            return None
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Erreur amélioration template Commune Intermédiaire: {e}"))
            return None

    def enhance_multi_structure_template(self):
        """Améliore le template Agent Polyvalent Multi-structures"""
        try:
            template = LearningPathTemplate.objects.get(
                name="Agent Polyvalent Multi-structures",
                structure="multi_structure",
                level="intermediate"
            )
            
            # Récupérer toutes les catégories pertinentes
            all_categories = Category.objects.all()
            
            # Sélectionner les catégories les plus pertinentes
            priority_categories = []
            priority_slugs = [
                "competences-relationnelles",
                "digitalisation", 
                "legislation-avancee",
                "qualite-standards",
                "gestion-projet",
                "analyse-donnees",
                "communication-inter-admin",
                "innovation-pedagogique"
            ]
            
            for slug in priority_slugs:
                cat = Category.objects.filter(slug=slug).first()
                if cat:
                    priority_categories.append(cat)
            
            # Ajouter quelques catégories existantes
            existing_categories = Category.objects.filter(
                Q(name__icontains="introduction") |
                Q(name__icontains="enregistrement") |
                Q(name__icontains="santé") |
                Q(name__icontains="formation")
            )[:3]
            
            all_selected_categories = list(priority_categories) + list(existing_categories)
            
            if all_selected_categories:
                template.categories.set(all_selected_categories)
                
                available_courses = Course.objects.filter(category__in=all_selected_categories)
                
                if available_courses.exists():
                    template.courses.set(available_courses[:10])
                    
                    template.sequence = {
                        "modules": [
                            {
                                "id": "module_fondamentaux_multi",
                                "name": "Module Fondamentaux Multi-structures",
                                "category": "Introduction",
                                "courses": list(available_courses.values_list('id', flat=True)[:2]),
                                "order": 1,
                                "prerequisites": [],
                                "duration_weeks": 3,
                                "skills": ["multi_structure_basics", "cross_understanding"]
                            },
                            {
                                "id": "module_specialisation",
                                "name": "Module Spécialisation par Structure",
                                "category": "Spécialisation",
                                "courses": list(available_courses.values_list('id', flat=True)[2:4]),
                                "order": 2,
                                "prerequisites": ["module_fondamentaux_multi"],
                                "duration_weeks": 4,
                                "skills": ["structure_specific", "specialized_knowledge"]
                            },
                            {
                                "id": "module_coordination",
                                "name": "Module Coordination Inter-structures",
                                "category": "Coordination",
                                "courses": list(available_courses.values_list('id', flat=True)[4:6]),
                                "order": 3,
                                "prerequisites": ["module_fondamentaux_multi", "module_specialisation"],
                                "duration_weeks": 4,
                                "skills": ["inter_admin_coordination", "collaboration"]
                            },
                            {
                                "id": "module_analyse",
                                "name": "Module Analyse et Données",
                                "category": "Analyse",
                                "courses": list(available_courses.values_list('id', flat=True)[6:8]),
                                "order": 4,
                                "prerequisites": ["module_coordination"],
                                "duration_weeks": 3,
                                "skills": ["data_analysis", "reporting"]
                            },
                            {
                                "id": "module_innovation",
                                "name": "Module Innovation et Digital",
                                "category": "Innovation",
                                "courses": list(available_courses.values_list('id', flat=True)[8:10]),
                                "order": 5,
                                "prerequisites": ["module_specialisation"],
                                "duration_weeks": 4,
                                "skills": ["digital_innovation", "process_improvement"]
                            }
                        ],
                        "total_duration_weeks": 18,
                        "certification_required": True,
                        "assessment_type": "comprehensive",
                        "learning_outcomes": [
                            "Comprendre toutes les structures d'état civil",
                            "Maîtriser la coordination inter-administrative",
                            "Analyser les données et générer des rapports",
                            "Innover dans les processus existants",
                            "Utiliser les outils numériques efficacement"
                        ]
                    }
                    
                    template.save()
                    self.stdout.write(f"   ✅ Template amélioré : {template.name}")
                    return template
            
        except LearningPathTemplate.DoesNotExist:
            self.stdout.write(self.style.WARNING("⚠️ Template Multi-structures non trouvé"))
            return None
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Erreur amélioration template Multi-structures: {e}"))
            return None
