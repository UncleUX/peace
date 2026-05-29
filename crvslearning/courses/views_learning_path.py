"""
Vues pour la gestion des parcours d'apprentissage
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Q, Count, Avg
from datetime import timedelta

from .models import LearningPath, LearningPathTemplate, Course, Lesson, LessonProgress

User = get_user_model()


@login_required
def learning_path_welcome(request):
    """
    Page de bienvenue pour les nouveaux utilisateurs du parcours d'apprentissage
    """
    learning_path = request.user.learning_path
    
    # Vérifier si l'utilisateur a déjà un parcours assigné
    has_template = get_recommended_template_for_user(request.user) is not None
    
    # Si l'utilisateur a déjà un parcours, rediriger vers le dashboard
    if has_template and learning_path.completed_courses.exists():
        return redirect('courses:learning_path_dashboard')
    
    context = {
        'learning_path': learning_path,
        'has_template': has_template,
        'user_structure': request.user.get_structure_display(),
    }
    
    return render(request, 'courses/learning_path_welcome.html', context)


@login_required
def learning_path_dashboard(request):
    """
    Dashboard principal du parcours d'apprentissage de l'utilisateur
    """
    learning_path = request.user.learning_path
    
    # Si l'utilisateur n'a pas de parcours assigné, essayer l'assignation automatique
    from courses.models import Enrollment
    if not Enrollment.objects.filter(user=request.user).exists():
        # Tenter l'assignation automatique
        auto_assigned = try_auto_assignment(request.user)
        if auto_assigned:
            messages.success(request, f'Parcours "{auto_assigned.name}" assigné automatiquement !')
        else:
            return redirect('courses:learning_path_welcome')
    
    # Récupérer le template recommandé
    current_template = get_recommended_template_for_user(request.user)
    
    # Statistiques de progression
    stats = get_learning_path_stats(learning_path, current_template)
    
    # Cours du parcours
    if current_template:
        path_courses = current_template.courses.all()
        completed_courses = learning_path.completed_courses.filter(id__in=path_courses)
        current_course = learning_path.current_course
    else:
        path_courses = []
        completed_courses = []
        current_course = None
    
    # Parcours disponibles
    available_templates = get_available_templates_for_user(request.user)
    
    # Calculer le prochain cours si le cours actuel est terminé
    next_course = None
    if current_template and current_course:
        if current_course in completed_courses.all():
            # Le cours actuel est terminé, trouver le prochain
            next_course = current_template.get_next_course(current_course)
    
    context = {
        'learning_path': learning_path,
        'current_template': current_template,
        'path_courses': path_courses,
        'completed_courses': completed_courses,
        'current_course': current_course,
        'next_course': next_course,
        'stats': stats,
        'available_templates': available_templates,
    }
    
    return render(request, 'courses/learning_path_dashboard.html', context)


@login_required
def assign_learning_path(request):
    """
    Page de choix et d'assignation d'un parcours d'apprentissage
    """
    learning_path = request.user.learning_path
    
    if request.method == 'POST':
        template_id = request.POST.get('template_id')
        template = get_object_or_404(LearningPathTemplate, id=template_id)
        
        # Assigner le parcours
        template.assign_to_user(request.user)
        
        messages.success(request, f'Parcours "{template.name}" assigné avec succès !')
        return redirect('courses:learning_path_dashboard')
    
    # Récupérer les parcours disponibles selon la structure
    available_templates = get_available_templates_for_user(request.user)
    
    # Organiser par catégorie pour l'affichage
    templates_by_category = {}
    for template in available_templates:
        for category in template.categories.all():
            if category.name not in templates_by_category:
                templates_by_category[category.name] = []
            templates_by_category[category.name].append(template)
    
    # Si aucune catégorie, organiser par structure
    if not templates_by_category:
        for template in available_templates:
            structure_name = template.get_structure_display()
            if structure_name not in templates_by_category:
                templates_by_category[structure_name] = []
            templates_by_category[structure_name].append(template)
    
    context = {
        'available_templates': available_templates,
        'templates_by_category': templates_by_category,
        'current_path': learning_path,
        'user_structure': request.user.get_structure_display(),
    }
    
    return render(request, 'courses/assign_learning_path.html', context)


@login_required
def update_learning_goals(request):
    """
    Mettre à jour les objectifs d'apprentissage de l'utilisateur
    """
    if request.method == 'POST':
        learning_path = request.user.learning_path
        learning_path.learning_goals = request.POST.get('learning_goals', '')
        learning_path.save()
        
        messages.success(request, 'Objectifs mis à jour avec succès !')
        return redirect('courses:learning_path_dashboard')
    
    return redirect('courses:learning_path_dashboard')


@login_required
def learning_path_progress(request):
    """
    API pour récupérer la progression détaillée du parcours
    """
    learning_path = request.user.learning_path
    current_template = get_recommended_template_for_user(request.user)
    
    if not current_template:
        return JsonResponse({'error': 'Aucun parcours assigné'}, status=404)
    
    # Progression détaillée
    progress_data = {
        'global_progress': get_global_progress_percentage(learning_path, current_template),
        'completed_courses': learning_path.completed_courses.filter(
            id__in=current_template.courses.all()
        ).count(),
        'total_courses': current_template.courses.count(),
        'current_course': {
            'id': learning_path.current_course.id if learning_path.current_course else None,
            'title': learning_path.current_course.title if learning_path.current_course else None,
        },
        'time_spent': str(learning_path.time_spent),
        'skills_acquired': learning_path.skills_acquired,
        'learning_goals': learning_path.learning_goals,
        'last_activity': learning_path.last_activity.isoformat(),
        'next_milestones': get_next_milestones(learning_path, current_template),
    }
    
    return JsonResponse(progress_data)


@login_required
def learning_path_analytics(request):
    """
    Page d'analyse et de statistiques du parcours
    """
    learning_path = request.user.learning_path
    current_template = get_recommended_template_for_user(request.user)
    
    # Statistiques détaillées
    analytics = {
        'time_stats': get_time_statistics(learning_path),
        'course_stats': get_course_statistics(learning_path, current_template),
        'skill_stats': get_skill_statistics(learning_path),
        'progression_trend': get_progression_trend(learning_path),
        'completion_predictions': get_completion_predictions(learning_path, current_template),
    }
    
    context = {
        'learning_path': learning_path,
        'current_template': current_template,
        'analytics': analytics,
    }
    
    return render(request, 'courses/learning_path_analytics.html', context)


class LearningPathComparisonView(LoginRequiredMixin, TemplateView):
    """
    Vue pour comparer différents parcours disponibles
    """
    template_name = 'courses/learning_path_comparison.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Récupérer tous les templates actifs pour la structure de l'utilisateur
        available_templates = get_available_templates_for_user(self.request.user)
        
        # Comparaison des parcours
        comparison_data = []
        for template in available_templates:
            comparison_data.append({
                'template': template,
                'course_count': template.get_course_count(),
                'category_count': template.get_category_count(),
                'duration_weeks': template.get_total_duration_weeks(),
                'difficulty': template.level,
                'structure': template.get_structure_display(),
                'description': template.description[:200] + '...' if len(template.description) > 200 else template.description,
            })
        
        context['comparison_data'] = comparison_data
        context['user_structure'] = self.request.user.get_structure_display()
        
        return context


# Fonctions utilitaires

def get_recommended_template_for_user(user):
    """
    Récupérer le template recommandé pour un utilisateur
    Logique : Priorité au template spécifique à la structure, puis multi-structure
    """
    from django.db.models import Q
    
    # 1. Essayer d'abord un template spécifique à la structure
    try:
        template = LearningPathTemplate.objects.get(
            structure=user.structure,
            level='beginner',
            is_active=True
        )
        print(f"✅ Template spécifique trouvé pour {user.username}: {template.name}")
        return template
    except LearningPathTemplate.DoesNotExist:
        print(f"⚠️ Aucun template spécifique trouvé pour {user.structure}")
    
    # 2. Si pas de template spécifique, essayer un template multi-structure
    try:
        template = LearningPathTemplate.objects.get(
            structure='multi_structure',
            level='beginner',
            is_active=True
        )
        print(f"✅ Template multi-structure trouvé pour {user.username}: {template.name}")
        return template
    except LearningPathTemplate.DoesNotExist:
        print(f"⚠️ Aucun template multi-structure trouvé")
    
    # 3. Si toujours rien, prendre n'importe quel template actif
    try:
        template = LearningPathTemplate.objects.filter(is_active=True).first()
        if template:
            print(f"✅ Template par défaut trouvé pour {user.username}: {template.name}")
            return template
    except:
        print(f"❌ Aucun template actif trouvé pour {user.username}")
        return None


def get_available_templates_for_user(user):
    """
    Récupérer les templates disponibles pour un utilisateur
    Logique : Si l'utilisateur fait partie d'une structure, il doit voir TOUS les parcours correspondants
    """
    from django.db.models import Q
    
    # 1. Templates spécifiques à la structure de l'utilisateur
    structure_templates = LearningPathTemplate.objects.filter(
        structure=user.structure,
        is_active=True
    )
    
    # 2. Templates multi-structures (disponibles pour tout le monde)
    multi_structure_templates = LearningPathTemplate.objects.filter(
        structure='multi_structure',
        is_active=True
    )
    
    # 3. Combiner les deux : structure spécifique + multi-structures
    available_templates = structure_templates | multi_structure_templates
    
    # 4. Si toujours rien (cas rare), inclure tous les templates actifs
    if not available_templates.exists():
        available_templates = LearningPathTemplate.objects.filter(is_active=True)
        print(f"⚠️ Aucun template trouvé pour {user.structure} - affichage de tous les templates")
    
    print(f"📊 Templates disponibles pour {user.username} ({user.structure}): {available_templates.count()}")
    
    return available_templates


def get_learning_path_stats(learning_path, template=None):
    """
    Calculer les statistiques du parcours d'apprentissage
    """
    # Si pas de template, utiliser le current_course pour compatibilité
    if not template:
        if not learning_path.current_course:
            return {
                'global_progress': 0,
                'completed_courses': learning_path.completed_courses.count(),
                'total_lessons': 0,
                'completed_lessons': 0,
                'time_spent': learning_path.time_spent,
                'skills_count': len(learning_path.skills_acquired),
                'last_activity': learning_path.last_activity,
            }
        
        # Compatibilité : calculer sur le current_course uniquement
        total_lessons = Lesson.objects.filter(
            module__course=learning_path.current_course
        ).count()
        
        completed_lessons = LessonProgress.objects.filter(
            user=learning_path.user,
            lesson__module__course=learning_path.current_course,
            is_fully_completed=True
        ).count()
    else:
        # Calculer sur tous les cours du template
        path_courses = template.courses.all()
        total_lessons = Lesson.objects.filter(
            module__course__in=path_courses
        ).count()
        
        completed_lessons = LessonProgress.objects.filter(
            user=learning_path.user,
            lesson__module__course__in=path_courses,
            is_fully_completed=True
        ).count()
        
        # Si le LearningPath a des cours complétés, les utiliser pour le calcul
        if learning_path.completed_courses.exists():
            completed_courses = learning_path.completed_courses.filter(id__in=path_courses).count()
        else:
            completed_courses = 0
    
    # Calculer la progression globale basée sur les cours complétés si template disponible
    if template:
        total_courses = template.courses.count()
        if learning_path.completed_courses.exists():
            completed_courses = learning_path.completed_courses.filter(id__in=template.courses.all()).count()
            progress_percentage = (completed_courses / total_courses * 100) if total_courses > 0 else 0
        else:
            # Fallback sur la progression des leçons
            progress_percentage = (
                (completed_lessons / total_lessons * 100)
                if total_lessons > 0 else 0
            )
    else:
        progress_percentage = (
            (completed_lessons / total_lessons * 100)
            if total_lessons > 0 else 0
        )
    
    return {
        'global_progress': round(progress_percentage, 1),
        'completed_courses': learning_path.completed_courses.count(),
        'total_lessons': total_lessons,
        'completed_lessons': completed_lessons,
        'time_spent': learning_path.time_spent,
        'skills_count': len(learning_path.skills_acquired),
        'last_activity': learning_path.last_activity,
    }


def get_category_progress_stats(learning_path, template):
    """
    Calculer la progression par catégorie
    """
    if not template:
        return {}
    
    category_progress = {}
    
    for category in template.categories.all():
        category_courses = category.course_set.filter(id__in=template.courses.all())
        completed_category_courses = learning_path.completed_courses.filter(
            id__in=category_courses
        )
        
        if category_courses.exists():
            progress_percentage = (
                (completed_category_courses.count() / category_courses.count() * 100)
                if category_courses.count() > 0 else 0
            )
            category_progress[category.name] = round(progress_percentage, 1)
        else:
            category_progress[category.name] = 0
    
    return category_progress


def get_global_progress_percentage(learning_path, template):
    """
    Calculer le pourcentage de progression global
    """
    if not template:
        return 0
    
    total_courses = template.courses.count()
    completed_courses = learning_path.completed_courses.filter(
        id__in=template.courses.all()
    ).count()
    
    return round((completed_courses / total_courses * 100) if total_courses > 0 else 0, 1)


def get_next_milestones(learning_path, template):
    """
    Déterminer les prochaines étapes du parcours
    """
    if not template or not learning_path.current_course:
        return []
    
    milestones = []
    
    # Prochain cours
    next_course = template.get_next_course(learning_path.current_course)
    if next_course:
        milestones.append({
            'type': 'course',
            'title': f"Prochain cours : {next_course.title}",
            'description': next_course.description[:100] + '...' if len(next_course.description) > 100 else next_course.description,
        })
    
    # Prochain module (basé sur la séquence)
    if template.sequence and 'modules' in template.sequence:
        modules = template.sequence.get('modules', [])
        current_module_index = get_current_module_index(learning_path.current_course, modules)
        
        if current_module_index is not None and current_module_index < len(modules) - 1:
            next_module = modules[current_module_index + 1]
            milestones.append({
                'type': 'module',
                'title': f"Prochain module : {next_module.get('name', 'Module sans nom')}",
                'description': f"Contient {len(next_module.get('courses', []))} cours",
            })
    
    return milestones


def get_current_module_index(current_course, modules):
    """
    Trouver l'index du module contenant le cours actuel
    """
    for i, module in enumerate(modules):
        if current_course.id in module.get('courses', []):
            return i
    return None


def get_time_statistics(learning_path):
    """
    Statistiques temporelles du parcours
    """
    # Temps total
    total_time = learning_path.time_spent
    
    # Temps moyen par cours
    completed_courses = learning_path.completed_courses.count()
    avg_time_per_course = (
        total_time / completed_courses
        if completed_courses > 0 else timedelta(0)
    )
    
    # Temps depuis le début
    days_since_start = (timezone.now() - learning_path.user.date_joined).days
    
    return {
        'total_time': str(total_time),
        'avg_time_per_course': str(avg_time_per_course),
        'days_since_start': days_since_start,
        'daily_average': str(total_time / days_since_start) if days_since_start > 0 else str(timedelta(0)),
    }


def get_course_statistics(learning_path, template):
    """
    Statistiques des cours du parcours
    """
    if not template:
        return {}
    
    total_courses = template.courses.count()
    completed_courses = learning_path.completed_courses.filter(
        id__in=template.courses.all()
    ).count()
    
    # Score moyen (si disponible)
    from .models import CourseResult
    course_results = CourseResult.objects.filter(
        user=learning_path.user,
        course__in=template.courses.all()
    )
    
    avg_score = course_results.aggregate(
        avg_score=Avg('final_score')
    )['avg_score'] or 0
    
    return {
        'total_courses': total_courses,
        'completed_courses': completed_courses,
        'completion_rate': round((completed_courses / total_courses * 100) if total_courses > 0 else 0, 1),
        'avg_score': round(avg_score, 1),
        'best_score': course_results.aggregate(max_score=Max('final_score'))['max_score'] or 0,
    }


def get_skill_statistics(learning_path):
    """
    Statistiques des compétences acquises
    """
    skills = learning_path.skills_acquired
    
    return {
        'total_skills': len(skills),
        'skills_by_level': {
            'beginner': len([s for s in skills.values() if s == 'beginner']),
            'intermediate': len([s for s in skills.values() if s == 'intermediate']),
            'advanced': len([s for s in skills.values() if s == 'advanced']),
        },
        'skills_list': list(skills.keys()),
    }


def get_progression_trend(learning_path):
    """
    Tendance de progression sur les 30 derniers jours
    """
    # Cette fonction pourrait être implémentée avec des données historiques
    # Pour l'instant, retourne des données simulées
    return {
        'trend': 'increasing',  # 'increasing', 'decreasing', 'stable'
        'last_30_days_progress': 15.5,  # pourcentage
        'weekly_average': 3.2,  # heures par semaine
    }


def get_completion_predictions(learning_path, template):
    """
    Prédictions de complétion du parcours
    """
    if not template or not learning_path.current_course:
        return {}
    
    # Calcul basé sur la vitesse actuelle
    completed_courses = learning_path.completed_courses.filter(
        id__in=template.courses.all()
    ).count()
    remaining_courses = template.courses.count() - completed_courses
    
    # Temps moyen par cours
    avg_time_per_course = (
        learning_path.time_spent / completed_courses
        if completed_courses > 0 else timedelta(weeks=2)  # estimation par défaut
    )
    
    estimated_completion = timezone.now() + (avg_time_per_course * remaining_courses)
    
    return {
        'estimated_completion_date': estimated_completion.date(),
        'remaining_courses': remaining_courses,
        'estimated_weeks_remaining': (avg_time_per_course * remaining_courses).days // 7,
        'completion_probability': min(95, completed_courses / template.courses.count() * 100) if template.courses.count() > 0 else 0,
    }


def try_auto_assignment(user):
    """
    Tente d'assigner automatiquement un template à l'utilisateur
    Retourne le template assigné ou None
    """
    # Importer la configuration
    from .auto_assignment_config import is_auto_assign_enabled, get_priority_templates, get_assignment_message
    
    # Vérifier si l'auto-assignation est activée pour cette structure
    if not is_auto_assign_enabled(user.structure):
        return None
    
    # Récupérer les templates disponibles pour cette structure
    available_templates = get_available_templates_for_user(user)
    
    if not available_templates.exists():
        return None
    
    # Utiliser les templates ordonnés par priorité
    prioritized_templates = get_priority_templates(available_templates)
    
    for template in prioritized_templates:
        if template:
            # Assigner le template à l'utilisateur
            learning_path = user.learning_path
            
            # Inscrire l'utilisateur à tous les cours du template
            from courses.models import Enrollment
            for course in template.courses.all():
                enrollment, created = Enrollment.objects.get_or_create(user=user, course=course)
                if created:
                    print(f"Auto-assignation: {user.username} inscrit à {course.title}")
            
            # Assigner le template au LearningPath
            learning_path.template = template
            if template.courses.exists() and not learning_path.current_course:
                learning_path.current_course = template.courses.first()
            
            # Définir les objectifs par défaut
            if not learning_path.learning_goals:
                learning_path.learning_goals = template.get_default_learning_goals()
            
            learning_path.save()
            
            # Message de succès personnalisé
            success_message = get_assignment_message(user.structure, 'success')
            print(f"✅ {success_message}: {user.username} → {template.name}")
            
            return template
    
    return None
