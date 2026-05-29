# 🎯 Mode Parcours avec Prérequis - Documentation Complète

## 📋 Table des Matières

1. [Vue d'ensemble](#vue-densemble)
2. [Modèle de données](#modèle-de-données)
3. [Logique métier](#logique-métier)
4. [Interface utilisateur](#interface-utilisateur)
5. [Cas d'utilisation](#cas-dutilisation)
6. [Étapes d'implémentation](#étapes-dimplémentation)
7. [Migration de base de données](#migration-de-base-de-données)
8. [Interface admin](#interface-admin)
9. [Tests et validation](#tests-et-validation)
10. [Fonctionnalités avancées](#fonctionnalités-avancées)

---

## 🎯 Vue d'ensemble

### **Objectif**
Implémenter un système de parcours d'apprentissage avec des prérequis pour structurer la progression des utilisateurs et garantir qu'ils acquièrent les compétences nécessaires avant d'accéder à des cours plus avancés.

### **Fonctionnalités principales**
- ✅ **Prérequis obligatoires** : Cours nécessaires avant d'accéder à un cours
- ✅ **Conditions flexibles** : Score minimum, pourcentage de completion
- ✅ **Parcours guidés** : Chemins d'apprentissage recommandés
- ✅ **Vérification automatique** : Déblocage/verrouillage automatique des cours
- ✅ **Interface visuelle** : Graphiques de progression et prérequis

---

## 📊 Modèle de données

### **Modèle `CoursePrerequisite`**

```python
# courses/models.py

class CoursePrerequisite(models.Model):
    """
    Modèle pour définir les prérequis entre cours.
    Un cours peut avoir plusieurs prérequis, et un cours peut être prérequis pour plusieurs autres.
    """
    course = models.ForeignKey(
        Course, 
        on_delete=models.CASCADE, 
        related_name='prerequisites',
        verbose_name="Cours cible"
    )
    prerequisite_course = models.ForeignKey(
        Course, 
        on_delete=models.CASCADE, 
        related_name='required_for',
        verbose_name="Cours prérequis"
    )
    
    # Champs supplémentaires pour plus de flexibilité
    is_mandatory = models.BooleanField(
        default=True,
        verbose_name="Prérequis obligatoire",
        help_text="Si coché, ce prérequis doit être validé pour accéder au cours"
    )
    
    minimum_score = models.IntegerField(
        null=True, 
        blank=True,
        verbose_name="Score minimum requis",
        help_text="Score minimum (sur 100) requis dans le cours prérequis"
    )
    
    completion_percentage = models.IntegerField(
        default=100,
        verbose_name="Pourcentage de completion requis",
        help_text="Pourcentage de completion du cours prérequis requis (0-100)"
    )
    
    description = models.TextField(
        blank=True,
        verbose_name="Description du prérequis",
        help_text="Explique pourquoi ce cours est nécessaire"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_prerequisites'
    )

    class Meta:
        verbose_name = "Prérequis de cours"
        verbose_name_plural = "Prérequis de cours"
        unique_together = ['course', 'prerequisite_course']
        ordering = ['course', 'created_at']
        # Empêcher un cours d'être prérequis de lui-même
        constraints = [
            models.CheckConstraint(
                check=~models.Q(course=models.F('prerequisite_course')),
                name='no_self_prerequisite'
            )
        ]

    def __str__(self):
        return f"{self.course.title} ← {self.prerequisite_course.title}"

    def clean(self):
        """Validation pour éviter les références circulaires"""
        if self.course == self.prerequisite_course:
            raise ValidationError("Un cours ne peut pas être son propre prérequis")
        
        # Vérifier les références circulaires indirectes
        if self.would_create_circular_reference():
            raise ValidationError("Cela créerait une référence circulaire dans les prérequis")

    def would_create_circular_reference(self):
        """Vérifie si l'ajout de ce prérequis créerait une référence circulaire"""
        def check_circular(current_course, target_course, visited=None):
            if visited is None:
                visited = set()
            
            if current_course == target_course:
                return True
            
            if current_course in visited:
                return False
            
            visited.add(current_course)
            
            # Vérifier tous les prérequis existants du cours actuel
            for prereq in current_course.prerequisites.all():
                if check_circular(prereq.prerequisite_course, target_course, visited):
                    return True
            
            return False
        
        return check_circular(self.prerequisite_course, self.course)

    def is_satisfied_by_user(self, user):
        """Vérifie si l'utilisateur satisfait ce prérequis"""
        # Vérifier si l'utilisateur est inscrit au cours prérequis
        enrollment = Enrollment.objects.filter(
            user=user, 
            course=self.prerequisite_course
        ).first()
        
        if not enrollment:
            return False
        
        # Vérifier le pourcentage de completion
        if self.completion_percentage > 0:
            completion = enrollment.get_completion_percentage()
            if completion < self.completion_percentage:
                return False
        
        # Vérifier le score minimum si requis
        if self.minimum_score is not None:
            score = enrollment.get_average_score()
            if score < self.minimum_score:
                return False
        
        return True
```

### **Méthodes ajoutées au modèle `Course`**

```python
# courses/models.py - Ajouter dans la classe Course

class Course(models.Model):
    # ... champs existants ...
    
    def get_prerequisites(self):
        """Retourne tous les prérequis de ce cours"""
        return self.prerequisites.select_related('prerequisite_course').all()
    
    def get_mandatory_prerequisites(self):
        """Retourne uniquement les prérequis obligatoires"""
        return self.prerequisites.filter(is_mandatory=True).select_related('prerequisite_course')
    
    def get_courses_that_require_this(self):
        """Retourne tous les cours qui nécessitent ce cours comme prérequis"""
        return self.required_for.select_related('course').all()
    
    def can_user_access(self, user):
        """Vérifie si un utilisateur peut accéder à ce cours"""
        if not user.is_authenticated:
            return False, "Vous devez être connecté"
        
        # Vérifier les prérequis obligatoires
        for prereq in self.get_mandatory_prerequisites():
            if not prereq.is_satisfied_by_user(user):
                return False, f"Prérequis non satisfait : {prereq.prerequisite_course.title}"
        
        return True, "Accès autorisé"
    
    def get_missing_prerequisites_for_user(self, user):
        """Retourne les prérequis manquants pour un utilisateur"""
        missing = []
        for prereq in self.get_mandatory_prerequisites():
            if not prereq.is_satisfied_by_user(user):
                missing.append(prereq)
        return missing
```

---

## 🧠 Logique métier

### **Vérification des prérequis**

```python
# courses/views.py

def check_course_prerequisites(user, course):
    """Vérifie si l'utilisateur a validé les prérequis"""
    prerequisites = course.prerequisites.filter(is_mandatory=True)
    
    for prereq in prerequisites:
        prereq_course = prereq.prerequisite_course
        # Vérifier si le cours prérequis est complété
        if not is_course_completed_by_user(user, prereq_course):
            return False, prereq_course
    
    return True, None

def is_course_completed_by_user(user, course):
    """Vérifie si un utilisateur a complété un cours"""
    try:
        enrollment = Enrollment.objects.get(user=user, course=course)
        return enrollment.is_completed
    except Enrollment.DoesNotExist:
        return False

def get_user_learning_path(user):
    """Retourne le parcours d'apprentissage recommandé pour l'utilisateur"""
    # Logique pour déterminer les prochains cours recommandés
    pass
```

### **Middleware de vérification**

```python
# courses/middleware.py

class PrerequisiteMiddleware:
    """Middleware pour vérifier les prérequis avant l'accès aux cours"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Vérifier les prérequis pour les pages de cours
        if request.path.startswith('/courses/'):
            course_id = self.extract_course_id(request.path)
            if course_id:
                course = Course.objects.get(id=course_id)
                can_access, message = course.can_user_access(request.user)
                
                if not can_access:
                    # Rediriger vers la page des prérequis
                    return redirect(f'/courses/{course_id}/prerequisites/')
        
        response = self.get_response(request)
        return response
    
    def extract_course_id(self, path):
        """Extrait l'ID du cours de l'URL"""
        import re
        match = re.search(r'/courses/(\d+)', path)
        return int(match.group(1)) if match else None
```

---

## 🎨 Interface utilisateur

### **Affichage des prérequis sur la page de cours**

```html
<!-- templates/courses/course_detail.html -->

{% if course.get_mandatory_prerequisites %}
<div class="prerequisites-section mb-4">
    <h5><i class="bi bi-lock me-2"></i>Prérequis requis</h5>
    
    {% for prereq in course.get_mandatory_prerequisites %}
    <div class="prerequisite-item d-flex align-items-center justify-content-between p-3 mb-2 rounded {% if prereq.is_satisfied_by_user(user) %}bg-success bg-opacity-10{% else %}bg-warning bg-opacity-10{% endif %}">
        <div class="d-flex align-items-center">
            <div class="prerequisite-icon me-3">
                {% if prereq.is_satisfied_by_user(user) %}
                    <i class="bi bi-check-circle-fill text-success"></i>
                {% else %}
                    <i class="bi bi-exclamation-triangle-fill text-warning"></i>
                {% endif %}
            </div>
            <div>
                <h6 class="mb-1">{{ prereq.prerequisite_course.title }}</h6>
                <small class="text-muted">
                    {% if prereq.minimum_score %}
                        Score minimum : {{ prereq.minimum_score }}/100
                    {% endif %}
                    {% if prereq.completion_percentage < 100 %}
                        • Completion : {{ prereq.completion_percentage }}%
                    {% endif %}
                </small>
                {% if prereq.description %}
                    <p class="mb-0 small text-muted mt-1">{{ prereq.description }}</p>
                {% endif %}
            </div>
        </div>
        <div>
            {% if prereq.is_satisfied_by_user(user) %}
                <span class="badge bg-success">✓ Validé</span>
            {% else %}
                <a href="{% url 'courses:course_detail' prereq.prerequisite_course.id %}" 
                   class="btn btn-sm btn-primary">
                    <i class="bi bi-arrow-right me-1"></i>Commencer
                </a>
            {% endif %}
        </div>
    </div>
    {% endfor %}
</div>
{% endif %}

{% if not can_access_course %}
<div class="alert alert-warning">
    <h5><i class="bi bi-exclamation-triangle me-2"></i>Accès limité</h5>
    <p>Vous ne pouvez pas accéder à ce cours car les prérequis ne sont pas satisfaits.</p>
    <a href="{% url 'courses:learning_paths' %}" class="btn btn-warning">
        Voir les parcours recommandés
    </a>
</div>
{% else %}
<!-- Bouton d'inscription normal -->
{% endif %}
```

### **Interface de parcours d'apprentissage**

```html
<!-- templates/courses/learning_paths.html -->

<div class="learning-path-container">
    <h3><i class="bi bi-diagram-3 me-2"></i>Parcours d'apprentissage recommandés</h3>
    
    {% for path in learning_paths %}
    <div class="learning-path mb-4">
        <h4>{{ path.name }}</h4>
        <p class="text-muted">{{ path.description }}</p>
        
        <div class="path-nodes">
            {% for course_node in path.courses %}
            <div class="path-node {% if course_node.is_completed_by_user %}completed{% elif course_node.is_accessible %}accessible{% else %}locked{% endif %}">
                <div class="node-content">
                    <div class="node-icon">
                        {% if course_node.is_completed_by_user %}
                            <i class="bi bi-check-circle-fill"></i>
                        {% elif course_node.is_accessible %}
                            <i class="bi bi-play-circle"></i>
                        {% else %}
                            <i class="bi bi-lock-fill"></i>
                        {% endif %}
                    </div>
                    <div class="node-info">
                        <h6>{{ course_node.course.title }}</h6>
                        <small>{{ course_node.course.get_level_display }}</small>
                    </div>
                    <div class="node-action">
                        {% if course_node.is_completed_by_user %}
                            <span class="badge bg-success">Terminé</span>
                        {% elif course_node.is_accessible %}
                            <a href="{% url 'courses:course_detail' course_node.course.id %}" 
                               class="btn btn-sm btn-primary">Continuer</a>
                        {% else %}
                            <button class="btn btn-sm btn-secondary" disabled>Verrouillé</button>
                        {% endif %}
                    </div>
                </div>
                
                {% if not forloop.last %}
                <div class="path-arrow">
                    <i class="bi bi-arrow-down"></i>
                </div>
                {% endif %}
            </div>
            {% endfor %}
        </div>
    </div>
    {% endfor %}
</div>

<style>
.learning-path-container {
    max-width: 800px;
    margin: 0 auto;
}

.path-nodes {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.path-node {
    background: white;
    border: 2px solid #e2e8f0;
    border-radius: 12px;
    padding: 1rem;
    transition: all 0.3s ease;
}

.path-node.completed {
    border-color: #22c55e;
    background: #f0fdf4;
}

.path-node.accessible {
    border-color: #3b82f6;
    background: #eff6ff;
}

.path-node.locked {
    border-color: #94a3b8;
    background: #f8fafc;
    opacity: 0.7;
}

.node-content {
    display: flex;
    align-items: center;
    gap: 1rem;
}

.node-icon {
    font-size: 1.5rem;
}

.node-info {
    flex: 1;
}

.path-arrow {
    text-align: center;
    color: #6b7280;
    font-size: 1.5rem;
}
</style>
```

---

## 💡 Cas d'utilisation

### **🎯 Cas simple - Prérequis unique**

```python
# React Intermédiaire nécessite JavaScript Débutant
CoursePrerequisite.objects.create(
    course=react_course,
    prerequisite_course=js_course,
    is_mandatory=True,
    description="JavaScript est nécessaire pour comprendre React"
)
```

**Résultat attendu :**
```
📚 Parcours "Développeur Frontend"
├── JavaScript Débutant ✓ [Requis]
└── React Intermédiaire 🔒 [Nécessite JS Débutant]
```

### **🎯 Cas avancé - Prérequis avec conditions**

```python
# Node.js Avancé nécessite React Intermédiaire avec 80% de completion
CoursePrerequisite.objects.create(
    course=nodejs_course,
    prerequisite_course=react_course,
    is_mandatory=True,
    completion_percentage=80,
    minimum_score=70,
    description="React et Node.js partagent des concepts JavaScript avancés"
)
```

**Résultat attendu :**
```
📚 Parcours "Développeur Full Stack"
├── HTML/CSS Débutant ✓
├── JavaScript Débutant ✓
├── React Intermédiaire 🔄 [80% requis]
└── Node.js Avancé 🔒 [Nécessite React 80%+]
```

### **🎯 Cas multiple - Plusieurs prérequis**

```python
# Full Stack nécessite plusieurs cours
CoursePrerequisite.objects.create(course=fullstack_course, prerequisite_course=html_course)
CoursePrerequisite.objects.create(course=fullstack_course, prerequisite_course=js_course)
CoursePrerequisite.objects.create(course=fullstack_course, prerequisite_course=react_course)
```

**Résultat attendu :**
```
📚 Parcours "Full Stack Developer"
├── HTML/CSS Débutant ✓ [Requis]
├── JavaScript Débutant ✓ [Requis]
├── React Intermédiaire ✓ [Requis]
└── Full Stack Project 🔒 [Nécessite les 3 précédents]
```

---

## 🚀 Étapes d'implémentation

### **Phase 1 - Structure de base (1-2 jours)**

1. **Créer le modèle `CoursePrerequisite`**
   ```bash
   python manage.py makemigrations courses
   python manage.py migrate
   ```

2. **Ajouter les méthodes au modèle `Course`**
   - `get_prerequisites()`
   - `can_user_access()`
   - `get_missing_prerequisites_for_user()`

3. **Créer l'interface admin**
   - Enregistrement du modèle dans `admin.py`
   - Interface pour gérer les prérequis

### **Phase 2 - Logique métier (2-3 jours)**

1. **Implémenter la vérification des prérequis**
   - Middleware de vérification
   - Logique dans les views

2. **Modifier les vues existantes**
   - `CourseDetailView` : vérifier les prérequis
   - `EnrollmentView` : valider avant inscription

3. **Créer les signaux**
   - Déblocage automatique des cours
   - Notifications de prérequis validés

### **Phase 3 - Interface utilisateur (3-4 jours)**

1. **Modifier `course_detail.html`**
   - Affichage des prérequis
   - Messages d'accès limité

2. **Créer la page des parcours**
   - `learning_paths.html`
   - Graphiques de progression

3. **Ajouter les styles CSS**
   - Design des parcours
   - Animations et transitions

### **Phase 4 - Fonctionnalités avancées (2-3 jours)**

1. **Parcours recommandés**
   - Algorithme de recommandation
   - Parcours personnalisés

2. **Statistiques et rapports**
   - Taux de completion des parcours
   - Analyse des prérequis

3. **Tests et validation**
   - Tests unitaires
   - Tests d'intégration

---

## 🗄️ Migration de base de données

```python
# courses/migrations/0002_add_course_prerequisites.py

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings

class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CoursePrerequisite',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_mandatory', models.BooleanField(default=True, verbose_name='Prérequis obligatoire')),
                ('minimum_score', models.IntegerField(blank=True, null=True, verbose_name='Score minimum requis')),
                ('completion_percentage', models.IntegerField(default=100, verbose_name='Pourcentage de completion requis')),
                ('description', models.TextField(blank=True, verbose_name='Description du prérequis')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='prerequisites', to='courses.course', verbose_name='Cours cible')),
                ('prerequisite_course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='required_for', to='courses.course', verbose_name='Cours prérequis')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_prerequisites', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Prérequis de cours',
                'verbose_name_plural': 'Prérequis de cours',
                'ordering': ['course', 'created_at'],
            },
        ),
        migrations.AddConstraint(
            model_name='courseprerequisite',
            constraint=models.CheckConstraint(check=~models.Q(course=models.F('prerequisite_course')), name='no_self_prerequisite'),
        ),
        migrations.AlterUniqueTogether(
            name='courseprerequisite',
            unique_together={('course', 'prerequisite_course')},
        ),
    ]
```

---

## 🛠️ Interface admin

```python
# courses/admin.py

from django.contrib import admin
from .models import Course, CoursePrerequisite

@admin.register(CoursePrerequisite)
class CoursePrerequisiteAdmin(admin.ModelAdmin):
    list_display = [
        'course', 
        'prerequisite_course', 
        'is_mandatory', 
        'minimum_score', 
        'completion_percentage',
        'created_at'
    ]
    list_filter = [
        'is_mandatory', 
        'created_at',
        'course__category',
        'prerequisite_course__category'
    ]
    search_fields = [
        'course__title', 
        'prerequisite_course__title',
        'description'
    ]
    raw_id_fields = ['course', 'prerequisite_course', 'created_by']
    
    fieldsets = (
        ('Relation de prérequis', {
            'fields': ('course', 'prerequisite_course', 'is_mandatory')
        }),
        ('Conditions', {
            'fields': ('minimum_score', 'completion_percentage', 'description'),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'course', 
            'prerequisite_course', 
            'created_by'
        )

# Inline pour gérer les prérequis directement depuis la page du cours
class CoursePrerequisiteInline(admin.TabularInline):
    model = CoursePrerequisite
    fk_name = 'course'
    extra = 1
    raw_id_fields = ['prerequisite_course']

class CourseAdmin(admin.ModelAdmin):
    # ... configuration existante ...
    inlines = [CoursePrerequisiteInline]
```

---

## 🧪 Tests et validation

### **Tests unitaires**

```python
# courses/tests/test_prerequisites.py

from django.test import TestCase
from django.contrib.auth import get_user_model
from courses.models import Course, CoursePrerequisite, Enrollment

User = get_user_model()

class CoursePrerequisiteTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Créer des cours de test
        self.beginner_course = Course.objects.create(
            title='JavaScript Débutant',
            level='beginner'
        )
        
        self.advanced_course = Course.objects.create(
            title='React Avancé',
            level='advanced'
        )
        
        # Créer le prérequis
        self.prerequisite = CoursePrerequisite.objects.create(
            course=self.advanced_course,
            prerequisite_course=self.beginner_course,
            is_mandatory=True
        )
    
    def test_prerequisite_creation(self):
        """Test la création d'un prérequis"""
        self.assertEqual(self.prerequisite.course, self.advanced_course)
        self.assertEqual(self.prerequisite.prerequisite_course, self.beginner_course)
        self.assertTrue(self.prerequisite.is_mandatory)
    
    def test_can_user_access_without_prerequisite(self):
        """Test l'accès sans prérequis validé"""
        can_access, message = self.advanced_course.can_user_access(self.user)
        self.assertFalse(can_access)
        self.assertIn('Prérequis non satisfait', message)
    
    def test_can_user_access_with_prerequisite(self):
        """Test l'accès avec prérequis validé"""
        # Inscrire l'utilisateur au cours prérequis
        enrollment = Enrollment.objects.create(
            user=self.user,
            course=self.beginner_course,
            is_completed=True
        )
        
        can_access, message = self.advanced_course.can_user_access(self.user)
        self.assertTrue(can_access)
        self.assertEqual(message, "Accès autorisé")
    
    def test_no_self_prerequisite(self):
        """Test qu'un cours ne peut pas être son propre prérequis"""
        with self.assertRaises(Exception):
            CoursePrerequisite.objects.create(
                course=self.beginner_course,
                prerequisite_course=self.beginner_course
            )
    
    def test_circular_reference_detection(self):
        """Test la détection des références circulaires"""
        # Créer une référence circulaire A → B → A
        CoursePrerequisite.objects.create(
            course=self.advanced_course,
            prerequisite_course=self.beginner_course
        )
        
        with self.assertRaises(Exception):
            CoursePrerequisite.objects.create(
                course=self.beginner_course,
                prerequisite_course=self.advanced_course
            )
```

### **Tests d'intégration**

```python
# courses/tests/test_views.py

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from courses.models import Course, CoursePrerequisite

User = get_user_model()

class CourseAccessTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.beginner_course = Course.objects.create(
            title='HTML/CSS Débutant',
            slug='html-css-debutant'
        )
        
        self.advanced_course = Course.objects.create(
            title='React Avancé',
            slug='react-avance'
        )
        
        CoursePrerequisite.objects.create(
            course=self.advanced_course,
            prerequisite_course=self.beginner_course,
            is_mandatory=True
        )
    
    def test_course_detail_without_prerequisite(self):
        """Test l'accès à la page de cours sans prérequis"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(
            reverse('courses:course_detail', kwargs={'slug': 'react-avance'})
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Prérequis requis')
        self.assertContains(response, 'Accès limité')
    
    def test_course_detail_with_prerequisite_completed(self):
        """Test l'accès après complétion du prérequis"""
        # Marquer le prérequis comme complété
        Enrollment.objects.create(
            user=self.user,
            course=self.beginner_course,
            is_completed=True
        )
        
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(
            reverse('courses:course_detail', kwargs={'slug': 'react-avance'})
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Accès limité')
```

---

## 🚀 Fonctionnalités avancées

### **1. Algorithmes de recommandation**

```python
# courses/recommendations.py

class LearningPathRecommender:
    """Système de recommandation de parcours d'apprentissage"""
    
    def recommend_next_courses(self, user, limit=5):
        """Recommande les prochains cours pour un utilisateur"""
        completed_courses = Course.objects.filter(
            enrollments__user=user,
            enrollments__is_completed=True
        )
        
        # Trouver les cours qui ont ces cours comme prérequis
        potential_courses = Course.objects.filter(
            prerequisites__prerequisite_course__in=completed_courses,
            prerequisites__is_mandatory=True
        ).exclude(
            enrollments__user=user
        )
        
        # Filtrer les cours dont tous les prérequis sont satisfaits
        recommended = []
        for course in potential_courses:
            can_access, _ = course.can_user_access(user)
            if can_access:
                recommended.append(course)
        
        return recommended[:limit]
    
    def create_learning_path(self, user, target_course):
        """Crée un parcours d'apprentissage personnalisé"""
        path = []
        current_course = target_course
        
        while current_course:
            path.insert(0, current_course)
            
            # Trouver les prérequis non complétés
            missing_prereqs = current_course.get_missing_prerequisites_for_user(user)
            
            if not missing_prereqs:
                break
            
            # Prendre le premier prérequis manquant
            current_course = missing_prereqs[0].prerequisite_course
        
        return path
```

### **2. Statistiques et analytics**

```python
# courses/analytics.py

class PrerequisiteAnalytics:
    """Analytics pour les prérequis et parcours"""
    
    def get_completion_rates(self):
        """Taux de completion des prérequis"""
        from django.db.models import Count, Avg
        
        return CoursePrerequisite.objects.aggregate(
            avg_completion_rate=Avg('completion_percentage'),
            mandatory_count=Count('id', filter=models.Q(is_mandatory=True)),
            optional_count=Count('id', filter=models.Q(is_mandatory=False))
        )
    
    def get_most_blocking_prerequisites(self, limit=10):
        """Prérequis qui bloquent le plus d'utilisateurs"""
        from django.db.models import Count
        
        return CoursePrerequisite.objects.annotate(
            blocking_count=Count(
                models.Case(
                    models.When(
                        prerequisite_course__enrollments__is_completed=False,
                        then=1
                    ),
                    default=0,
                    output_field=models.IntegerField()
                )
            )
        ).order_by('-blocking_count')[:limit]
    
    def get_learning_path_efficiency(self):
        """Efficacité des parcours d'apprentissage"""
        # Logique pour analyser combien d'utilisateurs suivent les parcours recommandés
        pass
```

### **3. Notifications et signaux**

```python
# courses/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Enrollment, CoursePrerequisite
from .notifications import send_prerequisite_unlocked_notification

@receiver(post_save, sender=Enrollment)
def enrollment_completed(sender, instance, created, **kwargs):
    """Quand un utilisateur complète un cours"""
    if instance.is_completed:
        # Vérifier si cela débloque de nouveaux cours
        unlocked_courses = []
        
        for course_prereq in instance.course.required_for.all():
            if course_prereq.is_satisfied_by_user(instance.user):
                unlocked_courses.append(course_prereq.course)
        
        if unlocked_courses:
            send_prerequisite_unlocked_notification(
                instance.user,
                instance.course,
                unlocked_courses
            )

@receiver(post_save, sender=CoursePrerequisite)
def prerequisite_created(sender, instance, created, **kwargs):
    """Quand un nouveau prérequis est créé"""
    if created:
        # Vérifier si cela affecte des utilisateurs existants
        affected_users = User.objects.filter(
            enrollments__course=instance.course
        ).distinct()
        
        for user in affected_users:
            can_access, _ = instance.course.can_user_access(user)
            if not can_access:
                # Notifier l'utilisateur que l'accès a été restreint
                send_access_restricted_notification(user, instance.course)
```

### **4. API REST pour les parcours**

```python
# courses/api.py

from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

class CoursePrerequisiteSerializer(serializers.ModelSerializer):
    prerequisite_course_title = serializers.CharField(source='prerequisite_course.title', read_only=True)
    is_satisfied = serializers.SerializerMethodField()
    
    class Meta:
        model = CoursePrerequisite
        fields = [
            'id', 'prerequisite_course', 'prerequisite_course_title',
            'is_mandatory', 'minimum_score', 'completion_percentage',
            'description', 'is_satisfied'
        ]
    
    def get_is_satisfied(self, obj):
        user = self.context['request'].user
        return obj.is_satisfied_by_user(user) if user.is_authenticated else False

class LearningPathViewSet(viewsets.ReadOnlyModelViewSet):
    """API pour les parcours d'apprentissage"""
    
    @action(detail=False, methods=['get'])
    def recommended(self, request):
        """Retourne les cours recommandés pour l'utilisateur"""
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=401)
        
        recommender = LearningPathRecommender()
        courses = recommender.recommend_next_courses(request.user)
        
        serializer = CourseSerializer(courses, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_progress(self, request):
        """Retourne la progression de l'utilisateur"""
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=401)
        
        # Logique pour calculer la progression
        pass
```

---

## 📝 Conclusion

Ce système de parcours avec prérequis transformera complètement l'expérience d'apprentissage :

### **🎯 Bénéfices pour les utilisateurs**
- **Apprentissage structuré** : Progression logique et guidée
- **Motivation** : Objectifs clairs et atteignables
- **Confiance** : Acquisition des compétences nécessaires

### **🎯 Bénéfices pour la plateforme**
- **Rétention améliorée** : Users plus engagés
- **Taux de completion** : Plus élevé grâce aux parcours guidés
- **Personnalisation** : Parcours adaptés à chaque utilisateur

### **🎯 Évolution future**
- **IA de recommandation** : Parcours encore plus personnalisés
- **Badges et certifications** : Récompenses pour les parcours
- **Analyse avancée** : Comprendre les patterns d'apprentissage

**Ce système positionnera CRVSTrainingZ comme une plateforme d'e-learning moderne et intelligente !** 🚀

---

*Documentation créée le 3 février 2026*
*Dernière mise à jour : 3 février 2026*
