from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db import models
from django.apps import apps
from nested_admin import NestedModelAdmin, NestedStackedInline, NestedTabularInline

# Utiliser l'admin par défaut de Django

from django.contrib.admin.sites import AlreadyRegistered
from .models import Course, Module, Lesson, UserLessonProgress, Category, Enrollment, LessonVideo, Comment, Competence, LearningPath, LearningPathTemplate, CourseCompletion
from .widgets import MultipleStructuresWidget

from .utils import duplicate_course as duplicate_course_func

# Inline classes pour Nested Admin
class LessonVideoInline(NestedTabularInline):
    model = LessonVideo
    extra = 1
    fields = ('title', 'video_file', 'order', 'duration')
    readonly_fields = ('duration',)

class CommentInline(NestedTabularInline):
    model = Comment
    extra = 1
    fields = ('user', 'content', 'created_at')
    readonly_fields = ('created_at',)

class LessonInline(NestedTabularInline):
    model = Lesson
    extra = 2
    fields = ('title', 'order', 'is_active', 'duration')
    readonly_fields = ('duration',)
    inlines = [LessonVideoInline]  # Vidéos à l'intérieur des leçons

class ModuleInline(NestedStackedInline):
    model = Module
    extra = 2  # 2 formulaires vides pour modules
    fields = ('title', 'description', 'level', 'order', 'is_locked', 'is_paid', 'price')
    inlines = [LessonInline]  # Leçons à l'intérieur des modules
    show_change_link = True
    min_num = 0
    max_num = 10

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'image_preview')                # Affiche Name, Slug et aperçu de l'image
    prepopulated_fields = {"slug": ("name",)}     # Remplit automatiquement Slug à partir de Name
    readonly_fields = ('image_preview',)
    fieldsets = (
        ('Informations générales', {
            'fields': ('name', 'image')
        }),
        ('URL', {
            'fields': ('slug',),
            'classes': ('collapse',)
        }),
        ('Aperçu', {
            'fields': ('image_preview',),
            'classes': ('collapse',)
        }),
    )
    
    def image_preview(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" width="100" height="100" style="object-fit: cover; border-radius: 5px;" />'
        return "Aucune image"
    image_preview.short_description = 'Aperçu de l\'image'
    image_preview.allow_tags = True


@admin.register(Competence)
class CompetenceAdmin(admin.ModelAdmin):
    list_display = ('nom', 'created_at')
    search_fields = ('nom', 'description')
    list_filter = ('created_at',)
    ordering = ('nom',)
    fieldsets = (
        ('Informations générales', {
            'fields': ('nom', 'description')
        }),
        ('Métadonnées', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at',)


@admin.register(Course)
class CourseAdmin(NestedModelAdmin):
    list_display = ('title', 'category', 'niveau', 'cible', 'language', 'order', 'created_by', 'created_at', 'is_published')
    search_fields = ('title', 'category__name', 'language', 'niveau', 'cible', 'competences__nom')
    list_filter = ('language', 'category', 'niveau', 'cible', 'competences', 'created_at', 'is_published')
    list_editable = ('order', 'is_published')
    actions = ['duplicate_course']
    inlines = [ModuleInline]  # Uniquement les modules
    filter_horizontal = ('competences',)
    fieldsets = (
        ('Informations générales', {
            'fields': ('title', 'description', 'category', 'niveau', 'cible', 'competences', 'thumbnail', 'video_promotionnelle', 'language', 'is_published', 'order')
        }),
        ('Métadonnées', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at',)
    
    def duplicate_course(self, request, queryset):
        """Action pour dupliquer un cours sélectionné"""
        if queryset.count() != 1:
            self.message_user(request, "Veuillez sélectionner un seul cours à dupliquer.", level='error')
            return
            
        original_course = queryset.first()
        try:
            new_course = duplicate_course_func(original_course)
            self.message_user(
                request, 
                f"Le cours a été dupliqué avec succès. Nouveau cours : {new_course.title}", 
                level='success'
            )
        except Exception as e:
            self.message_user(
                request, 
                f"Une erreur est survenue lors de la duplication du cours : {str(e)}", 
                level='error'
            )
    duplicate_course.short_description = "Dupliquer le cours sélectionné"


@admin.register(Module)
class ModuleAdmin(NestedModelAdmin):
    list_display = ('title', 'course', 'level', 'order', 'is_paid', 'price')
    list_filter = ('course', 'level', 'is_paid')
    ordering = ('course', 'order')
    inlines = [LessonInline]  # Leçons directement dans l'admin des modules


class IsActiveFilter(admin.SimpleListFilter):
    title = 'statut actif'
    parameter_name = 'is_active'

    def lookups(self, request, model_admin):
        return (
            ('1', 'Actives uniquement'),
            ('0', 'Inactives uniquement'),
        )

    def queryset(self, request, queryset):
        if self.value() == '1':
            return queryset.filter(is_active=True)
        if self.value() == '0':
            return queryset.filter(is_active=False)
        return queryset

@admin.register(Lesson)
class LessonAdmin(NestedModelAdmin):
    list_display = ('title', 'module', 'order', 'is_active', 'created_at')
    list_filter = (IsActiveFilter, 'module', 'created_at')
    list_editable = ('is_active', 'order')
    ordering = ('module', 'order')
    actions = ['mark_as_active', 'mark_as_inactive']
    inlines = [LessonVideoInline, CommentInline]
    
    def get_queryset(self, request):
        # Par défaut, n'afficher que les leçons actives
        qs = super().get_queryset(request)
        if not request.GET.get('is_active') and not request.POST.get('action'):
            qs = qs.filter(is_active=True)
        return qs
    
    @admin.action(description='Marquer les leçons sélectionnées comme actives')
    def mark_as_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} leçon(s) marquée(s) comme active(s).')
    
    @admin.action(description='Marquer les leçons sélectionnées comme inactives')
    def mark_as_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} leçon(s) marquée(s) comme inactive(s).')

@admin.register(Enrollment)
class EnrollmentAdmin(NestedModelAdmin):
    list_display = ('user', 'course', 'enrolled_at')
    list_filter = ('enrolled_at', 'course')
    search_fields = ('user__username', 'course__title')

@admin.register(UserLessonProgress)
class UserLessonProgressAdmin(NestedModelAdmin):
    list_display = ('user', 'lesson', 'is_completed', 'completed_at')
    list_filter = ('is_completed', 'completed_at')
    search_fields = ('user__username', 'lesson__title')

@admin.register(LessonVideo)
class LessonVideoAdmin(NestedModelAdmin):
    list_display = ('title', 'lesson', 'order', 'duration', 'views_count')
    list_filter = ('lesson',)
    search_fields = ('title', 'lesson__title')
    list_editable = ('order',)
    ordering = ('lesson', 'order')

# Admin pour LearningPath
@admin.register(LearningPath)
class LearningPathAdmin(NestedModelAdmin):
    list_display = ('user', 'current_course', 'current_lesson', 'last_activity', 'time_spent')
    list_filter = ('last_activity', 'current_course')
    search_fields = ('user__username', 'user__email', 'current_course__title')
    readonly_fields = ('last_activity', 'time_spent')
    fieldsets = (
        ('Informations utilisateur', {
            'fields': ('user',)
        }),
        ('Progression actuelle', {
            'fields': ('current_course', 'current_lesson', 'completed_courses')
        }),
        ('Compétences et objectifs', {
            'fields': ('skills_acquired', 'learning_goals')
        }),
        ('Métadonnées', {
            'fields': ('last_activity', 'time_spent'),
            'classes': ('collapse',)
        }),
    )
    filter_horizontal = ('completed_courses',)

# Admin pour LearningPathTemplate
@admin.register(LearningPathTemplate)
class LearningPathTemplateAdmin(NestedModelAdmin):
    list_display = ('name', 'structure', 'level', 'assignment_mode', 'certification_required', 'enable_email_notifications', 'estimated_duration', 'is_active', 'created_at')
    list_filter = ('structure', 'level', 'assignment_mode', 'certification_required', 'enable_email_notifications', 'is_active', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('courses', 'categories', 'assigned_users')
    actions = ['assign_to_users', 'send_notifications', 'send_email_notifications']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('name', 'structure', 'additional_structures', 'level', 'description')
        }),
        ('Mode d\'assignation', {
            'fields': ('assignment_mode', 'assigned_users'),
            'description': 'Détermine comment ce template est assigné aux utilisateurs. Structure uniquement = tous les utilisateurs de la structure. Utilisateurs spécifiques = seulement les utilisateurs sélectionnés. Both = structure + utilisateurs spécifiques.'
        }),
        ('Notifications', {
            'fields': ('enable_notifications', 'enable_email_notifications', 'email_subject', 'notification_message'),
            'description': 'Configuration des notifications internes et par email envoyées aux utilisateurs concernés.'
        }),
        ('Certification', {
            'fields': ('certification_required', 'certification_threshold', 'auto_generate_certification', 'certification_level', 'certificate_template_name'),
            'description': 'Configuration de la certification automatique pour ce parcours.'
        }),
        ('Contenu', {
            'fields': ('courses', 'categories', 'sequence')
        }),
        ('Paramètres', {
            'fields': ('estimated_duration', 'is_active')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        """Personnaliser les widgets des champs"""
        if db_field.name == 'additional_structures':
            # Utiliser un CharField avec le widget personnalisé
            kwargs['widget'] = MultipleStructuresWidget(choices=LearningPathTemplate.STRUCTURE_CHOICES)
        return super().formfield_for_dbfield(db_field, request, **kwargs)
    
    def get_queryset(self, request):
        """Optimiser les requêtes"""
        return super().get_queryset(request).prefetch_related(
            'courses', 'categories', 'assigned_users'
        )
    
    def assign_to_users(self, request, queryset):
        """Action admin pour assigner le template aux utilisateurs concernés"""
        count = 0
        for template in queryset:
            assigned = template.assign_to_multiple_users(notify=False)
            count += assigned
        
        self.message_user(
            request, 
            f'{count} utilisateurs ont été assignés aux {queryset.count()} templates sélectionnés.',
            level='success'
        )
    assign_to_users.short_description = "Assigner aux utilisateurs concernés"
    
    def send_notifications(self, request, queryset):
        """Action admin pour envoyer les notifications"""
        total_notifications = 0
        for template in queryset:
            notifications = template.notify_assigned_users()
            total_notifications += notifications
        
        self.message_user(
            request, 
            f'{total_notifications} notifications ont été envoyées pour {queryset.count()} templates.',
            level='success'
        )
    send_notifications.short_description = "Envoyer les notifications"
    
    def send_email_notifications(self, request, queryset):
        """Action admin pour envoyer uniquement les emails"""
        total_emails = 0
        for template in queryset:
            if template.enable_email_notifications:
                users = template.get_recommended_users()
                for user in users:
                    if user.email and template.send_email_notification(user):
                        total_emails += 1
        
        self.message_user(
            request, 
            f'{total_emails} emails ont été envoyés pour {queryset.count()} templates.',
            level='success'
        )
    send_email_notifications.short_description = "Envoyer uniquement les emails"
    
    def save_model(self, request, obj, form, change):
        """Surcharge pour envoyer les notifications lors de la création"""
        super().save_model(request, obj, form, change)
        
        # Si c'est une création et les notifications sont activées
        if not change and obj.enable_notifications:
            notifications_count = obj.notify_assigned_users()
            if notifications_count > 0:
                self.message_user(
                    request, 
                    f'✅ {notifications_count} notifications envoyées automatiquement.',
                    level='success'
                )

# Auto-register any other models in the app without a custom admin
app_config = apps.get_app_config('courses')
for model in app_config.get_models():
    try:
        admin.site.register(model)
    except AlreadyRegistered:
        pass


