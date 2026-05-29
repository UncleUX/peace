# Guide d'utilisation de django-nested-admin

## Configuration terminée ✅

django-nested-admin est maintenant configuré dans votre projet CRVS Learning.

### Ce qui a été fait :

1. **Ajout de 'nested_admin' dans INSTALLED_APPS** (settings.py)
2. **Mise à jour de courses/admin.py** avec les classes nested :
   - `CourseAdmin` utilise `NestedModelAdmin` avec `ModuleInline`
   - `ModuleAdmin` utilise `NestedModelAdmin` avec `LessonInline`  
   - `LessonAdmin` utilise `NestedModelAdmin` avec `LessonVideoInline` et `CommentInline`
   - Création des classes inline imbriquées

### Structure hiérarchique implémentée :

```
Course (NestedModelAdmin)
└── ModuleInline (NestedStackedInline)
    └── LessonInline (NestedStackedInline)
        ├── LessonVideoInline (NestedTabularInline)
        └── CommentInline (NestedTabularInline)
```

### Comment utiliser :

1. **Allez dans l'admin Django** : `/admin/`
2. **Cliquez sur "Courses"** dans le menu
3. **Ajoutez ou modifiez un cours**
4. **Vous verrez maintenant des sections imbriquées** pour :
   - Ajouter des modules directement dans le formulaire du cours
   - Ajouter des leçons directement dans chaque module
   - Ajouter des vidéos et commentaires directement dans chaque leçon

### Avantages :

- **Interface intuitive** : Tout est géré dans un seul formulaire
- **Gain de temps** : Pas besoin de naviguer entre plusieurs pages
- **Drag & drop** : Réorganisez facilement l'ordre des éléments
- **AJAX** : Ajout/suppression dynamique sans recharger la page

### Personnalisation possible :

Vous pouvez ajuster les champs affichés dans chaque inline en modifiant les `fields` dans les classes correspondantes.

Exemple pour ajouter plus de champs à LessonInline :
```python
class LessonInline(NestedStackedInline):
    model = Lesson
    extra = 1
    fields = ('title', 'description', 'content_file', 'order', 'is_active', 
              'thumbnail', 'duration', 'subtitle_file', 'is_processing')
    inlines = [LessonVideoInline, CommentInline]
```
