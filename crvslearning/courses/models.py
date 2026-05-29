from django.db import models
from datetime import timedelta
from django.conf import settings
from django.utils.text import slugify
import threading
from django.core.management import call_command
from django.db.models.signals import post_save
from django.dispatch import receiver

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True, help_text='Description de la catégorie')
    image = models.ImageField(upload_to='categories/images/', null=True, blank=True, help_text='Image de la catégorie')

    def save(self, *args, **kwargs):
        # S'assurer que le nom est nettoyé et en minuscules
        self.name = self.name.strip()
        
        # Vérifier si une catégorie avec ce nom existe déjà (insensible à la casse)
        if not self.pk:  # Nouvelle catégorie
            existing = Category.objects.filter(name__iexact=self.name).first()
            if existing:
                # Si une catégorie existe déjà avec ce nom (insensible à la casse),
                # on lève une exception qui sera capturée par le formulaire
                from django.core.exceptions import ValidationError
                raise ValidationError(f"Une catégorie avec le nom '{self.name}' existe déjà.")
        
        # Générer le slug si nécessaire
        if not self.slug:
            self.slug = orig = slugify(self.name)
            
            # Vérifier si le slug existe déjà
            for x in range(1, 100):  # Limite de 100 essais
                if not Category.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                    break
                self.slug = f"{orig}-{x}"
                
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Competence(models.Model):
    nom = models.CharField(max_length=200, unique=True, help_text='Nom de la compétence')
    description = models.TextField(blank=True, help_text='Description détaillée de la compétence')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['nom']
        verbose_name = 'Compétence'
        verbose_name_plural = 'Compétences'
    
    def __str__(self):
        return self.nom


class Course(models.Model):
    LEVEL_CHOICES = [
        ('beginner', 'Débutant'),
        ('intermediate', 'Intermédiaire'),
        ('advanced', 'Avancé'),
    ]
    
    CIBLE_CHOICES = [
        ('bunec', 'BUNEC'),
        ('commune', 'Commune'),
        ('minsante', 'Ministère de la Santé'),
        ('minddevel', 'Ministère du Développement'),
        ('ong', 'ONG'),
        ('universite', 'Université'),
        ('consultant', 'Consultant'),
        ('partenaire', 'Partenaire'),
        ('autre', 'Autre'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    thumbnail = models.ImageField(upload_to='course/thumbnails/', null=True, blank=True)
    niveau = models.CharField(
        max_length=20, 
        choices=LEVEL_CHOICES, 
        default='beginner',
        verbose_name='Niveau',
        help_text='Sélectionnez le niveau du cours'
    )
    cible = models.CharField(
        max_length=20, 
        choices=CIBLE_CHOICES, 
        default='autre',
        verbose_name='Structure cible',
        help_text='Sélectionnez la structure cible pour ce cours'
    )
    video_promotionnelle = models.FileField(
        upload_to='course/promotional_videos/', 
        null=True, 
        blank=True,
        help_text='Vidéo promotionnelle gratuite accessible à tous (format MP4 recommandé)'
    )
    language = models.CharField(
        max_length=10,
        choices=[('fr', 'Français'), ('en', 'English')],
        default='fr'
    )
    competences = models.ManyToManyField(
        Competence,
        blank=True,
        verbose_name='Compétences acquises',
        help_text='Sélectionnez les compétences que l\'apprenant acquerra en suivant ce cours'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='courses'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_published = models.BooleanField('Publié', default=False, 
        help_text='Cocher pour publier le cours et le rendre visible aux utilisateurs')
    order = models.PositiveIntegerField(
        'Ordre',
        default=0,
        help_text='Ordre du cours dans le parcours (0 = non défini, 1+ = ordre séquentiel)'
    )

    def __str__(self):
        return self.title

    def get_total_lessons(self):
        """Calcule le nombre total de leçons dans tous les modules du cours"""
        from courses.models import Lesson
        return Lesson.objects.filter(module__course=self).count()

    def get_next_course(self, user_structure=None):
        """Retourne le cours suivant dans l'ordre séquentiel"""
        if user_structure:
            # Filtrer par structure cible
            next_course = Course.objects.filter(
                order__gt=self.order,
                is_published=True,
                cible=user_structure
            ).order_by('order').first()
        else:
            # Sans filtre de structure
            next_course = Course.objects.filter(
                order__gt=self.order,
                is_published=True
            ).order_by('order').first()
        
        return next_course
    
    def get_previous_course(self, user_structure=None):
        """Retourne le cours précédent dans l'ordre séquentiel"""
        if user_structure:
            # Filtrer par structure cible
            prev_course = Course.objects.filter(
                order__lt=self.order,
                is_published=True,
                cible=user_structure
            ).order_by('-order').first()
        else:
            # Sans filtre de structure
            prev_course = Course.objects.filter(
                order__lt=self.order,
                is_published=True
            ).order_by('-order').first()
        
        return prev_course
    
    def get_total_duration(self):
        """Calcule la durée totale estimée du cours en minutes"""
        from courses.models import Lesson
        lessons = Lesson.objects.filter(module__course=self)
        total_duration = 0
        for lesson in lessons:
            if lesson.duration:
                total_duration += lesson.duration.total_seconds() / 60  # Convertir en minutes
            else:
                total_duration += 30  # Estimation par défaut de 30 minutes par leçon
        return int(total_duration)
    
    def calculate_user_result(self, user):
        """Calcule le résultat d'un utilisateur pour ce cours"""
        from courses.models import CourseResult
        
        result, created = CourseResult.objects.get_or_create(
            user=user,
            course=self,
            defaults={
                'lesson_weight': 0.3,
                'quiz_weight': 0.7,
                'passing_score': 70.0
            }
        )
        
        # Calculer les scores
        result.calculate_scores()
        return result
    
    def get_user_progress_summary(self, user):
        """Retourne un résumé de progression pour un utilisateur"""
        result = self.calculate_user_result(user)
        details = result.get_progress_details()
        
        return {
            'course': self,
            'result': result,
            'progress_details': details,
            'is_enrolled': hasattr(user, 'enrollment_set') and user.enrollment_set.filter(course=self).exists(),
            'final_score': result.final_score,
            'is_passed': result.is_passed,
            'lesson_score': result.lesson_score,
            'quiz_score': result.quiz_score,
        }

class Module(models.Model):
    LEVEL_CHOICES = [
        ('beginner', 'Débutant'),
        ('intermediate', 'Intermédiaire'),
        ('advanced', 'Avancé'),
    ]

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='beginner')
    order = models.PositiveIntegerField(default=1)
    is_locked = models.BooleanField('Verrouillé', default=True, 
        help_text='Si coché, le module est verrouillé jusqu\'à la réussite du module précédent')
    is_paid = models.BooleanField('Payant', default=False, 
        help_text='Si coché, le module nécessite un paiement pour y accéder')
    price = models.DecimalField('Prix', max_digits=10, decimal_places=2, default=0.00, 
        help_text='Prix du module en FCFA')

    class Meta:
        ordering = ['order']

    def save(self, *args, **kwargs):
        # Si c'est le premier module d'un cours, le déverrouiller
        if self.order == 1 and not self.pk:
            self.is_locked = False
        
        # Si le module est avancé, le rendre payant par défaut
        if self.level == 'advanced' and not self.pk:
            self.is_paid = True
            if self.price == 0.00:
                self.price = 5000.00  # Prix par défaut pour les modules avancés
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.course.title} - {self.title}"



class Lesson(models.Model):
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    content_file = models.FileField(upload_to='lessons/files/', blank=True, null=True)
    # video_file = models.FileField(upload_to='lessons/videos/', blank=True, null=True)
    order = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField('Active', default=True)
    thumbnail = models.ImageField(upload_to='lessons/thumbnails/', blank=True, null=True)
    duration = models.DurationField(blank=True, null=True)
    subtitle_file = models.FileField(upload_to='lessons/subtitles/', blank=True, null=True, help_text="Fichier de sous-titres au format .vtt")
    is_processing = models.BooleanField(default=False, help_text="En cours de génération des sous-titres")
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    
    def save(self, *args, **kwargs):
        # Enregistrer l'objet sans vérifier video_file qui n'existe pas dans ce modèle
        super().save(*args, **kwargs)
        
        # La logique de traitement des vidéos a été déplacée dans le modèle LessonVideo
        # Si is_processing est True, démarrer la génération des sous-titres
        if hasattr(self, 'is_processing') and self.is_processing:
            def generate():
                try:
                    from django.core.management import call_command
                    call_command('generate_subtitles', str(self.pk))
                    self.refresh_from_db()
                    self.is_processing = False
                    self.save(update_fields=['is_processing'])
                except Exception as e:
                    logger = logging.getLogger(__name__)
                    logger.error(f"Erreur lors de la génération des sous-titres: {str(e)}")
                    self.is_processing = False
                    self.save(update_fields=['is_processing'])
            
            # Démarrer le traitement en arrière-plan
            import threading
            thread = threading.Thread(target=generate)
            thread.daemon = True
            thread.start()

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.module.title} - {self.title}"


class LessonVideo(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='videos')
    title = models.CharField(max_length=255, blank=True)
    video_file = models.FileField(upload_to='lessons/videos/')
    order = models.PositiveIntegerField(default=1)
    duration = models.DurationField(blank=True, null=True)

    class Meta:
        ordering = ['order', 'id']

    @property
    def views_count(self):
        return self.views.count()

    def __str__(self):
        return self.title or f"Video #{self.pk} for {self.lesson.title}"

class UserLessonProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ('user', 'lesson')


class Comment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    lesson = models.ForeignKey('Lesson', on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} on {self.lesson}: {self.content[:30]}"


class CourseRating(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='ratings')
    rating = models.PositiveSmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'course')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} → {self.course}: {self.rating}"
       
class CourseLike(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'course')
        ordering = ['-created_at']

    def __str__(self):
        return f"❤ {self.user} → {self.course}"

class Enrollment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'course')
        ordering = ['-enrolled_at']

    def __str__(self):
        return f"{self.user.username} inscrit à {self.course.title}"
        

class CourseCompletion(models.Model):
    """Modèle pour suivre les cours marqués comme terminés par les utilisateurs"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='completed_courses')
    course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='completions')
    completed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'course')
        ordering = ['-completed_at']
        verbose_name = 'Achèvement de cours'
        verbose_name_plural = 'Achèvements de cours'
    
    def __str__(self):
        return f"{self.user.username} a terminé {self.course.title}"

class LearningPath(models.Model):
    """Modèle pour suivre le parcours d'apprentissage d'un utilisateur"""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='learning_path'
    )
    current_course = models.ForeignKey(
        'Course', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='active_learners'
    )
    current_lesson = models.ForeignKey(
        'Lesson', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='active_learners'
    )
    completed_courses = models.ManyToManyField(
        'Course',
        related_name='completed_by',
        blank=True
    )
    skills_acquired = models.JSONField(
        default=dict,
        help_text="Compétences acquises avec leur niveau"
    )
    learning_goals = models.TextField(
        blank=True,
        null=True,
        help_text="Objectifs d'apprentissage de l'utilisateur"
    )
    last_activity = models.DateTimeField(auto_now=True)
    time_spent = models.DurationField(
        default=timedelta(),
        help_text="Temps total passé sur la plateforme"
    )
    
    template = models.ForeignKey(
        'LearningPathTemplate',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_paths',
        verbose_name="Template du parcours"
    )
    
    certification_obtained = models.BooleanField(
        default=False,
        verbose_name="Certification obtenue"
    )
    
    certification_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de certification"
    )
    
    certification_progress = models.FloatField(
        default=0.0,
        verbose_name="Progression vers la certification (%)"
    )
    
    last_certification_check = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Dernière vérification de certification"
    )

    def __str__(self):
        return f"Parcours de {self.user.username}"

    def update_progress(self, lesson, is_completed=True):
        """Met à jour la progression d'une leçon"""
        progress, created = LessonProgress.objects.get_or_create(
            user=self.user,
            lesson=lesson,
            defaults={'is_completed': is_completed}
        )
        
        if not created and is_completed and not progress.is_completed:
            progress.is_completed = True
            progress.completed_at = timezone.now()
            progress.save()
        
        # Mettre à jour la leçon en cours
        self.current_lesson = lesson
        self.current_course = lesson.module.course
        self.last_activity = timezone.now()
        self.save()
        
        # Vérifier si le cours est complété
        self._check_course_completion()
        
        return progress

    def _check_course_completion(self):
        """Vérifie si l'utilisateur a terminé tous les modules du cours actuel"""
        if not self.current_course:
            return False
            
        total_lessons = Lesson.objects.filter(
            module__course=self.current_course
        ).count()
        
        completed_lessons = LessonProgress.objects.filter(
            user=self.user,
            lesson__module__course=self.current_course,
            is_completed=True
        ).count()
        
        if total_lessons > 0 and completed_lessons >= total_lessons:
            self.completed_courses.add(self.current_course)
            return True
        return False

    def get_progress_stats(self):
        """Retourne les statistiques de progression"""
        if not self.current_course:
            return {}
            
        total_lessons = Lesson.objects.filter(
            module__course=self.current_course
        ).count()
        
        completed_lessons = LessonProgress.objects.filter(
            user=self.user,
            lesson__module__course=self.current_course,
            is_completed=True
        ).count()
        
        progress_percentage = (
            (completed_lessons / total_lessons * 100) 
            if total_lessons > 0 else 0
        )
        
        return {
            'current_course': self.current_course.title,
            'total_lessons': total_lessons,
            'completed_lessons': completed_lessons,
            'progress_percentage': round(progress_percentage, 1),
            'time_spent': self.time_spent
        }


class LearningPathTemplate(models.Model):
    """Template de parcours d'apprentissage prédéfini"""
    
    STRUCTURE_CHOICES = [
        ('commune', 'Commune'),
        ('minsante', 'Ministère de la Santé'),
        ('bunec', 'BUNEC'),
        ('universite', 'Université'),
        ('ong', 'ONG'),
        ('consultant', 'Consultant'),
        ('partenaire', 'Partenaire'),
        ('autre', 'Autre'),
        ('multi_structure', 'Multi-structures'),
    ]
    
    LEVEL_CHOICES = [
        ('beginner', 'Débutant'),
        ('intermediate', 'Intermédiaire'),
        ('advanced', 'Avancé'),
    ]
    
    name = models.CharField(
        max_length=200,
        verbose_name="Nom du parcours"
    )
    
    structure = models.CharField(
        max_length=20,
        choices=STRUCTURE_CHOICES,
        verbose_name="Structure cible"
    )
    
    # Champ pour assigner à plusieurs structures additionnelles
    additional_structures = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Structures additionnelles",
        help_text="Sélectionnez les structures additionnelles (séparées par des virgules)"
    )
    
    def get_additional_structures_list(self):
        """Retourne la liste des structures additionnelles"""
        if not self.additional_structures:
            return []
        
        # Valider que chaque structure est dans les choix
        valid_structures = [choice[0] for choice in self.STRUCTURE_CHOICES]
        structures = []
        for struct in self.additional_structures.split(','):
            struct = struct.strip()
            if struct in valid_structures:
                structures.append(struct)
        return structures
    
    level = models.CharField(
        max_length=20,
        choices=LEVEL_CHOICES,
        verbose_name="Niveau"
    )
    
    description = models.TextField(
        verbose_name="Description",
        help_text="Description détaillée du parcours d'apprentissage"
    )
    
    courses = models.ManyToManyField(
        'Course',
        related_name='path_templates',
        blank=True,
        verbose_name="Cours inclus"
    )
    
    categories = models.ManyToManyField(
        'Category',
        related_name='path_templates',
        blank=True,
        verbose_name="Catégories"
    )
    
    # Champ pour assigner des utilisateurs spécifiques
    assigned_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='assigned_templates',
        blank=True,
        verbose_name="Utilisateurs assignés",
        help_text="Utilisateurs spécifiques assignés à ce template (en plus de la structure)"
    )
    
    # Champ pour contrôler le mode d'assignation
    assignment_mode = models.CharField(
        max_length=20,
        choices=[
            ('structure_only', 'Structure uniquement'),
            ('users_only', 'Utilisateurs spécifiques uniquement'),
            ('both', 'Structure ET utilisateurs spécifiques'),
        ],
        default='structure_only',
        verbose_name="Mode d'assignation",
        help_text="Comment ce template doit être assigné aux utilisateurs"
    )
    
    # Champ pour activer les notifications
    enable_notifications = models.BooleanField(
        default=True,
        verbose_name="Activer les notifications",
        help_text="Envoyer des notifications aux utilisateurs concernés"
    )
    
    # Champ pour activer les notifications par email
    enable_email_notifications = models.BooleanField(
        default=True,
        verbose_name="Activer les notifications par email",
        help_text="Envoyer également les notifications par email aux utilisateurs"
    )
    
    # Champs de certification (approche scalable)
    certification_required = models.BooleanField(
        default=False,
        verbose_name="Certification requise",
        help_text="Activer la certification automatique pour ce parcours"
    )
    
    certification_threshold = models.IntegerField(
        default=80,
        verbose_name="Seuil de certification (%)",
        help_text="Pourcentage minimum requis pour la certification"
    )
    
    auto_generate_certification = models.BooleanField(
        default=False,
        verbose_name="Génération automatique",
        help_text="Générer automatiquement la certification lorsque le seuil est atteint"
    )
    
    certification_level = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'Débutant'),
            ('intermediate', 'Intermédiaire'),
            ('advanced', 'Avancé'),
        ],
        default='beginner',
        verbose_name="Niveau de certification",
        help_text="Niveau de la certification délivrée"
    )
    
    certificate_template_name = models.CharField(
        max_length=100,
        blank=True,
        default='default',
        verbose_name="Template de certificat",
        help_text="Nom du template utilisé pour générer le certificat PDF"
    )
    
    # Champ pour stocker le message de notification personnalisé
    notification_message = models.TextField(
        blank=True,
        verbose_name="Message de notification",
        help_text="Message personnalisé pour les notifications (laisser vide pour utiliser le message par défaut)"
    )
    
    # Champ pour le sujet de l'email personnalisé
    email_subject = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Sujet de l'email",
        help_text="Sujet personnalisé pour les emails (laisser vide pour utiliser le sujet par défaut)"
    )
    
    sequence = models.JSONField(
        default=dict,
        verbose_name="Séquence recommandée",
        help_text="Structure et ordre des modules"
    )
    
    estimated_duration = models.DurationField(
        verbose_name="Durée estimée",
        help_text="Durée estimée du parcours"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Actif"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Date de mise à jour"
    )
    
    class Meta:
        verbose_name = "Template de parcours"
        verbose_name_plural = "Templates de parcours"
        ordering = ['structure', 'level', 'name']
        unique_together = ['structure', 'level', 'name']
        indexes = [
            models.Index(fields=['structure', 'level']),
            models.Index(fields=['is_active']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.get_structure_display()} ({self.get_level_display()})"
    
    def get_all_structures(self):
        """Retourne toutes les structures pour lesquelles ce template est disponible"""
        structures = [self.structure]
        structures.extend(self.get_additional_structures_list())
        return structures
    
    def is_available_for_structure(self, structure):
        """Vérifie si le template est disponible pour une structure donnée"""
        return structure in self.get_all_structures()
    
    def assign_to_user(self, user):
        """Assigner ce template à un utilisateur"""
        # Récupérer ou créer le LearningPath de l'utilisateur
        learning_path, created = LearningPath.objects.get_or_create(user=user)
        
        # Assigner le template au LearningPath
        learning_path.template = self
        learning_path.save()
        
        # Inscrire l'utilisateur à tous les cours du template
        for course in self.courses.all():
            from .models import Enrollment
            Enrollment.objects.get_or_create(user=user, course=course)
        
        # Définir le premier cours comme cours actuel si aucun cours n'est actif
        if self.courses.exists() and not learning_path.current_course:
            learning_path.current_course = self.courses.first()
            learning_path.save()
        
        # Définir les objectifs par défaut basés sur la structure
        default_goals = self.get_default_learning_goals()
        if default_goals and not learning_path.learning_goals:
            learning_path.learning_goals = default_goals
            learning_path.save()
        
        return learning_path
    
    def get_default_learning_goals(self):
        """Retourne les objectifs d'apprentissage par défaut selon la structure"""
        goals_by_structure = {
            'commune': "Devenir un agent d'état civil compétent dans la gestion des actes de naissance, mariage et décès.",
            'minsante': "Maîtriser la gestion des actes de naissance en milieu médical et collaborer avec les autres structures.",
            'bunec': "Développer une expertise dans la supervision et le contrôle qualité des services d'état civil.",
            'universite': "Acquérir des compétences théoriques et pratiques en démographie et statistiques.",
            'ong': "Appliquer les connaissances en état civil dans le contexte des organisations non gouvernementales.",
            'consultant': "Offrir des services spécialisés en état civil aux clients privés et organisations.",
            'partenaire': "Collaborer efficacement avec les partenaires institutionnels dans les projets d'état civil.",
            'autre': "Développer une polyvalence dans les différents aspects de l'état civil.",
            'multi_structure': "Acquérir des compétences inter-structures pour une compréhension globale du système."
        }
        
        return goals_by_structure.get(self.structure, "Développer ses compétences en état civil.")
    
    def get_recommended_users(self):
        """Retourne les utilisateurs recommandés pour ce template selon le mode d'assignation"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        if self.assignment_mode == 'structure_only':
            return User.objects.filter(structure=self.structure)
        elif self.assignment_mode == 'users_only':
            return self.assigned_users.all()
        elif self.assignment_mode == 'both':
            structure_users = User.objects.filter(structure=self.structure)
            specific_users = self.assigned_users.all()
            return structure_users.union(specific_users)
        else:
            return User.objects.none()
    
    def notify_assigned_users(self, message_type='new_template'):
        """Notifie les utilisateurs assignés à ce template (notifications internes + emails)"""
        if not self.enable_notifications:
            return 0
        
        users = self.get_recommended_users()
        notifications_sent = 0
        emails_sent = 0
        
        for user in users:
            try:
                # Notification interne
                from notifications.models import Notification
                from django.urls import reverse
                
                if message_type == 'new_template':
                    title = f"🎯 Nouveau parcours disponible : {self.name}"
                    if self.notification_message:
                        message = self.notification_message
                    else:
                        message = f"Un nouveau parcours d'apprentissage '{self.name}' de niveau {self.get_level_display()} est disponible pour votre structure."
                    
                    # Créer la notification interne
                    notification = Notification.objects.create(
                        recipient=user,
                        title=title,
                        message=message,
                        notification_type='learning_path',
                        action_url=reverse('courses:assign_learning_path')
                    )
                    notifications_sent += 1
                
                # Email notification
                if self.enable_email_notifications and user.email:
                    email_sent = self.send_email_notification(user, message_type)
                    if email_sent:
                        emails_sent += 1
                    
            except Exception as e:
                print(f"Erreur lors de la notification à {user.username}: {e}")
        
        print(f"✅ {notifications_sent} notifications internes et {emails_sent} emails envoyés")
        return notifications_sent + emails_sent
    
    def send_email_notification(self, user, message_type='new_template'):
        """Envoie un email de notification à un utilisateur"""
        try:
            from django.core.mail import send_mail
            from django.conf import settings
            from django.template.loader import render_to_string
            
            if message_type == 'new_template':
                # Sujet de l'email
                if self.email_subject:
                    subject = self.email_subject
                else:
                    subject = f"🎯 Nouveau parcours d'apprentissage disponible : {self.name}"
                
                # Message de l'email
                if self.notification_message:
                    custom_message = self.notification_message
                else:
                    custom_message = f"Un nouveau parcours d'apprentissage '{self.name}' de niveau {self.get_level_display()} est disponible pour votre structure."
                
                # Contexte pour le template email
                context = {
                    'user': user,
                    'template': self,
                    'custom_message': custom_message,
                    'site_name': getattr(settings, 'SITE_NAME', 'CRVS Learning'),
                    'login_url': f"{getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')}/courses/learning-path/"
                }
                
                # Rendre le template HTML
                html_message = render_to_string('courses/emails/new_learning_path.html', context)
                plain_message = render_to_string('courses/emails/new_learning_path.txt', context)
                
                # Envoyer l'email
                send_mail(
                    subject=subject,
                    message=plain_message,
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@crvslearning.com'),
                    recipient_list=[user.email],
                    html_message=html_message,
                    fail_silently=False
                )
                
                return True
                
        except Exception as e:
            print(f"Erreur lors de l'envoi de l'email à {user.email}: {e}")
            return False
    
    def assign_to_multiple_users(self, users_list=None, notify=True):
        """Assigne ce template à plusieurs utilisateurs"""
        if users_list is None:
            users_list = self.get_recommended_users()
        
        assigned_count = 0
        for user in users_list:
            try:
                learning_path = self.assign_to_user(user)
                assigned_count += 1
            except Exception as e:
                print(f"Erreur lors de l'assignation à {user.username}: {e}")
        
        # Envoyer les notifications si demandé
        if notify:
            notifications_count = self.notify_assigned_users()
            print(f"✅ {assigned_count} utilisateurs assignés, {notifications_count} notifications envoyées")
        else:
            print(f"✅ {assigned_count} utilisateurs assignés")
        
        return assigned_count
    
    def is_user_eligible(self, user):
        """Vérifie si un utilisateur est éligible pour ce template"""
        if self.assignment_mode == 'structure_only':
            return user.structure == self.structure
        elif self.assignment_mode == 'users_only':
            return self.assigned_users.filter(id=user.id).exists()
        elif self.assignment_mode == 'both':
            return (user.structure == self.structure or 
                   self.assigned_users.filter(id=user.id).exists())
        return False
    
    def get_total_duration_weeks(self):
        """Retourne la durée totale en semaines"""
        return self.estimated_duration.days // 7
    
    def get_course_count(self):
        """Retourne le nombre de cours dans ce parcours"""
        return self.courses.count()
    
    def get_category_count(self):
        """Retourne le nombre de catégories dans ce parcours"""
        return self.categories.count()
    
    def get_next_course(self, current_course):
        """Retourne le cours suivant dans la séquence"""
        if not self.sequence or 'modules' not in self.sequence:
            # Si pas de séquence définie, utiliser l'ordre des cours
            courses = list(self.courses.all())
            try:
                current_index = courses.index(current_course)
                if current_index < len(courses) - 1:
                    return courses[current_index + 1]
            except ValueError:
                return None
            return None
        
        # Utiliser la séquence définie
        modules = self.sequence.get('modules', [])
        for module in modules:
            if current_course.id in module.get('courses', []):
                # Trouver le cours suivant dans le même module
                course_ids = module.get('courses', [])
                try:
                    current_index = course_ids.index(current_course.id)
                    if current_index < len(course_ids) - 1:
                        next_course_id = course_ids[current_index + 1]
                        return Course.objects.get(id=next_course_id)
                except (ValueError, Course.DoesNotExist):
                    continue
            # Passer au module suivant
            continue
        
        return None
    
    def is_course_in_template(self, course):
        """Vérifie si un cours fait partie de ce template"""
        return self.courses.filter(id=course.id).exists()
    
    def add_course(self, course):
        """Ajouter un cours au template"""
        self.courses.add(course)
        self.updated_at = timezone.now()
        self.save()
    
    def remove_course(self, course):
        """Retirer un cours du template"""
        self.courses.remove(course)
        self.updated_at = timezone.now()
        self.save()
    
    def add_category(self, category):
        """Ajouter une catégorie au template"""
        self.categories.add(category)
        self.updated_at = timezone.now()
        self.save()
    
    def remove_category(self, category):
        """Retirer une catégorie du template"""
        self.categories.remove(category)
        self.updated_at = timezone.now()
        self.save()
    
    def clone(self, new_name, new_structure=None, new_level=None):
        """Cloner ce template avec de nouvelles caractéristiques"""
        new_template = LearningPathTemplate.objects.create(
            name=new_name,
            structure=new_structure or self.structure,
            level=new_level or self.level,
            description=self.description,
        )
        
        # Copier les cours et catégories
        new_template.courses.set(self.courses.all())
        new_template.categories.set(self.categories.all())
        new_template.sequence = self.sequence
        
        return new_template


class LessonProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='utilisateur')
    lesson = models.ForeignKey('Lesson', on_delete=models.CASCADE, verbose_name='leçon')
    
    # Suivi automatique (80% visionnage)
    watch_percentage = models.FloatField('pourcentage visionné', default=0.0, help_text='Pourcentage de la vidéo regardée')
    watch_time = models.DurationField('temps de visionnage', null=True, blank=True, help_text='Temps total passé sur la leçon')
    auto_completed = models.BooleanField('complétion automatique', default=False, help_text='Complété automatiquement à 80%')
    auto_completed_at = models.DateTimeField('date complétion auto', null=True, blank=True)
    
    # Validation manuelle
    manually_marked = models.BooleanField('marqué manuellement', default=False, help_text='Marqué comme terminé par l\'utilisateur')
    manually_marked_at = models.DateTimeField('date marquage manuel', null=True, blank=True)
    
    # Statut final
    is_fully_completed = models.BooleanField('pleinement complétée', default=False, help_text='Leçon 100% complétée (auto + manuel)')
    completed_at = models.DateTimeField('date de complétion', auto_now_add=True, null=True, blank=True)
    
    # Ancien champ pour compatibilité
    is_completed = models.BooleanField('est complétée', default=False)

    def __str__(self):
        return f"{self.user.username} - {self.lesson.title} ({self.watch_percentage}%)"

    class Meta:
        verbose_name = 'Progression de leçon'
        verbose_name_plural = 'Progressions des leçons'
        unique_together = ('user', 'lesson')
        indexes = [
            models.Index(fields=['user', 'lesson', 'is_fully_completed']),
            models.Index(fields=['auto_completed', 'manually_marked']),
        ]
    
    def calculate_completion(self):
        """Calcule le statut de complétion complet"""
        # Complété si les deux conditions sont remplies
        self.is_fully_completed = (
            self.auto_completed and 
            self.manually_marked
        )
        
        # Mettre à jour le champ is_completed pour compatibilité
        self.is_completed = self.is_fully_completed
        
        if self.is_fully_completed and not self.completed_at:
            from django.utils import timezone
            self.completed_at = timezone.now()
        
        self.save()
        return self.is_fully_completed
    
    def get_completion_percentage(self):
        """Retourne le pourcentage de complétion global"""
        if self.is_fully_completed:
            return 100.0
        elif self.auto_completed and not self.manually_marked:
            return 80.0  # Auto complété mais pas encore validé manuellement
        elif not self.auto_completed and self.manually_marked:
            return 90.0  # Validé manuellement mais pas encore 80%
        else:
            return min(self.watch_percentage, 79.0)  # En cours


class VideoView(models.Model):
    """Modèle pour suivre les vues des vidéos"""
    video = models.ForeignKey('LessonVideo', on_delete=models.CASCADE, related_name='views')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField('adresse IP', null=True, blank=True)
    created_at = models.DateTimeField('date de visualisation', auto_now_add=True)

    class Meta:
        verbose_name = 'Vue vidéo'
        verbose_name_plural = 'Vues vidéo'
        indexes = [
            models.Index(fields=['video', 'user', 'ip_address']),
        ]

    def __str__(self):
        return f"Vue de {self.video.title} par {self.user.username if self.user else self.ip_address}"


class Quiz(models.Model):
    """Quiz associé à une leçon"""
    lesson = models.OneToOneField('Lesson', on_delete=models.CASCADE, verbose_name='leçon', related_name='quiz')
    title = models.CharField('titre du quiz', max_length=255)
    description = models.TextField('description', blank=True)
    total_questions = models.PositiveIntegerField('nombre total de questions', default=5)
    passing_score = models.PositiveIntegerField('score de réussite', default=70, help_text='Score minimum pour réussir (en %)')
    time_limit = models.PositiveIntegerField('limite de temps (minutes)', null=True, blank=True, help_text='Temps limite en minutes, vide pour illimité')
    is_active = models.BooleanField('actif', default=True)
    created_at = models.DateTimeField('date de création', auto_now_add=True)
    
    def __str__(self):
        return f"Quiz: {self.title} ({self.lesson.title})"
    
    class Meta:
        verbose_name = 'Quiz'
        verbose_name_plural = 'Quiz'
        indexes = [
            models.Index(fields=['lesson', 'is_active']),
        ]
    
    def get_user_best_score(self, user):
        """Retourne le meilleur score de l'utilisateur pour ce quiz"""
        best_attempt = self.attempts.filter(user=user).order_by('-score').first()
        return best_attempt.score if best_attempt else 0
    
    def get_user_attempts_count(self, user):
        """Retourne le nombre de tentatives de l'utilisateur"""
        return self.attempts.filter(user=user).count()
    
    def has_user_passed(self, user):
        """Vérifie si l'utilisateur a réussi ce quiz"""
        return self.attempts.filter(user=user, is_passed=True).exists()


class QuizAttempt(models.Model):
    """Tentative de quiz d'un utilisateur"""
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, verbose_name='quiz', related_name='attempts')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='utilisateur')
    score = models.PositiveIntegerField('score obtenu', help_text='Score en pourcentage')
    is_passed = models.BooleanField('réussi', default=False)
    started_at = models.DateTimeField('date de début', auto_now_add=True)
    completed_at = models.DateTimeField('date de fin', null=True, blank=True)
    time_taken = models.DurationField('temps passé', null=True, blank=True, help_text='Temps pris pour compléter le quiz')
    
    def __str__(self):
        return f"{self.user.username} - {self.quiz.title} ({self.score}%)"
    
    class Meta:
        verbose_name = 'Tentative de quiz'
        verbose_name_plural = 'Tentatives de quiz'
        unique_together = ('quiz', 'user', 'started_at')
        indexes = [
            models.Index(fields=['quiz', 'user', 'is_passed']),
            models.Index(fields=['user', 'score']),
            models.Index(fields=['-score', 'completed_at']),
        ]
    
    def save(self, *args, **kwargs):
        # Déterminer si le quiz est réussi
        self.is_passed = self.score >= self.quiz.passing_score
        
        # Calculer le temps pris si non défini
        if self.completed_at and not self.time_taken:
            from django.utils import timezone
            self.time_taken = self.completed_at - self.started_at
        
        super().save(*args, **kwargs)


class CourseResult(models.Model):
    """Résultat global d'un utilisateur pour un cours"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='utilisateur')
    course = models.ForeignKey('Course', on_delete=models.CASCADE, verbose_name='cours')
    
    # Scores
    lesson_score = models.FloatField('score leçons', default=0.0, help_text='Score basé sur la progression des leçons (0-100)')
    quiz_score = models.FloatField('score quiz', default=0.0, help_text='Score moyen des quiz (0-100)')
    final_score = models.FloatField('score final', default=0.0, help_text='Score final pondéré (0-100)')
    
    # Pondérations (peuvent être personnalisées par cours)
    lesson_weight = models.FloatField('poids leçons', default=0.3, help_text='Poids des leçons dans le score final')
    quiz_weight = models.FloatField('poids quiz', default=0.7, help_text='Poids des quiz dans le score final')
    
    # Statut
    is_passed = models.BooleanField('réussi', default=False, help_text='Le cours est réussi si score >= seuil')
    passing_score = models.FloatField('seuil de réussite', default=70.0, help_text='Score minimum pour réussir le cours')
    
    # Dates
    started_at = models.DateTimeField('date de début', auto_now_add=True)
    completed_at = models.DateTimeField('date de complétion', null=True, blank=True)
    last_updated = models.DateTimeField('dernière mise à jour', auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.course.title} ({self.final_score}%)"
    
    class Meta:
        verbose_name = 'Résultat de cours'
        verbose_name_plural = 'Résultats de cours'
        unique_together = ('user', 'course')
        indexes = [
            models.Index(fields=['user', 'course', 'is_passed']),
            models.Index(fields=['course', 'final_score']),
            models.Index(fields=['-final_score', 'completed_at']),
        ]
    
    def calculate_scores(self):
        """Calcule les scores basés sur la progression actuelle"""
        from django.db.models import Avg, Count, Q
        
        # Calculer le score des leçons (30% par défaut)
        lessons = Lesson.objects.filter(module__course=self.course)
        total_lessons = lessons.count()
        
        if total_lessons > 0:
            completed_lessons = LessonProgress.objects.filter(
                user=self.user,
                lesson__in=lessons,
                is_fully_completed=True
            ).count()
            
            self.lesson_score = (completed_lessons / total_lessons) * 100
        else:
            self.lesson_score = 0.0
        
        # Calculer le score des quiz (70% par défaut)
        quizzes = Quiz.objects.filter(lesson__in=lessons, is_active=True)
        
        if quizzes.exists():
            quiz_attempts = QuizAttempt.objects.filter(
                user=self.user,
                quiz__in=quizzes
            )
            
            if quiz_attempts.exists():
                # Prendre le meilleur score pour chaque quiz
                best_scores = {}
                for attempt in quiz_attempts:
                    if attempt.quiz_id not in best_scores or attempt.score > best_scores[attempt.quiz_id]:
                        best_scores[attempt.quiz_id] = attempt.score
                
                if best_scores:
                    self.quiz_score = sum(best_scores.values()) / len(best_scores)
                else:
                    self.quiz_score = 0.0
            else:
                self.quiz_score = 0.0
        else:
            self.quiz_score = 0.0
        
        # Calculer le score final
        self.final_score = (self.lesson_score * self.lesson_weight) + (self.quiz_score * self.quiz_weight)
        
        # Déterminer si le cours est réussi
        self.is_passed = self.final_score >= self.passing_score
        
        # Mettre à jour la date de complétion si réussi
        if self.is_passed and not self.completed_at:
            from django.utils import timezone
            self.completed_at = timezone.now()
        
        self.save()
        return self.final_score
    
    def get_progress_details(self):
        """Retourne les détails de progression"""
        from django.db.models import Count, Q
        
        lessons = Lesson.objects.filter(module__course=self.course)
        total_lessons = lessons.count()
        
        completed_lessons = LessonProgress.objects.filter(
            user=self.user,
            lesson__in=lessons,
            is_fully_completed=True
        ).count()
        
        quizzes = Quiz.objects.filter(lesson__in=lessons, is_active=True)
        passed_quizzes = QuizAttempt.objects.filter(
            user=self.user,
            quiz__in=quizzes,
            is_passed=True
        ).values('quiz').distinct().count()
        
        return {
            'total_lessons': total_lessons,
            'completed_lessons': completed_lessons,
            'lesson_completion_rate': (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0,
            'total_quizzes': quizzes.count(),
            'passed_quizzes': passed_quizzes,
            'quiz_success_rate': (passed_quizzes / quizzes.count() * 100) if quizzes.exists() else 0,
        }