# Management Commands - Parcours d'Apprentissage

## 📋 Liste des commandes disponibles

### 1. `generate_path`
**Génère un parcours d'apprentissage structuré**

```bash
python manage.py generate_path [options]
```

**Options :**
- `--name` : Nom du parcours (défaut: "Parcours Agent État Civil")
- `--structure` : Structure cible (défaut: "commune")  
- `--level` : Niveau (débutant, intermédiaire, avancé)
- `--json-file` : Fichier JSON avec la structure

**Exemples :**
```bash
# Créer un parcours intermédiaire
python manage.py generate_path --level "intermédiaire" --structure "commune"

# Charger depuis un fichier JSON
python manage.py generate_path --json-file data/learning_path_template.json

# Créer un parcours personnalisé
python manage.py generate_path --name "Mon Parcours" --level "avancé"
```

---

### 2. `create_advanced_templates`
**Crée des templates de parcours avancés pour tous les niveaux**

```bash
python manage.py create_advanced_templates [options]
```

**Options :**
- `--level` : Niveau spécifique (débutant, intermédiaire, avancé)
- `--structure` : Structure cible (défaut: "commune")
- `--dry-run` : Simulation sans sauvegarder

**Exemples :**
```bash
# Créer tous les niveaux
python manage.py create_advanced_templates

# Créer un seul niveau
python manage.py create_advanced_templates --level "intermédiaire"

# Simulation seulement
python manage.py create_advanced_templates --dry-run

# Pour une autre structure
python manage.py create_advanced_templates --structure "région"
```

---

### 3. `generate_sequence_from_courses`
**Génère automatiquement une séquence à partir des cours sélectionnés**

```bash
python manage.py generate_sequence_from_courses [options]
```

**Options requises :**
- `--name` : Nom du parcours
- `--course-ids` : IDs des cours séparés par des virgules

**Options optionnelles :**
- `--structure` : Structure cible (défaut: "commune")
- `--level` : Niveau (défaut: "débutant")
- `--weeks-per-course` : Semaines par cours (défaut: 1.5)
- `--dry-run` : Simulation sans sauvegarder

**Exemples :**
```bash
# Générer avec 4 cours spécifiques
python manage.py generate_sequence_from_courses \
  --name "Parcours Personnalisé" \
  --course-ids "16,10,11,12" \
  --weeks-per-course 2.0

# Avec tous les cours disponibles
python manage.py generate_sequence_from_courses \
  --name "Parcours Complet" \
  --course-ids "1,2,3,4,5,6,7"

# Simulation pour tester
python manage.py generate_sequence_from_courses \
  --name "Test Parcours" \
  --course-ids "16,10,11" \
  --dry-run
```

---

## 🎯 Guide d'utilisation

### Étape 1 : Choisir la bonne commande

| Besoin | Commande recommandée |
|---------|-------------------|
| Créer un parcours simple | `generate_path` |
| Créer tous les niveaux | `create_advanced_templates` |
| Générer depuis des cours existants | `generate_sequence_from_courses` |

### Étape 2 : Préparer les données

#### Pour `generate_sequence_from_courses` :
1. Lister les cours disponibles :
   ```bash
   python manage.py shell -c "from courses.models import Course; print([(c.id, c.title) for c in Course.objects.all()])"
   ```

2. Noter les IDs des cours souhaités

3. Utiliser la commande avec les IDs

### Étape 3 : Vérifier les résultats

Après exécution :
1. **Vérifier dans l'admin** : `/admin/courses/learningpathtemplate/`
2. **Contrôler la séquence** générée
3. **Ajuster si nécessaire** directement dans l'admin

---

## 📊 Structure des séquences générées

### Format JSON complet
```json
{
  "modules": [
    {
      "id": "module_unique_id",
      "name": "Nom affiché du module",
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

### Format simple (ordre uniquement)
```json
{
  "course_order": [1, 2, 3, 4]
}
```

---

## 🔧 Personnalisation

### Modifier les catégories et compétences

Dans `generate_sequence_from_courses.py`, modifier la fonction `get_category_and_skills()` :

```python
def get_category_and_skills(self, course):
    title_lower = course.title.lower()
    
    if 'votre_mot_clé' in title_lower:
        return 'VOTRE_CATÉGORIE', ['compétence1', 'compétence2']
    
    # Ajouter d'autres conditions...
```

### Ajuster les durées par défaut

```python
# Dans les commandes, modifier la logique de durée
weeks_per_course = 2.0  # Au lieu de 1.5
```

---

## 🚀 Bonnes pratiques

### 1. Toujours tester en mode simulation
```bash
python manage.py generate_sequence_from_courses --dry-run --course-ids "16,10"
```

### 2. Utiliser des noms explicites
```bash
--name "Parcours Débutant - Commune 2024"
```

### 3. Documenter les parcours créés
Notez les commandes utilisées pour pouvoir les reproduire :

```bash
# Historique des parcours créés
python manage.py generate_path --level "débutant" --structure "commune"  # 2024-01-15
python manage.py generate_sequence_from_courses --course-ids "16,10,11,12"  # 2024-01-16
```

---

## 🐛 Dépannage

### Erreurs communes

**IDs de cours invalides :**
```
❌ IDs de cours invalides. Utilisez: --course-ids "1,2,3"
```
**Solution** : Vérifier les IDs des cours existants

**Template existe déjà :**
```
⚠️ Le template 'Nom' existe déjà
```
**Solution** : Utiliser un nom différent ou supprimer l'ancien

**JSON invalide :**
```
❌ Erreur de validation JSON
```
**Solution** : Vérifier la syntaxe JSON (virgules, guillemets)

### Commandes utiles

```bash
# Lister tous les cours avec leurs IDs
python manage.py shell -c "
from courses.models import Course
for c in Course.objects.all():
    print(f'ID: {c.id} - {c.title}')
"

# Vérifier les templates existants
python manage.py shell -c "
from courses.models import LearningPathTemplate
for t in LearningPathTemplate.objects.all():
    print(f'{t.name} - {t.level} - {t.structure}')
"

# Supprimer un template (attention!)
python manage.py shell -c "
from courses.models import LearningPathTemplate
LearningPathTemplate.objects.filter(name='Nom à supprimer').delete()
print('Template supprimé')
"
```

---

## 📞 Support

Pour toute question sur l'utilisation des commandes :

1. **Vérifier la documentation** ci-dessus
2. **Utiliser le mode `--dry-run`** pour tester
3. **Consulter les logs** dans la console
4. **Vérifier dans l'admin Django** après création

Les commandes sont conçues pour être **simples, flexibles et réutilisables** ! 🎯
