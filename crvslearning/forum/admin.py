from django.contrib import admin
from nested_admin import NestedModelAdmin, NestedStackedInline, NestedTabularInline
from .models import Category, Question, Answer, Comment, QuestionVote, Vote, QuestionView

# Vérification que les modèles sont bien chargés
print("Forum admin chargé - modèles:", [Category.__name__, Question.__name__, Answer.__name__])


class CommentInline(NestedTabularInline):
    model = Comment
    extra = 1
    fields = ('author', 'content', 'created_at')
    readonly_fields = ('created_at',)


class VoteInline(NestedTabularInline):
    model = Vote
    extra = 0
    fields = ('user', 'vote_type', 'created_at')
    readonly_fields = ('created_at',)


class AnswerInline(NestedStackedInline):
    model = Answer
    extra = 1
    fields = ('author', 'content', 'is_validated', 'votes_count', 'references', 'created_at')
    readonly_fields = ('created_at',)
    inlines = [CommentInline, VoteInline]


class QuestionVoteInline(NestedTabularInline):
    model = QuestionVote
    extra = 0
    fields = ('user', 'vote_type', 'created_at')
    readonly_fields = ('created_at',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'icon', 'created_at')
    search_fields = ('name', 'description')
    list_filter = ('created_at',)
    ordering = ('name',)
    fieldsets = (
        ('Informations générales', {
            'fields': ('name', 'description')
        }),
        ('Apparence', {
            'fields': ('color', 'icon')
        }),
        ('Métadonnées', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at',)


@admin.register(Question)
class QuestionAdmin(NestedModelAdmin):
    list_display = ('title', 'author', 'category', 'course', 'module', 'lesson', 'created_at', 'views_count')
    search_fields = ('title', 'content', 'author__username')
    list_filter = ('category', 'course', 'created_at')
    inlines = [AnswerInline, QuestionVoteInline]
    filter_horizontal = ()
    fieldsets = (
        ('Informations générales', {
            'fields': ('title', 'content', 'author', 'category')
        }),
        ('Contexte pédagogique', {
            'fields': ('course', 'module', 'lesson'),
            'classes': ('collapse',)
        }),
        ('Classification', {
            'fields': ('tags',)
        }),
        ('Statut', {
            'fields': ('is_closed', 'is_validated', 'validated_by', 'validated_at')
        }),
        ('Statistiques', {
            'fields': ('views_count',),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('views_count', 'created_at', 'updated_at', 'validated_at')


@admin.register(Answer)
class AnswerAdmin(NestedModelAdmin):
    list_display = ('content_preview', 'author', 'question', 'is_validated', 'votes_count', 'created_at')
    search_fields = ('content', 'author__username', 'question__title')
    list_filter = ('is_validated', 'created_at')
    inlines = [CommentInline, VoteInline]
    
    def content_preview(self, obj):
        """Affiche un aperçu du contenu de la réponse"""
        if obj.content:
            return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
        return '-'
    content_preview.short_description = 'Aperçu du contenu'
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('question', 'author', 'content')
        }),
        ('Validation', {
            'fields': ('is_validated', 'validated_by', 'validated_at')
        }),
        ('Références', {
            'fields': ('references',),
            'classes': ('collapse',)
        }),
        ('Statistiques', {
            'fields': ('votes_count',),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('votes_count', 'created_at', 'updated_at', 'validated_at')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('answer', 'author', 'content_preview', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('content', 'author__username', 'answer__question__title')
    ordering = ('-created_at',)
    fieldsets = (
        ('Informations générales', {
            'fields': ('answer', 'author', 'content')
        }),
        ('Métadonnées', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at',)
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Aperçu du contenu'


@admin.register(QuestionVote)
class QuestionVoteAdmin(admin.ModelAdmin):
    list_display = ('user', 'question', 'vote_type', 'created_at')
    list_filter = ('vote_type', 'created_at')
    search_fields = ('user__username', 'question__title')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ('user', 'answer', 'vote_type', 'created_at')
    list_filter = ('vote_type', 'created_at')
    search_fields = ('user__username', 'answer__question__title')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)


@admin.register(QuestionView)
class QuestionViewAdmin(admin.ModelAdmin):
    list_display = ('question', 'user', 'viewed_at')
    list_filter = ('viewed_at',)
    search_fields = ('question__title', 'user__username')
    ordering = ('-viewed_at',)
    readonly_fields = ('viewed_at',)
