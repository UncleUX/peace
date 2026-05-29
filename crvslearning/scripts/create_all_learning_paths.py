import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crvslearning.settings')
django.setup()

from courses.models import LearningPathTemplate, Course

def create_beginner_path():
    """Crée le parcours débutant"""
    
    sequence_data = {
        "modules": [
            {
                "id": "module_fondamentaux",
                "name": "Module Fondamentaux",
                "category": "INTRODUCTION A L'ETAT CIVIL",
                "courses": [16],  # CADRE REGLEMENTAIRE
                "order": 1,
                "prerequisites": [],
                "duration_weeks": 2,
                "skills": ["base_concepts", "understanding", "legal_framework"],
                "description": "Découverte des bases de l'état civil"
            },
            {
                "id": "module_declarations_base",
                "name": "Module Déclarations Base",
                "category": "ENREGISTREMENT DES FAITS D'ETAT CIVIL",
                "courses": [10],  # DECLARATION DES FAITS
                "order": 2,
                "prerequisites": ["module_fondamentaux"],
                "duration_weeks": 3,
                "skills": ["birth_registration", "death_registration", "basic_form_filling"],
                "description": "Apprentissage des déclarations essentielles"
            },
            {
                "id": "module_actes_simples",
                "name": "Module Actes Simples",
                "category": "ETABLISSEMENT DES ACTES",
                "courses": [12],  # ETABLISSEMENT DES ACTES
                "order": 3,
                "prerequisites": ["module_declarations_base"],
                "duration_weeks": 2,
                "skills": ["simple_certificates", "document_processing"],
                "description": "Gestion des actes courants"
            }
        ],
        "total_duration_weeks": 7,
        "certification_required": False,
        "assessment_type": "quiz",
        "learning_outcomes": [
            "Comprendre les fondamentaux de l'état civil",
            "Maîtriser les déclarations de base",
            "Savoir rédiger les actes simples",
            "Connaître les procédures essentielles"
        ],
        "difficulty_level": "débutant",
        "target_audience": "Nouveaux agents, personnel en formation"
    }
    
    return create_template("Parcours Débutant - Agent État Civil", sequence_data, "commune", "débutant")

def create_intermediate_path():
    """Crée le parcours intermédiaire"""
    
    sequence_data = {
        "modules": [
            {
                "id": "module_actes_complexes",
                "name": "Module Actes Complexes",
                "category": "ETABLISSEMENT DES ACTES AVANCÉS",
                "courses": [12, 13],  # ETABLISSEMENT + compléments
                "order": 1,
                "prerequisites": [],
                "duration_weeks": 3,
                "skills": ["complex_certificates", "legal_documents", "advanced_form_filling"],
                "description": "Gestion des actes complexes et spéciaux"
            },
            {
                "id": "module_registres",
                "name": "Module Tenue des Registres",
                "category": "GESTION DES REGISTRES",
                "courses": [11],  # TENUE DES REGISTRES
                "order": 2,
                "prerequisites": ["module_actes_complexes"],
                "duration_weeks": 2,
                "skills": ["register_management", "archiving", "record_keeping"],
                "description": "Gestion optimale des registres"
            },
            {
                "id": "module_juridique",
                "name": "Module Aspects Juridiques",
                "category": "CADRE JURIDIQUE",
                "courses": [],
                "order": 3,
                "prerequisites": ["module_actes_complexes"],
                "duration_weeks": 2,
                "skills": ["legal_aspects", "civil_code", "jurisprudence"],
                "description": "Approfondissement juridique"
            }
        ],
        "total_duration_weeks": 7,
        "certification_required": True,
        "assessment_type": "mixed",
        "learning_outcomes": [
            "Maîtriser les actes complexes",
            "Gérer efficacement les registres",
            "Comprendre les aspects juridiques",
            "Traiter les cas particuliers"
        ],
        "difficulty_level": "intermédiaire",
        "target_audience": "Agents expérimentés, responsables de service"
    }
    
    return create_template("Parcours Intermédiaire - Agent Confirmé", sequence_data, "commune", "intermédiaire")

def create_advanced_path():
    """Crée le parcours avancé"""
    
    sequence_data = {
        "modules": [
            {
                "id": "module_archivage",
                "name": "Module Archivage Digital",
                "category": "DIGITALISATION ET ARCHIVAGE",
                "courses": [14],  # ARCHIVAGE DES DOCUMENTS
                "order": 1,
                "prerequisites": [],
                "duration_weeks": 2,
                "skills": ["digital_archiving", "document_management", "electronic_records"],
                "description": "Transition vers le numérique"
            },
            {
                "id": "module_statistiques",
                "name": "Module Statistiques",
                "category": "PRODUCTION STATISTIQUE",
                "courses": [15],  # PRODUCTION ET DIFFUSION
                "order": 2,
                "prerequisites": ["module_archivage"],
                "duration_weeks": 2,
                "skills": ["statistical_analysis", "data_reporting", "performance_indicators"],
                "description": "Production et analyse des statistiques"
            },
            {
                "id": "module_management",
                "name": "Module Management",
                "category": "MANAGEMENT ET SUPERVISION",
                "courses": [],
                "order": 3,
                "prerequisites": ["module_statistiques"],
                "duration_weeks": 3,
                "skills": ["team_management", "quality_control", "process_optimization"],
                "description": "Gestion d'équipe et optimisation"
            },
            {
                "id": "module_expertise",
                "name": "Module Expertise Juridique",
                "category": "EXPERTISE ET CONSEIL",
                "courses": [],
                "order": 4,
                "prerequisites": ["module_management"],
                "duration_weeks": 2,
                "skills": ["legal_expertise", "advisory_role", "complex_case_handling"],
                "description": "Rôle d'expert et conseil"
            }
        ],
        "total_duration_weeks": 9,
        "certification_required": True,
        "assessment_type": "practical_exam",
        "learning_outcomes": [
            "Maîtriser l'archivage digital",
            "Produire des statistiques pertinentes",
            "Gérer une équipe efficacement",
            "Assurer un rôle d'expertise"
        ],
        "difficulty_level": "avancé",
        "target_audience": "Chefs de service, experts, formateurs"
    }
    
    return create_template("Parcours Avancé - Expert État Civil", sequence_data, "commune", "avancé")

def create_specialized_paths():
    """Crée des parcours spécialisés"""
    
    specialized_paths = []
    
    # Parcours pour les régions
    region_sequence = {
        "modules": [
            {
                "id": "module_region_fondamentaux",
                "name": "Module Spécifique Région",
                "category": "COMPÉTENCES RÉGIONALES",
                "courses": [],
                "order": 1,
                "prerequisites": [],
                "duration_weeks": 2,
                "skills": ["regional_regulations", "specific_procedures"],
                "description": "Spécificités régionales"
            },
            {
                "id": "module_coordination",
                "name": "Module Coordination",
                "category": "COORDINATION INTER-SERVICES",
                "courses": [],
                "order": 2,
                "prerequisites": ["module_region_fondamentaux"],
                "duration_weeks": 1,
                "skills": ["inter_service_coordination", "regional_collaboration"],
                "description": "Coordination au niveau régional"
            }
        ],
        "total_duration_weeks": 3,
        "certification_required": True,
        "assessment_type": "case_study",
        "learning_outcomes": [
            "Maîtriser les spécificités régionales",
            "Coordonner efficacement les services"
        ],
        "difficulty_level": "spécialisé",
        "target_audience": "Agents régionaux, coordinateurs"
    }
    
    specialized_paths.append(
        create_template("Parcours Spécialisé - Agent Régional", region_sequence, "région", "spécialisé")
    )
    
    return specialized_paths

def create_template(name, sequence_data, structure, level):
    """Crée un template avec validation"""
    
    # Vérifier si le template existe déjà
    if LearningPathTemplate.objects.filter(name=name).exists():
        print(f"⚠️  Le template '{name}' existe déjà")
        return None
    
    # Créer le template
    template = LearningPathTemplate.objects.create(
        name=name,
        description=f"Formation {level} pour les agents de l'état civil ({structure})",
        structure=structure,
        level=level,
        sequence=sequence_data,
        total_duration_weeks=sequence_data["total_duration_weeks"],
        certification_required=sequence_data["certification_required"],
        assessment_type=sequence_data["assessment_type"],
        learning_outcomes=sequence_data["learning_outcomes"],
        is_active=True
    )
    
    # Ajouter les cours automatiquement
    all_course_ids = []
    for module in sequence_data.get("modules", []):
        all_course_ids.extend(module.get("courses", []))
    
    if all_course_ids:
        courses = Course.objects.filter(id__in=all_course_ids, is_published=True)
        template.courses.set(courses)
        print(f"📚 {courses.count()} cours associés")
    
    print(f"✅ Template '{name}' créé avec succès")
    print(f"   📊 {len(sequence_data.get('modules', []))} modules")
    print(f"   ⏱️ {sequence_data['total_duration_weeks']} semaines")
    print(f"   🎯 Niveau: {level}")
    
    return template

def create_all_paths():
    """Crée tous les parcours d'apprentissage"""
    
    print("🚀 Création des parcours d'apprentissage...")
    print("=" * 50)
    
    # Créer les parcours principaux
    paths_created = []
    
    beginner_path = create_beginner_path()
    if beginner_path:
        paths_created.append(beginner_path)
    
    print("\n" + "-" * 30)
    
    intermediate_path = create_intermediate_path()
    if intermediate_path:
        paths_created.append(intermediate_path)
    
    print("\n" + "-" * 30)
    
    advanced_path = create_advanced_path()
    if advanced_path:
        paths_created.append(advanced_path)
    
    print("\n" + "-" * 30)
    
    # Créer les parcours spécialisés
    specialized_paths = create_specialized_paths()
    paths_created.extend(specialized_paths)
    
    # Résumé
    print("\n" + "=" * 50)
    print("📋 RÉCAPITULATIF DE CRÉATION")
    print("=" * 50)
    print(f"✅ Total templates créés: {len(paths_created)}")
    
    for path in paths_created:
        print(f"   📚 {path.name}")
        print(f"      📊 {path.sequence.get('total_duration_weeks', 0)} semaines")
        print(f"      🎯 Niveau: {path.level}")
        print(f"      🏢 Structure: {path.structure}")
    
    print("\n🎉 Tous les parcours ont été créés avec succès !")
    print("💡 Vous pouvez maintenant les consulter dans l'admin Django")
    
    return paths_created

def validate_paths():
    """Valide tous les parcours créés"""
    
    print("\n🔍 VALIDATION DES PARCOURS")
    print("=" * 30)
    
    templates = LearningPathTemplate.objects.all()
    
    for template in templates:
        sequence = template.sequence
        modules = sequence.get("modules", [])
        
        print(f"\n📋 Validation: {template.name}")
        
        # Validation des ordres
        orders = [m.get("order") for m in modules]
        if len(set(orders)) != len(orders):
            print(f"   ❌ Ordres dupliqués")
        else:
            print(f"   ✅ Ordres valides")
        
        # Validation des prérequis
        module_ids = [m.get("id") for m in modules]
        all_prereqs_valid = True
        
        for module in modules:
            prereqs = module.get("prerequisites", [])
            for prereq in prereqs:
                if prereq not in module_ids:
                    print(f"   ❌ Prérequis invalide: {prereq}")
                    all_prereqs_valid = False
        
        if all_prereqs_valid:
            print(f"   ✅ Prérequis valides")
        
        # Validation des cours
        all_course_ids = []
        for module in modules:
            all_course_ids.extend(module.get("courses", []))
        
        existing_courses = Course.objects.filter(id__in=all_course_ids).count()
        if existing_courses == len(set(all_course_ids)):
            print(f"   ✅ Tous les cours existent ({existing_courses})")
        else:
            print(f"   ❌ Certains cours manquent ({existing_courses}/{len(set(all_course_ids))})")

if __name__ == "__main__":
    # Créer tous les parcours
    paths = create_all_paths()
    
    # Valider les parcours
    validate_paths()
    
    print(f"\n🎯 Opération terminée : {len(paths)} parcours créés")
