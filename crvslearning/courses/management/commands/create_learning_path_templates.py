"""
Management command pour créer les templates de parcours d'apprentissage initiaux
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q
from courses.models import LearningPathTemplate, Course, Category
from users.models import CustomUser


class Command(BaseCommand):
    help = 'Crée les templates de parcours d\'apprentissage initiaux pour CRVS Learning'

    def handle(self, *args, **options):
        self.stdout.write("🚀 Création des templates de parcours d'apprentissage...")
        
        # Créer les templates de parcours
        templates_created = self.create_learning_path_templates()
        
        # Afficher le résumé
        self.stdout.write(self.style.SUCCESS(f"\n✅ {len(templates_created)} templates créés avec succès !"))
        
        for template in templates_created:
            self.stdout.write(f"   📚 {template.name} - {template.get_structure_display()} ({template.get_level_display()})")
        
        self.stdout.write("\n🎯 Templates prêts à être assignés aux utilisateurs !")

    def create_learning_path_templates(self):
        """Crée les templates de parcours prédéfinis"""
        templates = []
        
        # Template 1: Agent Commune Débutant
        template1 = self.create_commune_beginner_template()
        if template1:
            templates.append(template1)
        
        # Template 2: Agent Commune Intermédiaire
        template2 = self.create_commune_intermediate_template()
        if template2:
            templates.append(template2)
        
        # Template 3: Agent Santé Débutant
        template3 = self.create_sante_beginner_template()
        if template3:
            templates.append(template3)
        
        # Template 4: Agent Santé Intermédiaire
        template4 = self.create_sante_intermediate_template()
        if template4:
            templates.append(template4)
        
        # Template 5: Coordonnateur BUNEC
        template5 = self.create_bunec_coordinator_template()
        if template5:
            templates.append(template5)
        
        # Template 6: Agent Universitaire
        template6 = self.create_university_agent_template()
        if template6:
            templates.append(template6)
        
        # Template 7: Agent ONG
        template7 = self.create_ong_agent_template()
        if template7:
            templates.append(template7)
        
        # Template 8: Consultant État Civil
        template8 = self.create_consultant_template()
        if template8:
            templates.append(template8)
        
        # Template 9: Agent Polyvalent Multi-structures
        template9 = self.create_multi_structure_template()
        if template9:
            templates.append(template9)
        
        return templates

    def create_commune_beginner_template(self):
        """Template pour les agents de commune débutants"""
        try:
            # Récupérer les cours et catégories appropriés
            intro_category = Category.objects.filter(name__icontains="introduction").first()
            forms_category = Category.objects.filter(name__icontains="enregistrement").first()
            
            if not intro_category or not forms_category:
                self.stdout.write(self.style.WARNING("⚠️ Catégories non trouvées pour template Commune Débutant"))
                return None
            
            # Récupérer les cours disponibles
            available_courses = Course.objects.filter(
                category__in=[intro_category, forms_category]
            )
            
            if available_courses.count() < 2:
                self.stdout.write(self.style.WARNING("⚠️ Pas assez de cours disponibles pour template Commune Débutant"))
                return None
            
            template = LearningPathTemplate.objects.create(
                name="Agent Commune Débutant",
                structure="commune",
                level="beginner",
                description="Parcours complet pour les nouveaux agents de commune. Formation aux fondamentaux de l'état civil, aux formulaires de base et à l'accueil des citoyens.",
                estimated_duration=timedelta(weeks=6)
            )
            
            # Ajouter les cours
            template.courses.set(available_courses[:4])  # Limiter à 4 cours
            
            # Ajouter les catégories
            template.categories.set([intro_category, forms_category])
            
            # Définir la séquence
            template.sequence = {
                "modules": [
                    {
                        "id": "module_fondamentaux",
                        "name": "Module Fondamentaux",
                        "courses": list(available_courses.filter(category=intro_category).values_list('id', flat=True)[:2]),
                        "order": 1,
                        "prerequisites": [],
                        "duration_weeks": 2
                    },
                    {
                        "id": "module_pratique",
                        "name": "Module Pratique",
                        "courses": list(available_courses.filter(category=forms_category).values_list('id', flat=True)[:2]),
                        "order": 2,
                        "prerequisites": ["module_fondamentaux"],
                        "duration_weeks": 4
                    }
                ],
                "total_duration_weeks": 6,
                "certification_required": True,
                "assessment_type": "mixed"
            }
            
            template.save()
            return template
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Erreur création template Commune Débutant: {e}"))
            return None

    def create_commune_intermediate_template(self):
        """Template pour les agents de commune intermédiaires"""
        try:
            # Récupérer les catégories
            intro_category = Category.objects.filter(name__icontains="introduction").first()
            forms_category = Category.objects.filter(name__icontains="enregistrement").first()
            archive_category = Category.objects.filter(name__icontains="archiv").first()
            
            categories = [cat for cat in [intro_category, forms_category, archive_category] if cat]
            
            if len(categories) < 2:
                self.stdout.write(self.style.WARNING("⚠️ Catégories insuffisantes pour template Commune Intermédiaire"))
                return None
            
            # Récupérer plus de cours
            available_courses = Course.objects.filter(category__in=categories)
            
            if available_courses.count() < 3:
                self.stdout.write(self.style.WARNING("⚠️ Pas assez de cours pour template Commune Intermédiaire"))
                return None
            
            template = LearningPathTemplate.objects.create(
                name="Agent Commune Intermédiaire",
                structure="commune",
                level="intermediate",
                description="Parcours avancé pour agents expérimentés. Approfondissement des techniques d'enregistrement, gestion des archives complexes et législation avancée.",
                estimated_duration=timedelta(weeks=10)
            )
            
            template.courses.set(available_courses[:6])
            template.categories.set(categories)
            
            template.sequence = {
                "modules": [
                    {
                        "id": "module_perfectionnement",
                        "name": "Module Perfectionnement",
                        "courses": list(available_courses.filter(category=forms_category).values_list('id', flat=True)[:3]),
                        "order": 1,
                        "prerequisites": [],
                        "duration_weeks": 4
                    },
                    {
                        "id": "module_archives",
                        "name": "Module Archives",
                        "courses": list(available_courses.filter(category=archive_category).values_list('id', flat=True)[:2]),
                        "order": 2,
                        "prerequisites": ["module_perfectionnement"],
                        "duration_weeks": 3
                    },
                    {
                        "id": "module_specialisation",
                        "name": "Module Spécialisation",
                        "courses": list(available_courses.filter(category=intro_category).values_list('id', flat=True)[:1]),
                        "order": 3,
                        "prerequisites": ["module_perfectionnement"],
                        "duration_weeks": 3
                    }
                ],
                "total_duration_weeks": 10,
                "certification_required": True,
                "assessment_type": "practical"
            }
            
            template.save()
            return template
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Erreur création template Commune Intermédiaire: {e}"))
            return None

    def create_sante_beginner_template(self):
        """Template pour les agents du Ministère de la Santé débutants"""
        try:
            # Récupérer ou créer des catégories santé
            sante_category, created = Category.objects.get_or_create(
                name="Santé État Civil",
                defaults={
                    "slug": "sante-etat-civil",
                    "description": "Formation pour les agents du Ministère de la Santé"
                }
            )
            
            # Récupérer les cours existants ou créer des cours de base
            available_courses = Course.objects.filter(
                Q(title__icontains="santé") |
                Q(title__icontains="naissance") |
                Q(title__icontains="medical")
            )
            
            if available_courses.count() < 2:
                # Créer des cours de base si nécessaire
                self.stdout.write(self.style.WARNING("⚠️ Création de cours de base pour Santé Débutant"))
                # Note: Les cours devraient être créés manuellement via l'admin
            
            template = LearningPathTemplate.objects.create(
                name="Agent Santé Débutant",
                structure="minsante",
                level="beginner",
                description="Formation spécialisée pour les agents du Ministère de la Santé. Focus sur les actes de naissance en milieu médical, certificats médicaux et collaboration avec les autres structures.",
                estimated_duration=timedelta(weeks=8)
            )
            
            if available_courses.exists():
                template.courses.set(available_courses[:4])
            
            template.categories.set([sante_category])
            
            template.sequence = {
                "modules": [
                    {
                        "id": "module_actes_sante",
                        "name": "Actes de Naissance Santé",
                        "courses": list(available_courses.filter(title__icontains="naissance").values_list('id', flat=True)[:2]),
                        "order": 1,
                        "prerequisites": [],
                        "duration_weeks": 3
                    },
                    {
                        "id": "module_certificats",
                        "name": "Certificats Médicaux",
                        "courses": list(available_courses.filter(title__icontains="certificat").values_list('id', flat=True)[:2]),
                        "order": 2,
                        "prerequisites": ["module_actes_sante"],
                        "duration_weeks": 3
                    },
                    {
                        "id": "module_collaboration",
                        "name": "Collaboration Inter-structures",
                        "courses": list(available_courses.exclude(
                            title__icontains="naissance"
                        ).exclude(
                            title__icontains="certificat"
                        ).values_list('id', flat=True)[:2]),
                        "order": 3,
                        "prerequisites": ["module_actes_sante"],
                        "duration_weeks": 2
                    }
                ],
                "total_duration_weeks": 8,
                "certification_required": True,
                "assessment_type": "mixed"
            }
            
            template.save()
            return template
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Erreur création template Santé Débutant: {e}"))
            return None

    def create_sante_intermediate_template(self):
        """Template pour les agents du Ministère de la Santé intermédiaires"""
        try:
            sante_category = Category.objects.filter(name__icontains="santé").first()
            
            if not sante_category:
                self.stdout.write(self.style.WARNING("⚠️ Catégorie Santé non trouvée"))
                return None
            
            available_courses = Course.objects.filter(
                Q(title__icontains="santé") |
                Q(title__icontains="medical") |
                Q(title__icontains="hospital")
            )
            
            template = LearningPathTemplate.objects.create(
                name="Agent Santé Intermédiaire",
                structure="minsante",
                level="intermediate",
                description="Parcours avancé pour agents de santé expérimentés. Gestion des cas complexes, coordination avec les services hospitaliers et expertise en documentation médicale.",
                estimated_duration=timedelta(weeks=12)
            )
            
            if available_courses.exists():
                template.courses.set(available_courses[:5])
            
            template.categories.set([sante_category])
            
            template.sequence = {
                "modules": [
                    {
                        "id": "module_expertise",
                        "name": "Expertise Médicale",
                        "courses": list(available_courses.values_list('id', flat=True)[:3]),
                        "order": 1,
                        "prerequisites": [],
                        "duration_weeks": 5
                    },
                    {
                        "id": "module_coordination",
                        "name": "Coordination Hospitalière",
                        "courses": list(available_courses.values_list('id', flat=True)[3:5]),
                        "order": 2,
                        "prerequisites": ["module_expertise"],
                        "duration_weeks": 4
                    },
                    {
                        "id": "module_specialisation",
                        "name": "Spécialisation Avancée",
                        "courses": list(available_courses.values_list('id', flat=True)[5:7]),
                        "order": 3,
                        "prerequisites": ["module_expertise", "module_coordination"],
                        "duration_weeks": 3
                    }
                ],
                "total_duration_weeks": 12,
                "certification_required": True,
                "assessment_type": "practical"
            }
            
            template.save()
            return template
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Erreur création template Santé Intermédiaire: {e}"))
            return None

    def create_bunec_coordinator_template(self):
        """Template pour les coordinateurs BUNEC"""
        try:
            # Créer des catégories BUNEC
            management_category, created = Category.objects.get_or_create(
                name="Management BUNEC",
                defaults={
                    "slug": "management-bunec",
                    "description": "Formation pour les coordinateurs et superviseurs BUNEC"
                }
            )
            
            training_category, created = Category.objects.get_or_create(
                name="Formation BUNEC",
                defaults={
                    "slug": "formation-bunec",
                    "description": "Pédagogie et formation pour les formateurs BUNEC"
                }
            )
            
            quality_category, created = Category.objects.get_or_create(
                name="Qualité BUNEC",
                defaults={
                    "slug": "qualite-bunec",
                    "description": "Contrôle qualité et standards BUNEC"
                }
            )
            
            available_courses = Course.objects.filter(
                Q(title__icontains="bunec") |
                Q(title__icontains="formation") |
                Q(title__icontains="qualité")
            )
            
            template = LearningPathTemplate.objects.create(
                name="Coordonnateur BUNEC",
                structure="bunec",
                level="advanced",
                description="Parcours complet pour les coordinateurs et superviseurs BUNEC. Management d'équipes, formation des formateurs, contrôle qualité et planification stratégique.",
                estimated_duration=timedelta(weeks=16)
            )
            
            if available_courses.exists():
                template.courses.set(available_courses[:6])
            
            template.categories.set([management_category, training_category, quality_category])
            
            template.sequence = {
                "modules": [
                    {
                        "id": "module_management",
                        "name": "Management d'Équipe",
                        "courses": list(available_courses.filter(title__icontains="management").values_list('id', flat=True)[:2]),
                        "order": 1,
                        "prerequisites": [],
                        "duration_weeks": 4
                    },
                    {
                        "id": "module_formation",
                        "name": "Formation et Pédagogie",
                        "courses": list(available_courses.filter(title__icontains="formation").values_list('id', flat=True)[:2]),
                        "order": 2,
                        "prerequisites": ["module_management"],
                        "duration_weeks": 4
                    },
                    {
                        "id": "module_qualite",
                        "name": "Contrôle Qualité",
                        "courses": list(available_courses.filter(title__icontains="qualité").values_list('id', flat=True)[:2]),
                        "order": 3,
                        "prerequisites": ["module_management"],
                        "duration_weeks": 4
                    },
                    {
                        "id": "module_strategie",
                        "name": "Planification Stratégique",
                        "courses": list(available_courses.exclude(
                            title__icontains="management"
                        ).exclude(
                            title__icontains="formation"
                        ).exclude(
                            title__icontains="qualité"
                        ).values_list('id', flat=True)[:2]),
                        "order": 4,
                        "prerequisites": ["module_management", "module_formation"],
                        "duration_weeks": 4
                    }
                ],
                "total_duration_weeks": 16,
                "certification_required": True,
                "assessment_type": "leadership"
            }
            
            template.save()
            return template
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Erreur création template BUNEC Coordonnateur: {e}"))
            return None

    def create_university_agent_template(self):
        """Template pour les agents universitaires"""
        try:
            # Créer des catégories universitaires
            theory_category, created = Category.objects.get_or_create(
                name="Théorie Universitaire",
                defaults={
                    "slug": "theorie-universitaire",
                    "description": "Formation théorique pour le milieu universitaire"
                }
            )
            
            research_category, created = Category.objects.get_or_create(
                name="Recherche Démographique",
                defaults={
                    "slug": "recherche-demographique",
                    "description": "Recherche et statistiques démographiques"
                }
            )
            
            available_courses = Course.objects.filter(
                Q(title__icontains="universit") |
                Q(title__icontains="recherche") |
                Q(title__icontains="theorie")
            )
            
            template = LearningPathTemplate.objects.create(
                name="Agent Universitaire",
                structure="universite",
                level="intermediate",
                description="Parcours spécialisé pour les agents universitaires. Approfondissement théorique, techniques de recherche démographique et analyse statistique.",
                estimated_duration=timedelta(weeks=14)
            )
            
            if available_courses.exists():
                template.courses.set(available_courses[:5])
            
            template.categories.set([theory_category, research_category])
            
            template.sequence = {
                "modules": [
                    {
                        "id": "module_theorie",
                        "name": "Théorie Avancée",
                        "courses": list(available_courses.filter(title__icontains="theorie").values_list('id', flat=True)[:2]),
                        "order": 1,
                        "prerequisites": [],
                        "duration_weeks": 4
                    },
                    {
                        "id": "module_recherche",
                        "name": "Recherche Démographique",
                        "courses": list(available_courses.filter(title__icontains="recherche").values_list('id', flat=True)[:2]),
                        "order": 2,
                        "prerequisites": ["module_theorie"],
                        "duration_weeks": 5
                    },
                    {
                        "id": "module_analyse",
                        "name": "Analyse et Statistiques",
                        "courses": list(available_courses.exclude(
                            title__icontains="theorie"
                        ).exclude(
                            title__icontains="recherche"
                        ).values_list('id', flat=True)[:1]),
                        "order": 3,
                        "prerequisites": ["module_theorie", "module_recherche"],
                        "duration_weeks": 5
                    }
                ],
                "total_duration_weeks": 14,
                "certification_required": True,
                "assessment_type": "research"
            }
            
            template.save()
            return template
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Erreur création template Universitaire: {e}"))
            return None

    def create_ong_agent_template(self):
        """Template pour les agents ONG"""
        try:
            # Créer des catégories ONG
            project_category, created = Category.objects.get_or_create(
                name="Projets ONG",
                defaults={
                    "slug": "projets-ong",
                    "description": "Gestion de projets dans les ONG"
                }
            )
            
            field_category, created = Category.objects.get_or_create(
                name="Intervention Terrain",
                defaults={
                    "slug": "intervention-terrain",
                    "description": "Travail sur le terrain pour les ONG"
                }
            )
            
            available_courses = Course.objects.filter(
                Q(title__icontains="ong") |
                Q(title__icontains="projet") |
                Q(title__icontains="terrain")
            )
            
            template = LearningPathTemplate.objects.create(
                name="Agent ONG",
                structure="ong",
                level="intermediate",
                description="Parcours adapté pour les agents d'ONG. Gestion de projets, intervention sur le terrain, et collaboration avec les autorités locales.",
                estimated_duration=timedelta(weeks=10)
            )
            
            if available_courses.exists():
                template.courses.set(available_courses[:4])
            
            template.categories.set([project_category, field_category])
            
            template.sequence = {
                "modules": [
                    {
                        "id": "module_projets",
                        "name": "Gestion de Projets",
                        "courses": list(available_courses.filter(title__icontains="projet").values_list('id', flat=True)[:2]),
                        "order": 1,
                        "prerequisites": [],
                        "duration_weeks": 4
                    },
                    {
                        "id": "module_terrain",
                        "name": "Intervention Terrain",
                        "courses": list(available_courses.filter(title__icontains="terrain").values_list('id', flat=True)[:2]),
                        "order": 2,
                        "prerequisites": ["module_projets"],
                        "duration_weeks": 4
                    },
                    {
                        "id": "module_collaboration",
                        "name": "Collaboration Locale",
                        "courses": list(available_courses.exclude(
                            title__icontains="projet"
                        ).exclude(
                            title__icontains="terrain"
                        ).values_list('id', flat=True)[:2]),
                        "order": 3,
                        "prerequisites": ["module_projets", "module_terrain"],
                        "duration_weeks": 2
                    }
                ],
                "total_duration_weeks": 10,
                "certification_required": True,
                "assessment_type": "field"
            }
            
            template.save()
            return template
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Erreur création template ONG: {e}"))
            return None

    def create_consultant_template(self):
        """Template pour les consultants en état civil"""
        try:
            # Créer des catégories consultant
            consulting_category, created = Category.objects.get_or_create(
                name="Consulting État Civil",
                defaults={
                    "slug": "consulting-etat-civil",
                    "description": "Services de conseil en état civil"
                }
            )
            
            expertise_category, created = Category.objects.get_or_create(
                name="Expertise Avancée",
                defaults={
                    "slug": "expertise-avancee",
                    "description": "Compétences spécialisées en état civil"
                }
            )
            
            available_courses = Course.objects.filter(
                Q(title__icontains="consult") |
                Q(title__icontains="expert") |
                Q(title__icontains="special")
            )
            
            template = LearningPathTemplate.objects.create(
                name="Consultant État Civil",
                structure="consultant",
                level="advanced",
                description="Parcours pour consultants indépendants. Expertise avancée, services de conseil, et gestion de clientèle privée et institutionnelle.",
                estimated_duration=timedelta(weeks=12)
            )
            
            if available_courses.exists():
                template.courses.set(available_courses[:5])
            
            template.categories.set([consulting_category, expertise_category])
            
            template.sequence = {
                "modules": [
                    {
                        "id": "module_expertise",
                        "name": "Expertise Avancée",
                        "courses": list(available_courses.filter(title__icontains="expert").values_list('id', flat=True)[:2]),
                        "order": 1,
                        "prerequisites": [],
                        "duration_weeks": 4
                    },
                    {
                        "id": "module_consulting",
                        "name": "Services Conseil",
                        "courses": list(available_courses.filter(title__icontains="consult").values_list('id', flat=True)[:2]),
                        "order": 2,
                        "prerequisites": ["module_expertise"],
                        "duration_weeks": 4
                    },
                    {
                        "id": "module_specialisation",
                        "name": "Spécialisation",
                        "courses": list(available_courses.exclude(
                            title__icontains="expert"
                        ).exclude(
                            title__icontains="consult"
                        ).values_list('id', flat=True)[:1]),
                        "order": 3,
                        "prerequisites": ["module_expertise", "module_consulting"],
                        "duration_weeks": 4
                    }
                ],
                "total_duration_weeks": 12,
                "certification_required": True,
                "assessment_type": "consulting"
            }
            
            template.save()
            return template
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Erreur création template Consultant: {e}"))
            return None

    def create_multi_structure_template(self):
        """Template polyvalent multi-structures"""
        try:
            # Récupérer toutes les catégories pertinentes
            all_categories = Category.objects.all()
            
            # Récupérer une variété de cours
            available_courses = Course.objects.all()[:8]  # Limiter à 8 cours pour commencer
            
            template = LearningPathTemplate.objects.create(
                name="Agent Polyvalent Multi-structures",
                structure="multi_structure",
                level="intermediate",
                description="Parcours complet pour agents polyvalents travaillant avec plusieurs structures. Compétences transversales en état civil, communication inter-administrative et gestion multi-structures.",
                estimated_duration=timedelta(weeks=18)
            )
            
            if available_courses.exists():
                template.courses.set(available_courses)
            
            # Ajouter plusieurs catégories pour la polyvalence
            if all_categories.exists():
                template.categories.set(all_categories[:4])
            
            template.sequence = {
                "modules": [
                    {
                        "id": "module_fondamentaux",
                        "name": "Fondamentaux Multi-structures",
                        "courses": list(available_courses.values_list('id', flat=True)[:2]),
                        "order": 1,
                        "prerequisites": [],
                        "duration_weeks": 4
                    },
                    {
                        "id": "module_specialisation",
                        "name": "Spécialisation par Structure",
                        "courses": list(available_courses.values_list('id', flat=True)[2:4]),
                        "order": 2,
                        "prerequisites": ["module_fondamentaux"],
                        "duration_weeks": 5
                    },
                    {
                        "id": "module_coordination",
                        "name": "Coordination Inter-structures",
                        "courses": list(available_courses.values_list('id', flat=True)[4:6]),
                        "order": 3,
                        "prerequisites": ["module_fondamentaux", "module_specialisation"],
                        "duration_weeks": 5
                    },
                    {
                        "id": "module_expertise",
                        "name": "Expertise Avancée",
                        "courses": list(available_courses.values_list('id', flat=True)[6:8]),
                        "order": 4,
                        "prerequisites": ["module_fondamentaux", "module_specialisation", "module_coordination"],
                        "duration_weeks": 4
                    }
                ],
                "total_duration_weeks": 18,
                "certification_required": True,
                "assessment_type": "comprehensive"
            }
            
            template.save()
            return template
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Erreur création template Multi-structures: {e}"))
            return None
