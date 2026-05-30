from django.db import models
from django.conf import settings
from django.utils import timezone
from django.db.models import Avg, Count, Q, F, ExpressionWrapper, DurationField
from django.db.models.functions import Coalesce
from courses.models import Course, Lesson, Module
from users.models import CustomUser

class LearnerProgress(models.Model):
    """
    Suivi de la progression d'un apprenant dans un cours
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='progress')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='learner_progress')
    completed_lessons = models.ManyToManyField(Lesson, blank=True, related_name='completed_by')
    completed_modules = models.ManyToManyField(Module, blank=True, related_name='completed_by')
    is_completed = models.BooleanField(default=False)
    completion_percentage = models.FloatField(default=0.0)
    last_accessed = models.DateTimeField(auto_now=True)
    enrollment_date = models.DateTimeField(auto_now_add=True)
    completion_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Progression Apprenant'
        verbose_name_plural = 'Progression des Apprenants'
        unique_together = ('user', 'course')

    def __str__(self):
        return f"{self.user.username} - {self.course.title} ({self.completion_percentage}%)"

    def update_progress(self):
        """
        Met à jour le pourcentage de complétion du cours
        """
        total_lessons = self.course.get_total_lessons()
        if total_lessons > 0:
            completed = self.completed_lessons.count()
            self.completion_percentage = (completed / total_lessons) * 100
            
            # Mettre à jour la date de complétion si le cours est terminé
            if self.completion_percentage >= 100 and not self.is_completed:
                self.is_completed = True
                self.completion_date = timezone.now()
            elif self.completion_percentage < 100 and self.is_completed:
                self.is_completed = False
                self.completion_date = None
                
            self.save()


class CourseStatistics(models.Model):
    """
    Statistiques agrégées pour un cours
    """
    course = models.OneToOneField(Course, on_delete=models.CASCADE, related_name='statistics')
    total_enrollments = models.PositiveIntegerField(default=0)
    total_completions = models.PositiveIntegerField(default=0)
    average_rating = models.FloatField(default=0.0)
    average_completion_time = models.DurationField(null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Statistiques du Cours'
        verbose_name_plural = 'Statistiques des Cours'

    def __str__(self):
        return f"Statistiques pour {self.course.title}"

    def update_statistics(self):
        """
        Met à jour les statistiques du cours
        """
        from django.db.models import Avg, F, ExpressionWrapper, DurationField
        from django.db.models.functions import Coalesce
        
        # Compter le nombre total d'inscriptions
        self.total_enrollments = self.course.enrollments.count()
        
        # Compter le nombre de complétions
        self.total_completions = self.course.learner_progress.filter(is_completed=True).count()
        
        # Calculer la note moyenne
        avg_rating = self.course.ratings.aggregate(avg=Avg('rating'))['avg']
        self.average_rating = avg_rating if avg_rating is not None else 0.0
        
        # Calculer le temps moyen de complétion
        completed_progress = self.course.learner_progress.filter(
            is_completed=True,
            completion_date__isnull=False,
            enrollment_date__isnull=False
        )
        
        if completed_progress.exists():
            avg_time = completed_progress.annotate(
                completion_time=ExpressionWrapper(
                    F('completion_date') - F('enrollment_date'),
                    output_field=DurationField()
                )
            ).aggregate(avg=Avg('completion_time'))['avg']
            
            if avg_time:
                self.average_completion_time = avg_time
        
        self.save()


class ActivityLog(models.Model):
    """
    Journal d'activité des utilisateurs
    """
    ACTION_CHOICES = [
        ('view_lesson', 'A consulté une leçon'),
        ('complete_lesson', 'A terminé une leçon'),
        ('start_course', 'A commencé un cours'),
        ('complete_course', 'A terminé un cours'),
        ('enroll', 'S\'est inscrit à un cours'),
        ('login', 'Connexion'),
        ('logout', 'Déconnexion'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='activities')
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True, related_name='activities')
    lesson = models.ForeignKey(Lesson, on_delete=models.SET_NULL, null=True, blank=True, related_name='activities')
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Journal d'activité"
        verbose_name_plural = "Journaux d'activité"
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user.username} - {self.timestamp} - {self.get_action_display()}"


class UserProgress(models.Model):
    """
    Suivi de la progression d'un utilisateur dans une leçon spécifique
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='lesson_progress')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='user_progress')
    completed = models.BooleanField(default=False)
    completion_percentage = models.FloatField(default=0.0)
    last_accessed = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    time_spent = models.DurationField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'lesson')


class CourseReminder(models.Model):
    """
    Rappels pour les cours inachevés - système sans conflit
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='course_reminders')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='reminders')
    last_activity = models.DateTimeField(null=True, blank=True, help_text="Dernière activité dans le cours")
    current_lesson = models.ForeignKey(Lesson, on_delete=models.SET_NULL, null=True, blank=True, 
                                     help_text="Dernière leçon consultée")
    progress_percentage = models.FloatField(default=0.0, help_text="Pourcentage de progression actuel")
    is_active = models.BooleanField(default=True, help_text="Rappel actif ou non")
    reminder_count = models.PositiveIntegerField(default=0, help_text="Nombre de rappels envoyés")
    last_reminder_sent = models.DateTimeField(null=True, blank=True, help_text="Date du dernier rappel")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'course')
        verbose_name = 'Rappel de cours'
        verbose_name_plural = 'Rappels de cours'

    def __str__(self):
        return f"Rappel: {self.user.username} - {self.course.title} ({self.progress_percentage}%)"

    def should_remind(self, days_threshold=3):
        """
        Détermine si un rappel doit être envoyé
        """
        if not self.is_active or self.progress_percentage >= 100:
            return False
            
        # Si pas d'activité depuis le seuil en jours
        from django.utils import timezone
        threshold_date = timezone.now() - timezone.timedelta(days=days_threshold)
        
        if not self.last_activity:
            return True
            
        return self.last_activity < threshold_date
    
    def should_remind_immediately(self):
        """
        Détermine si un rappel doit être affiché immédiatement (pour les reconnexions)
        """
        if not self.is_active or self.progress_percentage >= 100:
            return False
            
        # Afficher immédiatement pour les reconnexions
        return True

    def get_next_lesson(self):
        """
        Retourne la prochaine leçon à continuer
        """
        if self.current_lesson:
            # Chercher la leçon suivante dans le même module
            next_lesson = Lesson.objects.filter(
                module=self.current_lesson.module,
                order__gt=self.current_lesson.order
            ).order_by('order').first()
            
            if next_lesson:
                return next_lesson
            
            # Chercher le premier module suivant
            current_module = self.current_lesson.module
            next_module = Module.objects.filter(
                course=self.course,
                order__gt=current_module.order
            ).order_by('order').first()
            
            if next_module:
                return next_module.lessons.order_by('order').first()
        
        # Si pas de leçon actuelle, retourner la première leçon du cours
        first_module = self.course.modules.order_by('order').first()
        if first_module:
            return first_module.lessons.order_by('order').first()
        
        return None

    @classmethod
    def update_or_create_reminder(cls, user, course, lesson=None):
        """
        Met à jour ou crée un rappel pour un utilisateur et cours
        """
        from django.utils import timezone
        
        # Récupérer la progression existante
        learner_progress = LearnerProgress.objects.filter(user=user, course=course).first()
        
        if learner_progress:
            progress_percentage = learner_progress.completion_percentage
            last_activity = learner_progress.last_accessed
        else:
            progress_percentage = 0.0
            last_activity = timezone.now()
        
        # Créer ou mettre à jour le rappel
        reminder, created = cls.objects.update_or_create(
            user=user,
            course=course,
            defaults={
                'current_lesson': lesson,
                'progress_percentage': progress_percentage,
                'last_activity': last_activity,
                'is_active': progress_percentage < 100,  # Désactiver si cours terminé
            }
        )
        
        return reminder
