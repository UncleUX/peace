# Scripts de Gestion des Parcours d'Apprentissage

## 📁 Structure des scripts

```
crvslearning/
├── scripts/
│   ├── README.md                    # Ce fichier
│   ├── create_all_learning_paths.py    # Création de tous les niveaux
│   ├── quick_path_generator.py         # Générateur rapide
│   └── __init__.py
├── courses/
│   └── management/
│       └── commands/
│           ├── README.md               # Documentation des commands
│           ├── generate_path.py         # Création manuelle
│           ├── create_advanced_templates.py  # Création avancée
│           ├── generate_sequence_from_courses.py  # Génération depuis cours
│           ├── validate_and_generate_sequence.py  # Validation + génération
│           └── __init__.py
└── data/
    ├── learning_path_template.json    # Template de référence
    └── __init__.py
```

## 🚀 Scripts disponibles

### 1. `create_all_learning_paths.py`
**Usage** : Créer tous les parcours (débutant, intermédiaire, avancé)

```bash
cd crvslearning
python scripts/create_all_learning_paths.py
```

**Fonctionnalités** :
- ✅ Crée 3 niveaux de parcours complets
- ✅ Modules détaillés avec objectifs et compétences
- ✅ Validation automatique des structures
- ✅ Création de parcours spécialisés

---

### 2. `quick_path_generator.py`
**Usage** : Générateur rapide de configurations

```bash
cd crvslearning
python scripts/quick_path_generator.py
```

**Fonctionnalités** :
- ✅ Génère configurations pour tous les niveaux
- ✅ Crée des fichiers JSON de sortie
- ✅ Personnalisation des paramètres
- ✅ Création automatique des parcours

---

### 3. Management Commands

#### 3.1 `generate_path.py`
**Usage** : Création manuelle de parcours

```bash
python manage.py generate_path --name "Mon Parcours" --level "intermédiaire"
```

#### 3.2 `create_advanced_templates.py`
**Usage** : Création avancée de tous les niveaux

```bash
python manage.py create_advanced_templates --level "avancé"
```

#### 3.3 `generate_sequence_from_courses.py`
**Usage** : Génération depuis des cours existants

```bash
python manage.py generate_sequence_from_courses --course-ids "16,10,11,12"
```

#### 3.4 `validate_and_generate_sequence.py`
**Usage** : Validation complète et génération automatique

```bash
python manage.py validate_and_generate_sequence --course-ids "16,10,11,12" --interactive
```

---

## 📋 Guide d'utilisation

### Étape 1 : Choisir la bonne approche

| Besoin | Script recommandé | Commande |
|---------|------------------|----------|
| Créer rapidement tous les niveaux | `create_all_learning_paths.py` | Direct |
| Générateur de configurations | `quick_path_generator.py` | Direct |
| Création manuelle avec contrôle | `generate_path.py` | Django |
| Depuis des cours existants | `generate_sequence_from_courses.py` | Django |
| Validation + génération automatique | `validate_and_generate_sequence.py` | Django |

### Étape 2 : Préparer les données

#### Lister les cours disponibles :
```bash
python manage.py shell -c "
from courses.models import Course
for c in Course.objects.all():
    print(f'ID: {c.id} - {c.title}')
"
```

#### Noter les IDs pour la génération :
```bash
# Exemple d'IDs à utiliser
16,10,11,12,14,15
```

### Étape 3 : Exécuter le script

#### Mode simple :
```bash
python scripts/create_all_learning_paths.py
```

#### Mode avec paramètres :
```bash
python manage.py validate_and_generate_sequence \
  --course-ids "16,10,11,12" \
  --name "Parcours Personnalisé" \
  --structure "commune"
```

#### Mode simulation :
```bash
python manage.py validate_and_generate_sequence \
  --course-ids "16,10,11,12" \
  --dry-run
```

---

## 🎯 Formats de séquence

### Format complet (recommandé)
```json
{
  "modules": [
    {
      "id": "module_unique_id",
      "name": "Nom affiché",
      "category": "Catégorie thématique",
      "courses": [1, 2, 3],
      "order": 1,
      "prerequisites": [],
      "duration_weeks": 2,
      "skills": ["compétence1", "compétence2"],
      "description": "Description du module",
      "objectives": ["Objectif 1", "Objectif 2"]
    }
  ],
  "total_duration_weeks": 8,
  "certification_required": true,
  "assessment_type": "mixed",
  "learning_outcomes": ["Objectif global 1", "Objectif global 2"]
}
```

### Format simplifié
```json
{
  "course_order": [1, 2, 3, 4],
  "total_weeks": 6,
  "certification": false
}
```

### Format minimaliste
```json
{
  "modules": [
    {"id": "mod_1", "order": 1, "courses": [16]},
    {"id": "mod_2", "order": 2, "courses": [10]}
  ]
}
```

---

## 🔧 Personnalisation

### Modifier les catégories

Dans `validate_and_generate_sequence.py`, modifier la fonction `classify_course()` :

```python
def classify_course(self, course):
    title = course.title.lower()
    
    # Ajouter vos propres règles
    if 'votre_mot_clé' in title:
        return 'Votre Catégorie Personnalisée'
    
    # ... autres règles
```

### Ajuster les compétences

```python
def generate_skills_for_category(self, category, course):
    skills_map = {
        'Votre Catégorie': ['compétence1', 'compétence2'],
        # ... autres catégories
    }
    
    return skills_map.get(category, ['default_skills'])
```

### Personnaliser les durées

```python
def calculate_duration(self, difficulty, order):
    # Modifier la logique de durée
    if difficulty == 'avancé':
        return 2.0  # Plus de temps pour les experts
    return 1.5  # Durée par défaut
```

---

## 📊 Exemples d'utilisation

### Exemple 1 : Création rapide
```bash
# Créer tous les parcours de base
cd crvslearning
python scripts/create_all_learning_paths.py

# Résultat attendu
✅ Template 'Parcours Débutant' créé
✅ Template 'Parcours Intermédiaire' créé  
✅ Template 'Parcours Avancé' créé
```

### Exemple 2 : Génération depuis cours
```bash
# Générer une séquence depuis 4 cours spécifiques
python manage.py generate_sequence_from_courses \
  --course-ids "16,10,11,12" \
  --name "Parcours Personnalisé" \
  --weeks-per-course 2.0

# Résultat attendu
📋 SÉQUENCE GÉNÉRÉE:
  1. Module 1 - CADRE REGLEMENTAIRE
     Cours: CADRE REGLEMENTAIRE
     Durée: 2.0 semaines
  2. Module 2 - DECLARATIONS
     Cours: DECLARACTION DES FAITS
     Durée: 2.0 semaines
# ... etc
```

### Exemple 3 : Validation complète
```bash
# Validation avec génération automatique
python manage.py validate_and_generate_sequence \
  --course-ids "16,10,11,12,14,15" \
  --name "Parcours Complet Validé" \
  --output "parcours_valide.json"

# Résultat attendu
📋 ÉTAPE 1: VALIDATION DES COURS
✅ Tous les cours sont valides
   📚 6 cours trouvés

📊 ÉTAPE 2: ANALYSE DES COURS
   📂 Catégories: 4 identifiées
   🎯 Niveaux: 3 niveaux
   📋 Ordre recommandé: 6 cours

✅ ÉTAPE 4: VALIDATION DE SÉQUENCE
✅ Séquence VALIDIDE
   • Structure cohérente
   • Prérequis valides

✅ Template sauvegardé
💾 Séquence sauvegardée dans: parcours_valide.json
```

---

## 🐛 Dépannage

### Erreurs communes

#### IDs de cours invalides
```
❌ Format d'IDs invalide. Utilisez: --course-ids "1,2,3"
```
**Solution** : Vérifier le format des IDs

#### Template existe déjà
```
⚠️ Le template 'Nom' existe déjà
```
**Solution** : Utiliser un nom différent

#### JSON invalide
```
❌ Erreur de validation JSON
```
**Solution** : Vérifier la syntaxe JSON

### Commandes utiles

#### Lister les cours
```bash
python manage.py shell -c "
from courses.models import Course
print('Cours disponibles:')
for c in Course.objects.filter(is_published=True):
    print(f'  ID {c.id}: {c.title}')
"
```

#### Vérifier les templates
```bash
python manage.py shell -c "
from courses.models import LearningPathTemplate
print('Templates existants:')
for t in LearningPathTemplate.objects.all():
    print(f'  - {t.name} ({t.level})')
"
```

#### Supprimer un template
```bash
python manage.py shell -c "
from courses.models import LearningPathTemplate
LearningPathTemplate.objects.filter(name='Ancien Template').delete()
print('Template supprimé')
"
```

---

## 📈 Bonnes pratiques

### 1. Toujours tester en mode simulation
```bash
python manage.py validate_and_generate_sequence --dry-run --course-ids "16,10"
```

### 2. Utiliser des noms explicites
```bash
--name "Parcours Débutant - Commune 2024"
```

### 3. Documenter les créations
```bash
# Historique à conserver
python manage.py generate_path --level "débutant"  # 2024-01-15
python manage.py generate_sequence_from_courses --course-ids "16,10,11"  # 2024-01-16
```

### 4. Sauvegarder les configurations
```bash
# Générer et sauvegarder
python scripts/quick_path_generator.py
# Fichiers JSON créés :
#   - path_debutant_config.json
#   - path_intermediaire_config.json
#   - path_avance_config.json
```

---

## 🚀 Évolution du système

### Prochaines améliorations possibles

1. **Interface web** pour créer des parcours visuellement
2. **API REST** pour la gestion programmatique
3. **Templates prédéfinis** par type de structure
4. **Système de versioning** des parcours
5. **Export/Import** pour partager les parcours

---

## 📞 Support

### Pour obtenir de l'aide

1. **Consulter les README** des scripts spécifiques
2. **Utiliser le mode `--help`** des commands
3. **Tester avec `--dry-run`** avant d'appliquer
4. **Vérifier dans l'admin** après création

### Documentation complémentaire

- **Django Admin** : `/admin/courses/learningpathtemplate/`
- **API des parcours** : (à implémenter)
- **Base de données** : Modèles `LearningPathTemplate`, `Course`

---

## 🎯 Résumé

Ce système de scripts vous offre :

✅ **Flexibilité totale** dans la création de parcours  
✅ **Validation automatique** des structures  
✅ **Génération intelligente** des séquences  
✅ **Modes multiples** (direct, simulation, interactif)  
✅ **Documentation complète** pour chaque outil  

**Vous avez maintenant une solution complète et professionnelle pour la gestion des parcours d'apprentissage !** 🚀📚
