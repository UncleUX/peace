from django.db import models
from django.conf import settings
from courses.models import Course, LearningPathTemplate
import uuid


class Certification(models.Model):
    LEVEL_CHOICES = [
        ('beginner', 'Débutant'),
        ('intermediate', 'Intermédiaire'),
        ('advanced', 'Avancé'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='certifications')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='certifications', null=True, blank=True)
    template = models.ForeignKey(LearningPathTemplate, on_delete=models.CASCADE, related_name='certifications', null=True, blank=True)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    code = models.CharField(max_length=64, unique=True, db_index=True, default="", blank=True)
    title = models.CharField(max_length=255, blank=True, null=True, help_text="Titre de la certification")
    pdf = models.FileField(upload_to='certificates/', blank=True, null=True)
    issued_at = models.DateTimeField(auto_now_add=True)
    is_valid = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'course', 'level'], 
                condition=models.Q(course__isnull=False),
                name='unique_user_course_level'
            ),
            models.UniqueConstraint(
                fields=['user', 'template', 'level'], 
                condition=models.Q(template__isnull=False),
                name='unique_user_template_level'
            )
        ]
        indexes = [
            models.Index(fields=['user', 'issued_at']),
            models.Index(fields=['template', 'is_valid']),
        ]

    def save(self, *args, **kwargs):
        if not self.code:
            # generate a compact unique code
            self.code = uuid.uuid4().hex
        return super().save(*args, **kwargs)

    def __str__(self):
        if self.template:
            return f"Certif {self.template.name} - {self.level} - {self.user}"
        elif self.course:
            return f"Certif {self.course.title} - {self.level} - {self.user}"
        else:
            return f"Certif {self.title} - {self.level} - {self.user}"

    @property
    def display_name(self):
        """Nom affiché de la certification"""
        if self.template:
            return self.template.name
        elif self.course:
            return self.course.title
        else:
            return self.title

# Create your models here.
