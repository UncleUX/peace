"""
Management command pour créer les templates de parcours d'apprentissage de niveau avancé
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q
from courses.models import LearningPathTemplate, Course, Category


class Command(BaseCommand):
    help = 'Crée les templates de parcours d\'apprentissage de niveau avancé'

    def handle(self, *args, **options):
        self.stdout.write("🚀 Création des templates de parcours de niveau avancé...")
        
        # Créer les templates avancés
        templates_created = self.create_advanced_templates()
        
        # Afficher le résumé
        self.stdout.write(self.style.SUCCESS(f"\n✅ {len(templates_created)} templates avancés créés avec succès !"))
        
        for template in templates_created:
            self.stdout.write(f"   📚 {template.name} - {template.get_structure_display()} ({template.get_level_display()})")
        
        self.stdout.write("\n🎯 Templates avancés prêts à être assignés aux utilisateurs !")

    def create_advanced_templates(self):
        """Crée les templates de parcours avancés"""
        templates = []
        
        # Template 1: Expert Commune
        template1 = self.create_commune_expert_template()
        if template1:
            templates.append(template1)
        
        # Template 2: Expert Santé
        template2 = self.create_sante_expert_template()
        if template2:
            templates.append(template2)
        
        # Template 3: Directeur BUNEC
        template3 = self.create_bunec_director_template()
        if template3:
            templates.append(template3)
        
        # Template 4: Chercheur Universitaire
        template4 = self.create_university_researcher_template()
        if template4:
            templates.append(template4)
        
        # Template 5: Senior Consultant
        template5 = self.create_senior_consultant_template()
        if template5:
            templates.append(template5)
        
        # Template 6: Expert Multi-structures
        template6 = self.create_multi_structure_expert_template()
        if template6:
            templates.append(template6)
        
        return templates

    def create_commune_expert_template(self):
        """Template pour les experts de commune"""
        try:
            # Récupérer les catégories
            intro_category = Category.objects.filter(name__icontains="introduction").first()
            forms_category = Category.objects.filter(name__icontains="enregistrement").first()
            
            # Créer des catégories avancées si nécessaire
            expert_category, created = Category.objects.get_or_create(
                name="Expertise Commune",
                defaults={
                    "slug": "expertise-commune",
                    "description": "Formation expert pour les agents de commune"
                }
            )
            
            leadership_category, created = Category.objects.get_or_create(
                name="Leadership Communal",
                defaults={
                    "slug": "leadership-communal",
                    "description": "Compétences de leadership pour les responsables communaux"
                }
            )
            
            categories = [cat for cat in [intro_category, forms_category, expert_category, leadership_category] if cat]
            
            # Récupérer tous les cours disponibles
            available_courses = Course.objects.all()
            
            if available_courses.count() < 6:
                self.stdout.write(self.style.WARNING("⚠️ Pas assez de cours pour template Expert Commune"))
                return None
            
            template = LearningPathTemplate.objects.create(
                name="Expert Commune",
                structure="commune",
                level="advanced",
                description="Parcours expert pour les agents de commune expérimentés. Leadership, gestion d'équipe, expertise juridique avancée, et coordination inter-administrative.",
                estimated_duration=timedelta(weeks=20)
            )
            
            template.courses.set(available_courses[:8])
            template.categories.set(categories)
            
            template.sequence = {
                "modules": [
                    {
                        "id": "module_leadership",
                        "name": "Leadership et Management",
                        "courses": list(available_courses.values_list('id', flat=True)[:2]),
                        "order": 1,
                        "prerequisites": [],
                        "duration_weeks": 6
                    },
                    {
                        "id": "module_expertise",
                        "name": "Expertise Juridique Avancée",
                        "courses": list(available_courses.values_list('id', flat=True)[2:4]),
                        "order": 2,
                        "prerequisites": ["module_leadership"],
                        "duration_weeks": 5
                    },
                    {
                        "id": "module_coordination",
                        "name": "Coordination Inter-administrative",
                        "courses": list(available_courses.values_list('id', flat=True)[4:6]),
                        "order": 3,
                        "prerequisites": ["module_leadership", "module_expertise"],
                        "duration_weeks": 5
                    },
                    {
                        "id": "module_innovation",
                        "name": "Innovation et Digitalisation",
                        "courses": list(available_courses.values_list('id', flat=True)[6:8]),
                        "order": 4,
                        "prerequisites": ["module_leadership"],
                        "duration_weeks": 4
                    }
                ],
                "total_duration_weeks": 20,
                "certification_required": True,
                "assessment_type": "leadership"
            }
            
            template.save()
            return template
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Erreur création template Expert Commune: {e}"))
            return None

    def create_sante_expert_template(self):
        """Template pour les experts du Ministère de la Santé"""
        try:
            # Créer des catégories santé avancées
            medical_expertise_category, created = Category.objects.get_or_create(
                name="Expertise Médicale Avancée",
                defaults={
                    "slug": "expertise-medicale-avancee",
                    "description": "Formation médicale avancée pour les experts santé"
                }
            )
            
            hospital_coordination_category, created = Category.objects.get_or_create(
                name="Coordination Hospitalière",
                defaults={
                    "slug": "coordination-hospitaliere",
                    "description": "Coordination avec les services hospitaliers"
                }
            )
            
            research_category, created = Category.objects.get_or_create(
                name="Recherche Santé",
                defaults={
                    "slug": "recherche-sante",
                    "description": "Recherche et développement dans le domaine santé"
                }
            )
            
            available_courses = Course.objects.filter(
                Q(title__icontains="santé") |
                Q(title__icontains="medical") |
                Q(title__icontains="hospital") |
                Q(title__icontains="research")
            )
            
            if available_courses.count() < 4:
                self.stdout.write(self.style.WARNING("⚠️ Pas assez de cours pour template Expert Santé"))
                return None
            
            template = LearningPathTemplate.objects.create(
                name="Expert Santé",
                structure="minsante",
                level="advanced",
                description="Parcours expert pour les professionnels de santé. Expertise médicale avancée, coordination hospitalière, recherche santé, et leadership dans le domaine médical.",
                estimated_duration=timedelta(weeks=24)
            )
            
            template.courses.set(available_courses[:6])
            template.categories.set([medical_expertise_category, hospital_coordination_category, research_category])
            
            template.sequence = {
                "modules": [
                    {
                        "id": "module_medical_expertise",
                        "name": "Expertise Médicale Avancée",
                        "courses": list(available_courses[:2]),
                        "order": 1,
                        "prerequisites": [],
                        "duration_weeks": 8
                    },
                    {
                        "id": "module_hospital_coordination",
                        "name": "Coordination Hospitalière",
                        "courses": list(available_courses[2:4]),
                        "order": 2,
                        "prerequisites": ["module_medical_expertise"],
                        "duration_weeks": 6
                    },
                    {
                        "id": "module_research",
                        "name": "Recherche et Innovation",
                        "courses": list(available_courses[4:6]),
                        "order": 3,
                        "prerequisites": ["module_medical_expertise", "module_hospital_coordination"],
                        "duration_weeks": 6
                    },
                    {
                        "id": "module_leadership",
                        "name": "Leadership Santé",
                        "courses": list(available_courses[6:8]),
                        "order": 4,
                        "prerequisites": ["module_medical_expertise"],
                        "duration_weeks": 4
                    }
                ],
                "total_duration_weeks": 24,
                "certification_required": True,
                "assessment_type": "expert"
            }
            
            template.save()
            return template
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Erreur création template Expert Santé: {e}"))
            return None

    def create_bunec_director_template(self):
        """Template pour les directeurs BUNEC"""
        try:
            # Créer des catégories BUNEC avancées
            strategy_category, created = Category.objects.get_or_create(
                name="Stratégie BUNEC",
                defaults={
                    "slug": "strategie-bunec",
                    "description": "Planification stratégique pour le BUNEC"
                }
            )
            
            policy_category, created = Category.objects.get_or_create(
                name="Politiques Publiques",
                defaults={
                    "slug": "politiques-publiques",
                    "description": "Élaboration des politiques publiques en état civil"
                }
            )
            
            international_category, created = Category.objects.get_or_create(
                name="Coopération Internationale",
                defaults={
                    "slug": "cooperation-internationale",
                    "description": "Coopération internationale en état civil"
                }
            )
            
            available_courses = Course.objects.filter(
                Q(title__icontains="bunec") |
                Q(title__icontains="strateg") |
                Q(title__icontains="policy") |
                Q(title__icontains="international")
            )
            
            if available_courses.count() < 4:
                self.stdout.write(self.style.WARNING("⚠️ Pas assez de cours pour template Directeur BUNEC"))
                return None
            
            template = LearningPathTemplate.objects.create(
                name="Directeur BUNEC",
                structure="bunec",
                level="advanced",
                description="Parcours pour les directeurs et hauts responsables BUNEC. Planification stratégique, politiques publiques, coopération internationale, et leadership institutionnel.",
                estimated_duration=timedelta(weeks=28)
            )
            
            template.courses.set(available_courses[:8])
            template.categories.set([strategy_category, policy_category, international_category])
            
            template.sequence = {
                "modules": [
                    {
                        "id": "module_strategic_planning",
                        "name": "Planification Stratégique",
                        "courses": list(available_courses[:2]),
                        "order": 1,
                        "prerequisites": [],
                        "duration_weeks": 8
                    },
                    {
                        "id": "module_policy_development",
                        "name": "Développement des Politiques",
                        "courses": list(available_courses[2:4]),
                        "order": 2,
                        "prerequisites": ["module_strategic_planning"],
                        "duration_weeks": 6
                    },
                    {
                        "id": "module_international_cooperation",
                        "name": "Coopération Internationale",
                        "courses": list(available_courses[4:6]),
                        "order": 3,
                        "prerequisites": ["module_strategic_planning", "module_policy_development"],
                        "duration_weeks": 7
                    },
                    {
                        "id": "module_institutional_leadership",
                        "name": "Leadership Institutionnel",
                        "courses": list(available_courses[6:8]),
                        "order": 4,
                        "prerequisites": ["module_strategic_planning"],
                        "duration_weeks": 7
                    }
                ],
                "total_duration_weeks": 28,
                "certification_required": True,
                "assessment_type": "executive"
            }
            
            template.save()
            return template
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Erreur création template Directeur BUNEC: {e}"))
            return None

    def create_university_researcher_template(self):
        """Template pour les chercheurs universitaires"""
        try:
            # Créer des catégories recherche avancées
            advanced_research_category, created = Category.objects.get_or_create(
                name="Recherche Avancée",
                defaults={
                    "slug": "recherche-avancee",
                    "description": "Méthodologie de recherche avancée"
                }
            )
            
            statistics_category, created = Category.objects.get_or_create(
                name="Statistiques Avancées",
                defaults={
                    "slug": "statistiques-avancees",
                    "description": "Statistiques et analyse de données avancées"
                }
            )
            
            publication_category, created = Category.objects.get_or_create(
                name="Publication Scientifique",
                defaults={
                    "slug": "publication-scientifique",
                    "description": "Rédaction et publication scientifique"
                }
            )
            
            available_courses = Course.objects.filter(
                Q(title__icontains="research") |
                Q(title__icontains="statistic") |
                Q(title__icontains="publication") |
                Q(title__icontains="academic")
            )
            
            if available_courses.count() < 4:
                self.stdout.write(self.style.WARNING("⚠️ Pas assez de cours pour template Chercheur Universitaire"))
                return None
            
            template = LearningPathTemplate.objects.create(
                name="Chercheur Universitaire",
                structure="universite",
                level="advanced",
                description="Parcours pour les chercheurs et universitaires. Méthodologie de recherche avancée, statistiques, publication scientifique, et expertise académique.",
                estimated_duration=timedelta(weeks=26)
            )
            
            template.courses.set(available_courses[:6])
            template.categories.set([advanced_research_category, statistics_category, publication_category])
            
            template.sequence = {
                "modules": [
                    {
                        "id": "module_research_methodology",
                        "name": "Méthodologie de Recherche",
                        "courses": list(available_courses[:2]),
                        "order": 1,
                        "prerequisites": [],
                        "duration_weeks": 8
                    },
                    {
                        "id": "module_advanced_statistics",
                        "name": "Statistiques Avancées",
                        "courses": list(available_courses[2:4]),
                        "order": 2,
                        "prerequisites": ["module_research_methodology"],
                        "duration_weeks": 6
                    },
                    {
                        "id": "module_scientific_publication",
                        "name": "Publication Scientifique",
                        "courses": list(available_courses[4:6]),
                        "order": 3,
                        "prerequisites": ["module_research_methodology", "module_advanced_statistics"],
                        "duration_weeks": 6
                    },
                    {
                        "id": "module_academic_leadership",
                        "name": "Leadership Académique",
                        "courses": list(available_courses[6:8]),
                        "order": 4,
                        "prerequisites": ["module_research_methodology"],
                        "duration_weeks": 6
                    }
                ],
                "total_duration_weeks": 26,
                "certification_required": True,
                "assessment_type": "research"
            }
            
            template.save()
            return template
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Erreur création template Chercheur Universitaire: {e}"))
            return None

    def create_senior_consultant_template(self):
        """Template pour les consultants seniors"""
        try:
            # Créer des catégories consulting avancées
            senior_consulting_category, created = Category.objects.get_or_create(
                name="Consulting Senior",
                defaults={
                    "slug": "consulting-senior",
                    "description": "Services de consulting senior"
                }
            )
            
            business_category, created = Category.objects.get_or_create(
                name="Business Development",
                defaults={
                    "slug": "business-development",
                    "description": "Développement commercial et gestion d'entreprise"
                }
            )
            
            transformation_category, created = Category.objects.get_or_create(
                name="Transformation Digitale",
                defaults={
                    "slug": "transformation-digitale",
                    "description": "Transformation numérique et innovation"
                }
            )
            
            available_courses = Course.objects.filter(
                Q(title__icontains="consult") |
                Q(title__icontains="business") |
                Q(title__icontains="digital") |
                Q(title__icontains="transform")
            )
            
            if available_courses.count() < 4:
                self.stdout.write(self.style.WARNING("⚠️ Pas assez de cours pour template Senior Consultant"))
                return None
            
            template = LearningPathTemplate.objects.create(
                name="Senior Consultant",
                structure="consultant",
                level="advanced",
                description="Parcours pour consultants seniors expérimentés. Consulting stratégique, business development, transformation digitale, et expertise sectorielle.",
                estimated_duration=timedelta(weeks=22)
            )
            
            template.courses.set(available_courses[:6])
            template.categories.set([senior_consulting_category, business_category, transformation_category])
            
            template.sequence = {
                "modules": [
                    {
                        "id": "module_strategic_consulting",
                        "name": "Consulting Stratégique",
                        "courses": list(available_courses[:2]),
                        "order": 1,
                        "prerequisites": [],
                        "duration_weeks": 6
                    },
                    {
                        "id": "module_business_development",
                        "name": "Business Development",
                        "courses": list(available_courses[2:4]),
                        "order": 2,
                        "prerequisites": ["module_strategic_consulting"],
                        "duration_weeks": 6
                    },
                    {
                        "id": "module_digital_transformation",
                        "name": "Transformation Digitale",
                        "courses": list(available_courses[4:6]),
                        "order": 3,
                        "prerequisites": ["module_strategic_consulting", "module_business_development"],
                        "duration_weeks": 5
                    },
                    {
                        "id": "module_sectorial_expertise",
                        "name": "Expertise Sectorielle",
                        "courses": list(available_courses[6:8]),
                        "order": 4,
                        "prerequisites": ["module_strategic_consulting"],
                        "duration_weeks": 5
                    }
                ],
                "total_duration_weeks": 22,
                "certification_required": True,
                "assessment_type": "executive"
            }
            
            template.save()
            return template
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Erreur création template Senior Consultant: {e}"))
            return None

    def create_multi_structure_expert_template(self):
        """Template pour les experts multi-structures"""
        try:
            # Créer des catégories multi-structures avancées
            integration_category, created = Category.objects.get_or_create(
                name="Intégration Systèmes",
                defaults={
                    "slug": "integration-systemes",
                    "description": "Intégration des systèmes d'état civil"
                }
            )
            
            innovation_category, created = Category.objects.get_or_create(
                name="Innovation État Civil",
                defaults={
                    "slug": "innovation-etat-civil",
                    "description": "Innovation dans les services d'état civil"
                }
            )
            
            governance_category, created = Category.objects.get_or_create(
                name="Gouvernance",
                defaults={
                    "slug": "gouvernance-etat-civil",
                    "description": "Gouvernance des systèmes d'état civil"
                }
            )
            
            available_courses = Course.objects.all()
            
            if available_courses.count() < 8:
                self.stdout.write(self.style.WARNING("⚠️ Pas assez de cours pour template Expert Multi-structures"))
                return None
            
            template = LearningPathTemplate.objects.create(
                name="Expert Multi-structures",
                structure="multi_structure",
                level="advanced",
                description="Parcours expert pour les professionnels travaillant avec plusieurs structures. Intégration des systèmes, innovation, gouvernance, et leadership transversal.",
                estimated_duration=timedelta(weeks=30)
            )
            
            template.courses.set(available_courses[:10])
            template.categories.set([integration_category, innovation_category, governance_category])
            
            template.sequence = {
                "modules": [
                    {
                        "id": "module_system_integration",
                        "name": "Intégration des Systèmes",
                        "courses": list(available_courses[:3]),
                        "order": 1,
                        "prerequisites": [],
                        "duration_weeks": 8
                    },
                    {
                        "id": "module_cross_structure_coordination",
                        "name": "Coordination Inter-structures",
                        "courses": list(available_courses[3:5]),
                        "order": 2,
                        "prerequisites": ["module_system_integration"],
                        "duration_weeks": 7
                    },
                    {
                        "id": "module_innovation_strategy",
                        "name": "Stratégie d'Innovation",
                        "courses": list(available_courses[5:7]),
                        "order": 3,
                        "prerequisites": ["module_system_integration", "module_cross_structure_coordination"],
                        "duration_weeks": 7
                    },
                    {
                        "id": "module_governance_leadership",
                        "name": "Gouvernance et Leadership",
                        "courses": list(available_courses[7:10]),
                        "order": 4,
                        "prerequisites": ["module_system_integration", "module_cross_structure_coordination"],
                        "duration_weeks": 8
                    }
                ],
                "total_duration_weeks": 30,
                "certification_required": True,
                "assessment_type": "executive"
            }
            
            template.save()
            return template
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Erreur création template Expert Multi-structures: {e}"))
            return None
