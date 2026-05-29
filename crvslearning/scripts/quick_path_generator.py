import json
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crvslearning.settings')
django.setup()

from courses.models import LearningPathTemplate, Course

def generate_path_config(level, target_weeks, structure="commune"):
    """Génère une configuration de parcours rapide"""
    
    configs = {
        "débutant": {
            "modules_count": 3,
            "avg_duration": 2,
            "skills_per_module": 3,
            "certification": False,
            "assessment": "quiz"
        },
        "intermédiaire": {
            "modules_count": 4,
            "avg_duration": 2,
            "skills_per_module": 4,
            "certification": True,
            "assessment": "mixed"
        },
        "avancé": {
            "modules_count": 4,
            "avg_duration": 2.5,
            "skills_per_module": 5,
            "certification": True,
            "assessment": "practical_exam"
        }
    }
    
    config = configs.get(level, configs["débutant"])
    
    # Générer les modules
    modules = []
    for i in range(config["modules_count"]):
        module = {
            "id": f"module_{level}_{i+1}",
            "name": f"Module {level.title()} {i+1}",
            "category": f"CATÉGORIE {i+1}",
            "courses": [],
            "order": i+1,
            "prerequisites": [f"module_{level}_{i}"] if i > 0 else [],
            "duration_weeks": config["avg_duration"],
            "skills": [f"skill_{j}" for j in range(config["skills_per_module"])]
        }
        modules.append(module)
    
    return {
        "name": f"Parcours {level.title()} Généré",
        "structure": structure,
        "level": level,
        "modules": modules,
        "total_duration_weeks": target_weeks,
        "certification_required": config["certification"],
        "assessment_type": config["assessment"],
        "learning_outcomes": [
            f"Objectif {level} {i+1}" for i in range(config["modules_count"])
        ]
    }

def create_path_from_config(config):
    """Crée un parcours à partir d'une configuration"""
    
    # Vérifier si le template existe déjà
    if LearningPathTemplate.objects.filter(name=config["name"]).exists():
        print(f"⚠️  Le template '{config['name']}' existe déjà")
        return None
    
    # Créer le template
    template = LearningPathTemplate.objects.create(
        name=config["name"],
        description=f"Formation {config['level']} générée automatiquement",
        structure=config["structure"],
        level=config["level"],
        sequence=config,
        total_duration_weeks=config["total_duration_weeks"],
        certification_required=config["certification_required"],
        assessment_type=config["assessment_type"],
        learning_outcomes=config["learning_outcomes"],
        is_active=True
    )
    
    print(f"✅ Template '{config['name']}' créé avec succès")
    print(f"   📊 {len(config.get('modules', []))} modules")
    print(f"   ⏱️ {config['total_duration_weeks']} semaines")
    print(f"   🎯 Niveau: {config['level']}")
    
    return template

# Exemple d'utilisation
if __name__ == "__main__":
    print("🚀 Génération de configurations de parcours...")
    
    # Générer les 3 niveaux
    for level in ["débutant", "intermédiaire", "avancé"]:
        config = generate_path_config(level, 7)
        
        # Créer le parcours
        create_path_from_config(config)
        
        # Sauvegarder en JSON
        filename = f"path_{level}_config.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Configuration sauvegardée: {filename}")
        print("-" * 40)
    
    print("\n🎉 Toutes les configurations ont été générées !")
