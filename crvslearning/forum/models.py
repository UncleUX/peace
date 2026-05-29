from django.db import models
from django.contrib.auth import get_user_model
from courses.models import Course, Module, Lesson
from django.utils import timezone

User = get_user_model()

class Category(models.Model):
    """Catégorie pour classer les questions"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#007bff')
    icon = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Question(models.Model):
    """Question métier posée par les apprenants et formateurs"""
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='forum_questions')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='category_questions')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True, blank=True, related_name='course_questions')
    module = models.ForeignKey(Module, on_delete=models.CASCADE, null=True, blank=True, related_name='module_questions')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, null=True, blank=True, related_name='lesson_questions')
    tags = models.CharField(max_length=500, blank=True, help_text="Tags séparés par des virgules")
    views_count = models.PositiveIntegerField(default=0)
    is_closed = models.BooleanField(default=False)
    is_validated = models.BooleanField(default=False)
    validated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='validated_questions')
    validated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Question"
        verbose_name_plural = "Questions"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        """Retourne l'URL absolue de la question"""
        from django.urls import reverse
        return reverse('forum:question_detail', kwargs={'pk': self.pk})
    
    @property
    def upvotes(self):
        """Nombre de votes positifs"""
        try:
            return self.question_votes.filter(vote_type='up').count()
        except Exception as e:
            # Si le champ vote_type n'existe pas encore (migration pas appliquée)
            return self.question_votes.count()
    
    @property
    def downvotes(self):
        """Nombre de votes négatifs"""
        try:
            return self.question_votes.filter(vote_type='down').count()
        except Exception as e:
            # Si le champ vote_type n'existe pas encore (migration pas appliquée)
            return 0
    
    @property
    def total_votes(self):
        """Total des votes (positifs - négatifs)"""
        return self.upvotes - self.downvotes

class Answer(models.Model):
    """Réponse à une question"""
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='forum_answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='question_answers')
    is_validated = models.BooleanField(default=False)
    validated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='validated_answers')
    validated_at = models.DateTimeField(null=True, blank=True)
    votes_count = models.PositiveIntegerField(default=0)
    references = models.TextField(blank=True, help_text="Références réglementaires ou textes de loi")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Réponse"
        verbose_name_plural = "Réponses"
        ordering = ['is_validated', '-votes_count', '-created_at']
    
    def __str__(self):
        return f"Réponse à {self.question.title}"
    
    @property
    def upvotes(self):
        """Nombre de votes positifs"""
        try:
            return self.answer_votes.filter(vote_type='up').count()
        except Exception as e:
            # Si le champ vote_type n'existe pas encore (migration pas appliquée)
            return self.answer_votes.count()
    
    @property
    def downvotes(self):
        """Nombre de votes négatifs"""
        try:
            return self.answer_votes.filter(vote_type='down').count()
        except Exception as e:
            # Si le champ vote_type n'existe pas encore (migration pas appliquée)
            return 0
    
    @property
    def total_votes(self):
        """Total des votes (positifs - négatifs)"""
        return self.upvotes - self.downvotes

class Comment(models.Model):
    """Commentaire sur une réponse"""
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='answer_comments')
    answer = models.ForeignKey('Answer', on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Commentaire"
        verbose_name_plural = "Commentaires"
        ordering = ['created_at']
    
    def __str__(self):
        return f"Commentaire de {self.author.username} sur {self.answer}"

class QuestionVote(models.Model):
    """Vote sur une question"""
    VOTE_TYPES = [
        ('up', 'Vote positif'),
        ('down', 'Vote négatif'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='question_votes')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='question_votes')
    vote_type = models.CharField(max_length=4, choices=VOTE_TYPES, default='up')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Vote sur question"
        verbose_name_plural = "Votes sur questions"
        unique_together = ['user', 'question']
    
    def __str__(self):
        return f"Vote {self.vote_type} de {self.user.username} pour {self.question}"

class Vote(models.Model):
    """Vote sur une réponse"""
    VOTE_TYPES = [
        ('up', 'Vote positif'),
        ('down', 'Vote négatif'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='forum_votes')
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, related_name='answer_votes')
    vote_type = models.CharField(max_length=4, choices=VOTE_TYPES, default='up')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Vote"
        verbose_name_plural = "Votes"
        unique_together = ['user', 'answer']
    
    def __str__(self):
        return f"Vote {self.vote_type} de {self.user.username} pour {self.answer}"

class QuestionView(models.Model):
    """Suivi des vues des questions"""
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='question_views')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_question_views')
    viewed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Vue de question"
        verbose_name_plural = "Vues de questions"
        unique_together = ['question', 'user']
    
    def __str__(self):
        return f"Vue de {self.user.username} pour {self.question.title}"
