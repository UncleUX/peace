# users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db.models import Count, Case, When, IntegerField, CharField
from django.db.models.functions import Concat
from django.db.models import Value
from django.utils.html import format_html
from .models import CustomUser, UserPreference

class StructureFilter(admin.SimpleListFilter):
    title = 'Structure'  # Nom du filtre
    parameter_name = 'structure_type'  # Paramètre d'URL pour le filtre

    def lookups(self, request, model_admin):
        return (
            ('bunec', 'BUNEC'),
            ('commune', 'Communes'),
            ('minsante', 'Ministère de la Santé'),
            ('minddevel', 'Ministère du Développement'),
            ('ong', 'ONG'),
            ('universite', 'Universités'),
            ('consultant', 'Consultants'),
            ('partenaire', 'Partenaires'),
            ('autre', 'Autres')
        )

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(structure=self.value())
        return queryset

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'email', 'full_name', 'role', 'structure_display', 'service_commune', 'is_active', 'date_joined', 'user_actions')
    list_filter = (StructureFilter, 'role', 'is_staff', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'service', 'commune')
    list_per_page = 50
    date_hierarchy = 'date_joined'
    
    fieldsets = UserAdmin.fieldsets + (
        ('Informations supplémentaires', {
            'fields': ('role', 'structure', 'service', 'commune', 'avatar', 'cover', 'bio')
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'email', 'first_name', 'last_name')
        }),
        ('Informations supplémentaires', {
            'fields': ('role', 'structure', 'service', 'commune')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            full_name=Case(
                When(first_name__isnull=False, last_name__isnull=False,
                     then=Concat('first_name', Value(' '), 'last_name')),
                default='username',
                output_field=CharField(),
            )
        )
    
    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}" if obj.first_name and obj.last_name else obj.username
    full_name.short_description = 'Nom complet'
    full_name.admin_order_field = 'full_name'
    
    def structure_display(self, obj):
        if obj.structure == 'bunec':
            return 'BUNEC'
        elif obj.structure == 'commune':
            return f'Commune: {obj.commune}'
        return obj.get_structure_display()
    structure_display.short_description = 'Structure'
    structure_display.admin_order_field = 'structure'
    
    def service_commune(self, obj):
        if obj.structure == 'bunec' and obj.service:
            return f'Service: {obj.service}'
        elif obj.structure == 'commune' and obj.commune:
            return f'Commune: {obj.commune}'
        return '—'
    service_commune.short_description = 'Service/Commune'
    
    def user_actions(self, obj):
        return format_html(
            '<a class="button" href="{}/change/">Modifier</a>',
            obj.id
        )
    user_actions.short_description = 'Actions'
    user_actions.allow_tags = True
    
    def get_list_display_links(self, request, list_display):
        return ['username']

class StructureStats(admin.ModelAdmin):
    change_list_template = 'admin/users/customuser/stats.html'
    
    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(
            request,
            extra_context=extra_context,
        )
        
        try:
            qs = response.context_data['cl'].queryset
        except (AttributeError, KeyError):
            return response
            
        # Statistiques par structure
        stats = qs.values('structure').annotate(
            total=Count('id'),
            active=Count(Case(When(is_active=True, then=1), output_field=IntegerField())),
            staff=Count(Case(When(is_staff=True, then=1), output_field=IntegerField())),
        ).order_by('-total')
        
        response.context_data['structure_stats'] = list(stats)
        return response


class UserPreferenceAdmin(admin.ModelAdmin):
    """
    Administration des préférences utilisateur
    """
    list_display = ('user', 'theme', 'language', 'favorite_modules_count', 'favorite_categories_count', 
                   'email_notifications', 'last_activity', 'created_at')
    list_filter = ('theme', 'language', 'email_notifications', 'push_notifications', 
                   'auto_play_video', 'show_progress', 'cookie_consent')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    list_per_page = 25
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at', 'last_activity')
    
    fieldsets = (
        ('Informations utilisateur', {
            'fields': ('user',)
        }),
        ('Préférences d\'affichage', {
            'fields': ('theme', 'language')
        }),
        ('Favoris', {
            'fields': ('favorite_modules', 'favorite_categories'),
            'classes': ('collapse',)
        }),
        ('Notifications', {
            'fields': ('email_notifications', 'push_notifications')
        }),
        ('Préférences d\'apprentissage', {
            'fields': ('auto_play_video', 'show_progress', 'download_for_offline')
        }),
        ('Session et cookies', {
            'fields': ('session_preferences', 'cookie_consent'),
            'classes': ('collapse',)
        }),
        ('Informations système', {
            'fields': ('created_at', 'updated_at', 'last_activity'),
            'classes': ('collapse',)
        }),
    )
    
    def favorite_modules_count(self, obj):
        """Affiche le nombre de modules favoris"""
        count = len(obj.favorite_modules) if obj.favorite_modules else 0
        return format_html('<span style="color: #3b82f6; font-weight: bold;">{}</span>', count)
    favorite_modules_count.short_description = 'Modules favoris'
    
    def favorite_categories_count(self, obj):
        """Affiche le nombre de catégories favorites"""
        count = len(obj.favorite_categories) if obj.favorite_categories else 0
        return format_html('<span style="color: #10b981; font-weight: bold;">{}</span>', count)
    favorite_categories_count.short_description = 'Catégories favorites'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Si l'objet existe déjà
            return self.readonly_fields + ('user',)
        return self.readonly_fields


# Inline pour afficher les préférences directement dans la page utilisateur
class UserPreferenceInline(admin.StackedInline):
    """
    Inline pour afficher les préférences utilisateur dans la page de l'utilisateur
    """
    model = UserPreference
    extra = 0
    can_delete = False
    readonly_fields = ('created_at', 'updated_at', 'last_activity')
    
    fieldsets = (
        ('Préférences principales', {
            'fields': ('theme', 'language', 'email_notifications', 'push_notifications')
        }),
        ('Favoris', {
            'fields': ('favorite_modules', 'favorite_categories'),
            'classes': ('collapse',)
        }),
        ('Apprentissage', {
            'fields': ('auto_play_video', 'show_progress', 'download_for_offline'),
            'classes': ('collapse',)
        }),
    )


# Ajouter l'inline à CustomUserAdmin
CustomUserAdmin.inlines = [UserPreferenceInline]

# Enregistrement des modèles d'administration
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(UserPreference, UserPreferenceAdmin)

# Ajout d'une vue personnalisée pour les statistiques
admin.site.site_header = "Administration CRVS Learning"
admin.site.index_title = "Tableau de bord"
admin.site.site_title = "Administration"
