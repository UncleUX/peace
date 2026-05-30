import csv
import json
from datetime import datetime, timedelta

from django.shortcuts import render, get_object_or_404, redirect, HttpResponse
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, TemplateView
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Avg, F, ExpressionWrapper, DurationField, Max
from django.db.models import Count, Q
from django.db.models.functions import Coalesce
from django.utils import timezone

from django.contrib.auth import get_user_model
from courses.models import Course, Enrollment, Lesson, Module

# Obtenir le modèle utilisateur personnalisé
CustomUser = get_user_model()
from .models import UserProgress, LearnerProgress, CourseStatistics, ActivityLog, CourseReminder

# Vérifie si l'utilisateur est un formateur ou un administrateur
def is_trainer_or_admin(user):
    return user.is_authenticated and (user.role == 'trainer' or user.is_superuser)

class TrainerOrAdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin pour vérifier que l'utilisateur est un formateur ou un administrateur"""
    def test_func(self):
        return is_trainer_or_admin(self.request.user)

@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(is_trainer_or_admin), name='dispatch')
class LearnerTrackingView(TemplateView):
    template_name = 'tracking/learner_tracking.html'
    paginate_by = 10
    
    def get(self, request, *args, **kwargs):
        # Vérifier si c'est une demande d'exportation CSV
        if 'export' in request.GET and request.GET['export'] == 'csv':
            return self.export_learners_csv()
        return super().get(request, *args, **kwargs)
    
    def export_learners_csv(self):
        from django.db.models import Count
        from django.db.models.functions import Coalesce
        
        # Créer la réponse HTTP avec l'en-tête CSV
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = f'attachment; filename="apprenants_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        # Créer le writer CSV
        writer = csv.writer(response, delimiter=';')
        
        # Écrire l'en-tête
        writer.writerow([
            'Nom', 'Email', 'Cours Inscrits', 'Cours Terminés', 
            'Taux de Complétion Cours', 'Dernière Activité'
        ])
        
        # Obtenir le modèle utilisateur personnalisé
        CustomUser = get_user_model()
        
        # Récupérer les données des apprenants avec les champs nécessaires
        learners = CustomUser.objects.filter(role='learner').annotate(
            courses_enrolled=Count('enrollments', distinct=True),
            courses_completed=Count('completed_courses', distinct=True),
            last_activity=Coalesce('last_login', 'date_joined')
        ).select_related().order_by('-last_activity')
        
        # Écrire les données
        for learner in learners:
            completion_rate = (learner.courses_completed / learner.courses_enrolled * 100) if learner.courses_enrolled > 0 else 0
            
            writer.writerow([
                learner.get_full_name() or learner.username,
                learner.email,
                learner.courses_enrolled,
                learner.courses_completed,
                f"{completion_rate:.1f}%",
                learner.last_activity.strftime('%d/%m/%Y %H:%M') if learner.last_activity else 'Jamais'
            ])
        
        return response
    
    def get_context_data(self, **kwargs):
        from django.db.models import Count, Q
        from django.db.models.functions import Coalesce
        context = super().get_context_data(**kwargs)
        
        # Obtenir le modèle utilisateur personnalisé
        CustomUser = get_user_model()
        
        # Récupérer tous les apprenants avec des statistiques et les champs nécessaires
        learners = CustomUser.objects.filter(role='learner').select_related().annotate(
            courses_enrolled=Count('enrollments', distinct=True),
            courses_completed=Count('completed_courses', distinct=True),
            lessons_completed=Count('lessonprogress', filter=Q(lessonprogress__is_completed=True), distinct=True),
            last_activity=Coalesce('last_login', 'date_joined')
        ).order_by('-last_activity')
        
        # Récupérer les choix de structure
        structure_choices = dict(CustomUser.STRUCTURE_CHOICES)
        
        # Appliquer le filtre de structure si spécifié
        structure_filter = self.request.GET.get('structure', '')
        if structure_filter:
            learners = learners.filter(structure=structure_filter)
            
        # Appliquer le filtre de certification si spécifié
        certification_filter = self.request.GET.get('certification', '')
        if certification_filter:
            if certification_filter == 'with_certification':
                learners = learners.filter(certifications__isnull=False).distinct()
            elif certification_filter == 'without_certification':
                learners = learners.filter(certifications__isnull=True)
        
        # Calculer les statistiques globales
        total_learners = learners.count()
        active_learners = learners.filter(
            last_login__gte=timezone.now() - timedelta(days=30)
        ).count()
        
        # Récupérer le nombre total de cours et de leçons
        from courses.models import Course, Lesson
        total_courses = Course.objects.count()
        total_lessons = Lesson.objects.count()
        
        # Calculer les totaux pour les cours suivis et complétés
        total_enrollments = sum(learner.courses_enrolled for learner in learners)
        total_completed_courses = sum(learner.courses_completed for learner in learners)
        total_completed_lessons = sum(learner.lessons_completed for learner in learners)
        total_available_lessons = total_lessons * total_learners
        
        # Calculer les taux de complétion globaux
        # Pourcentage de cours terminés sur la plateforme
        course_completion_rate = (total_completed_courses / total_enrollments * 100) if total_enrollments > 0 else 0
        
        # Préparer les données pour le graphique des structures
        structure_stats = learners.values('structure').annotate(
            count=Count('id'),
            active=Count('id', filter=Q(last_login__gte=timezone.now() - timedelta(days=30)))
        ).order_by('-count')
        
        # Formater les données pour le graphique
        structure_labels = []
        structure_data = []
        for stat in structure_stats:
            structure_labels.append(structure_choices.get(stat['structure'], 'Non spécifié'))
            structure_data.append(stat['count'])
        
        # Ajouter les données au contexte
        context.update({
            'learners': learners,
            'total_learners': total_learners,
            'active_learners': active_learners,
            'total_courses': total_courses,
            'total_lessons': total_lessons,
            'total_enrollments': total_enrollments,
            'total_completed_courses': total_completed_courses,
            'total_completed_lessons': total_completed_lessons,
            'course_completion_rate': course_completion_rate,
            'structure_choices': structure_choices,
            'structure_filter': structure_filter,
            'structure_labels': structure_labels,
            'structure_data': structure_data,
            'certification_filter': certification_filter if 'certification_filter' in locals() else '',
        })
        
        # Pourcentage de leçons terminées sur la plateforme
        lesson_completion_rate = (total_completed_lessons / (total_lessons * total_learners) * 100) if (total_lessons * total_learners) > 0 else 0
        
        # Calculer le taux d'absence (inverse du taux de complétion des cours)
        absence_rate = 100 - course_completion_rate
        
        # Calculer le nombre de cours manqués
        total_missed_courses = total_enrollments - total_completed_courses
        
        # S'assurer que les taux sont entre 0 et 100%
        course_completion_rate = max(0, min(100, course_completion_rate))
        lesson_completion_rate = max(0, min(100, lesson_completion_rate))
        absence_rate = max(0, min(100, absence_rate))
        
        # Pagination
        page = self.request.GET.get('page', 1)
        paginator = Paginator(learners, self.paginate_by)
        
        try:
            learners_page = paginator.page(page)
        except PageNotAnInteger:
            learners_page = paginator.page(1)
        except EmptyPage:
            learners_page = paginator.page(paginator.num_pages)
        
        # Préparer les données pour le template
        learners_data = []
        for learner in learners_page:
            # Calculer les taux de complétion pour cet apprenant
            course_completion_rate = (learner.courses_completed / learner.courses_enrolled * 100) if learner.courses_enrolled > 0 else 0
            
            # Calculer le taux de complétion des leçons
            total_lessons = Lesson.objects.filter(module__course__enrollments__user=learner).count()
            lesson_completion_rate = (learner.lessons_completed / total_lessons * 100) if total_lessons > 0 else 0
            
            # Calculer la différence pour l'affichage
            lesson_only_completion = max(0, lesson_completion_rate - course_completion_rate)
            
            learners_data.append({
                'user': learner,
                'courses_enrolled': learner.courses_enrolled,
                'courses_completed': learner.courses_completed,
                'course_completion_rate': round(course_completion_rate, 1),
                'lesson_completion_rate': round(lesson_completion_rate, 1),
                'lesson_only_completion': round(lesson_only_completion, 1),  # Nouveau champ
                'last_activity': learner.last_login or learner.date_joined
            })
        
        # Récupérer les choix de structure depuis le modèle CustomUser
        from users.models import CustomUser
        structure_choices = dict(CustomUser.STRUCTURE_CHOICES)
        
        # Récupérer le filtre de structure actuel
        structure_filter = self.request.GET.get('structure', '')
        
        # Filtrer les apprenants par structure si un filtre est appliqué
        if structure_filter:
            learners = learners.filter(structure=structure_filter)
            
        # Calculer les statistiques par structure
        from django.db.models import Count, Q, F, ExpressionWrapper, FloatField, Case, When, Value
        from django.db.models.functions import Coalesce
        
        structure_stats = (CustomUser.objects
            .filter(role='learner')
            .values('structure')
            .annotate(
                total=Count('id'),
                active=Count('id', filter=Q(last_login__gte=timezone.now() - timedelta(days=30))),
                enrolled=Count('enrollments', distinct=True),
                completed=Count('completed_courses', distinct=True)
            )
            .order_by('-total')
        )
        
        # Convertir les statistiques en une liste de dictionnaires avec les noms de structure
        structure_stats_list = []
        for stat in structure_stats:
            structure_code = stat['structure']
            structure_name = structure_choices.get(structure_code, 'Non spécifié')
            completion_rate = (stat['completed'] / stat['enrolled'] * 100) if stat['enrolled'] > 0 else 0
            
            structure_stats_list.append({
                'structure': structure_name,
                'total': stat['total'],
                'active': stat['active'],
                'enrolled': stat['enrolled'],
                'completed': stat['completed'],
                'completion_rate': round(completion_rate, 1)
            })
        
        context.update({
            'learners': learners_data,
            'page_obj': learners_page,
            'paginator': paginator,
            'is_paginated': learners_page.has_other_pages(),
            'total_learners': total_learners,
            'active_learners': active_learners,
            'total_courses': total_courses,
            'total_lessons': total_lessons,
            'total_enrollments': total_enrollments,
            'total_available_lessons': total_available_lessons,
            'total_completed_courses': total_completed_courses,
            'total_missed_courses': total_missed_courses,
            'total_completed_lessons': total_completed_lessons,
            'course_completion_rate': round(course_completion_rate, 1),
            'lesson_completion_rate': round(lesson_completion_rate, 1),
            'absence_rate': round(absence_rate, 1),
            'title': 'Suivi des apprenants',
            'structure_choices': structure_choices,
            'structure_filter': structure_filter,
            'structure_stats': structure_stats_list,
        })
        
        return context

@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(is_trainer_or_admin), name='dispatch')
class CourseProgressView(TemplateView):
    template_name = 'tracking/course_progress.html'
    paginate_by = 10
    
    def get_queryset(self):
        from courses.models import LessonProgress, CourseCompletion
        
        # Récupérer les cours avec des statistiques
        queryset = Course.objects.all()
        
        # Filtrer par créateur si l'utilisateur n'est pas superutilisateur
        if not self.request.user.is_superuser:
            queryset = queryset.filter(created_by=self.request.user)
        
        # Récupérer le nombre de leçons complétées par cours
        completed_lessons = (
            LessonProgress.objects
            .filter(is_completed=True)
            .values('lesson__module__course')
            .annotate(completed_count=Count('id', distinct=True))
        )
        
        # Récupérer le nombre de cours complétés par cours
        completed_courses = (
            CourseCompletion.objects
            .values('course')
            .annotate(completed_count=Count('id', distinct=True))
        )
        
        # Créer des dictionnaires pour un accès rapide
        completed_lessons_dict = {item['lesson__module__course']: item['completed_count'] 
                                for item in completed_lessons}
        
        completed_courses_dict = {item['course']: item['completed_count']
                                for item in completed_courses}
        
        # Annoter les cours avec les statistiques
        queryset = queryset.annotate(
            total_enrollments=Count('enrollments', distinct=True),
            total_lessons=Count('modules__lessons', distinct=True),
            average_rating=Coalesce(Avg('ratings__rating'), 0.0),
            last_activity=Max('enrollments__enrolled_at')
        )
        
        # Ajouter les statistiques à chaque cours
        for course in queryset:
            course.completed_lessons_count = completed_lessons_dict.get(course.id, 0)
            course.completed_courses_count = completed_courses_dict.get(course.id, 0)
            
        return queryset.order_by('-last_activity')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Récupérer les cours avec statistiques
        courses = self.get_queryset()
        
        # Préparer les données pour le graphique
        course_titles = list(courses.values_list('title', flat=True)[:10])
        completion_rates = []
        enrollment_counts = []
        course_completion_rates = []
        
        for course in courses[:10]:  # Limiter à 10 cours pour le graphique
            total_lessons = course.total_lessons or 1  # Éviter la division par zéro
            completed_lessons = getattr(course, 'completed_lessons_count', 0)
            rate = (completed_lessons / total_lessons) * 100 if total_lessons > 0 else 0
            
            # Calculer le taux de complétion des cours (nombre de cours complétés / nombre d'inscriptions)
            total_enrollments = course.total_enrollments or 1
            completed_courses = getattr(course, 'completed_courses_count', 0)
            course_completion_rate = (completed_courses / total_enrollments) * 100
            
            completion_rates.append(round(rate, 1))
            course_completion_rates.append(round(course_completion_rate, 1))
            enrollment_counts.append(course.total_enrollments)
        
        # Préparer les données pour le tableau
        courses_data = []
        for course in courses:
            total_lessons = course.total_lessons or 1
            completed_lessons = getattr(course, 'completed_lessons_count', 0)
            lesson_completion_rate = (completed_lessons / total_lessons) * 100 if total_lessons > 0 else 0
            
            # Calculer le taux de complétion du cours (nombre de cours complétés / nombre d'inscriptions)
            total_enrollments = course.total_enrollments or 1
            completed_courses = getattr(course, 'completed_courses_count', 0)
            course_completion_rate = (completed_courses / total_enrollments) * 100
            
            # Calculer la différence entre le taux de complétion des leçons et des cours
            lesson_only_completion = max(0, lesson_completion_rate - course_completion_rate)
            
            courses_data.append({
                'id': course.id,
                'title': course.title,
                'instructor': course.created_by,
                'category': course.category,
                'thumbnail': course.thumbnail,
                'is_published': getattr(course, 'is_published', False),
                'enrollments': course.total_enrollments,
                'completed_lessons': completed_lessons,
                'completed_courses': completed_courses,
                'total_lessons': total_lessons,
                'lesson_completion_rate': round(lesson_completion_rate, 1),
                'course_completion_rate': round(course_completion_rate, 1),
                'lesson_only_completion': round(lesson_only_completion, 1),
                'average_rating': round(course.average_rating, 1) if course.average_rating else 0.0,
                'created_at': course.created_at,
                'updated_at': getattr(course, 'updated_at', course.created_at),
            })
        
        # Trier les cours par taux de complétion des cours pour le top 5
        top_courses = sorted(courses_data, key=lambda x: x['course_completion_rate'], reverse=True)[:5]
        
        # Pagination
        page = self.request.GET.get('page', 1)
        paginator = Paginator(courses_data, self.paginate_by)
        
        try:
            courses_page = paginator.page(page)
        except PageNotAnInteger:
            courses_page = paginator.page(1)
        except EmptyPage:
            courses_page = paginator.page(paginator.num_pages)
        
        # Convertir les listes en JSON pour le JavaScript
        import json
        
        context.update({
            'courses': courses_page,
            'top_courses': top_courses,
            'page_obj': courses_page,
            'paginator': paginator,
            'is_paginated': courses_page.has_other_pages(),
            'course_titles': json.dumps([str(title) for title in course_titles]),
            'completion_rates': completion_rates,  # Taux de complétion des leçons
            'course_completion_rates': course_completion_rates,  # Taux de complétion des cours
            'enrollment_counts': enrollment_counts,
            'title': 'Progression des cours',
        })
        
        return context

# Vues basées sur des fonctions pour la rétrocompatibilité
@login_required
@user_passes_test(is_trainer_or_admin)
def learner_tracking(request):
    view = LearnerTrackingView.as_view()
    return view(request)

@login_required
@user_passes_test(is_trainer_or_admin)
def course_progress(request):
    view = CourseProgressView.as_view()
    return view(request)

@login_required
@user_passes_test(is_trainer_or_admin)
def learner_detail(request, learner_id):
    """
    Vue détaillée pour un apprenant spécifique
    """
    learner = get_object_or_404(CustomUser, id=learner_id, role='learner')
    
    # Récupérer les progressions de l'apprenant
    learner_progress = LearnerProgress.objects.filter(user=learner).select_related('course')
    
    # Récupérer les cours complétés via CourseCompletion
    from courses.models import CourseCompletion
    completed_course_ids = set(CourseCompletion.objects.filter(
        user=learner
    ).values_list('course_id', flat=True))
    
    # Créer une liste des inscriptions avec les données de progression
    enrollments = []
    for enrollment in Enrollment.objects.filter(user=learner).select_related('course'):
        progress = learner_progress.filter(course=enrollment.course).first()
        
        # Utiliser CourseCompletion pour déterminer si le cours est complété
        is_course_completed = enrollment.course.id in completed_course_ids
        
        # Mettre à jour l'objet enrollment avec les données de progression
        enrollment.progress = progress.completion_percentage if progress else 0.0
        enrollment.last_accessed = progress.last_accessed if progress else None
        enrollment.completed = is_course_completed
        
        # Si le cours est marqué comme complété mais que la progression est < 100%,
        # forcer la progression à 100%
        if is_course_completed and enrollment.progress < 100:
            enrollment.progress = 100.0
        
        enrollments.append(enrollment)
    
    # Calculer les statistiques
    total_courses = len(enrollments)
    completed_courses = len(completed_course_ids)
    completion_rate = (completed_courses / total_courses * 100) if total_courses > 0 else 0
    
    # Récupérer les activités récentes
    from courses.models import LessonProgress
    recent_activities = LessonProgress.objects.filter(
        user=learner
    ).select_related(
        'lesson', 'lesson__module', 'lesson__module__course'
    ).order_by('-completed_at' if 'completed_at' in [f.name for f in LessonProgress._meta.fields] else '-last_accessed')[:10]
    
    # Calculer le temps total passé sur la plateforme
    total_time_spent = timedelta()
    
    # Récupérer les certifications de l'apprenant
    from certifications.models import Certification
    certifications = Certification.objects.filter(user=learner).select_related('course').order_by('-issued_at')
    
    context = {
        'title': f'Détails de {learner.get_full_name() or learner.username}',
        'learner': learner,
        'enrollments': enrollments,
        'certifications': certifications,
        'total_courses': total_courses,
        'completed_courses': completed_courses,
        'completion_rate': round(completion_rate, 1),
        'recent_activities': recent_activities,
        'total_time_spent': total_time_spent,
    }
    
    return render(request, 'tracking/learner_detail.html', context)

@login_required
@user_passes_test(is_trainer_or_admin)
def course_detail(request, course_id):
    """Vue détaillée pour un cours spécifique"""
    from courses.models import CourseCompletion, LessonProgress
    
    course = get_object_or_404(Course, id=course_id)
    
    # Vérifier que l'utilisateur a le droit de voir ce cours
    if not request.user.is_superuser and course.instructor != request.user:
        return redirect('tracking:course_progress')
    
    # Récupérer les inscriptions avec progression
    enrollments = Enrollment.objects.filter(course=course).select_related('user')
    
    # Récupérer les utilisateurs ayant complété le cours via CourseCompletion
    completed_user_ids = set(CourseCompletion.objects.filter(
        course=course
    ).values_list('user_id', flat=True))
    
    # Mettre à jour les inscriptions avec l'état de complétion
    for enrollment in enrollments:
        enrollment.completed = enrollment.user_id in completed_user_ids
    
    # Calculer les statistiques du cours
    total_learners = enrollments.count()
    completed_learners = len(completed_user_ids)
    completion_rate = (completed_learners / total_learners * 100) if total_learners > 0 else 0
    
    # Récupérer les modules et leçons avec progression
    modules = course.modules.all().prefetch_related('lessons')
    
    # Récupérer les statistiques de progression des leçons
    lesson_stats = {}
    for module in modules:
        for lesson in module.lessons.all():
            completed_count = LessonProgress.objects.filter(
                lesson=lesson,
                is_completed=True
            ).count()
            
            lesson_stats[lesson.id] = {
                'completed': completed_count,
                'completion_rate': (completed_count / total_learners * 100) if total_learners > 0 else 0
            }
    
    # Préparer les données pour le graphique de progression
    completion_data = []
    for module in modules:
        module_completion = enrollments.filter(progress__lesson__module=module).aggregate(
            avg_completion=Avg('progress__completion')
        )
        completion_data.append({
            'module': module,
            'completion': module_completion['avg_completion'] or 0
        })
    
    context = {
        'course': course,
        'modules': modules,
        'total_learners': total_learners,
        'completed_learners': completed_learners,
        'completion_rate': round(completion_rate, 1),
        'completion_data': completion_data,
        'title': f'Statistiques - {course.title}',
    }
    
    return render(request, 'tracking/course_detail.html', context)


# ==========================================
# VUES POUR LES RAPPELS DE COURS INACHEVÉS
# ==========================================

def get_course_reminders(request):
    """
    API pour récupérer les rappels de cours inachevés
    Calcule la progression en temps réel basée sur les inscriptions et leçons complétées
    """
    if request.method == 'GET':
        # Vérification explicite de l'authentification
        if not request.user.is_authenticated:
            print("🔍 DEBUG: Utilisateur non authentifié!")
            return JsonResponse({
                'error': 'Utilisateur non authentifié',
                'reminders': [],
                'total_count': 0,
                'debug_user': 'anonymous'
            }, status=401)
        
        user = request.user
        
        # DÉBOGAGE: Afficher l'utilisateur connecté
        print(f"🔍 DEBUG: Utilisateur connecté = {user.username} (ID: {user.id})")
        print(f"🔍 DEBUG: is_authenticated = {user.is_authenticated}")
        print(f"🔍 DEBUG: Session user_id = {request.session.get('_auth_user_id')}")
        
        try:
            # Importer les modèles nécessaires
            from courses.models import Enrollment, LessonProgress
            from courses.models import CourseCompletion
            
            print(f"🔍 DEBUG: Début vérification pour {user.username}")
            
            # Récupérer tous les cours où l'utilisateur est inscrit
            enrollments = Enrollment.objects.filter(user=user).select_related('course')
            print(f"🔍 DEBUG: Inscriptions trouvées pour {user.username}: {enrollments.count()}")
            
            # Récupérer les IDs des cours complétés
            completed_course_ids = set(CourseCompletion.objects.filter(
                user=user
            ).values_list('course_id', flat=True))
            print(f"🔍 DEBUG: Cours complétés par {user.username}: {len(completed_course_ids)}")
            
            # Calculer la progression réelle pour chaque inscription
            active_reminders = []
            for enrollment in enrollments:
                course = enrollment.course
                course_id = course.id
                
                # Ignorer les cours complétés
                if course_id in completed_course_ids:
                    print(f"🔍 DEBUG: Cours {course.title} déjà complété - ignoré")
                    continue
                
                # Calculer la progression réelle basée sur les leçons complétées
                total_lessons = course.get_total_lessons()
                if total_lessons == 0:
                    print(f"🔍 DEBUG: Cours {course.title} n'a pas de leçons - ignoré")
                    continue
                
                # Compter les leçons complétées via LessonProgress
                completed_lessons_count = LessonProgress.objects.filter(
                    user=user,
                    lesson__module__course=course,
                    is_completed=True
                ).count()
                
                # Calculer le pourcentage réel
                real_progress = (completed_lessons_count / total_lessons) * 100
                
                print(f"🔍 DEBUG: {course.title} - {completed_lessons_count}/{total_lessons} leçons = {real_progress:.1f}%")
                
                # N'inclure que les cours avec une progression entre 0% et 100%
                # Mais aussi inclure les cours avec 0% s'il y a au moins une activité
                has_activity = LessonProgress.objects.filter(
                    user=user,
                    lesson__module__course=course
                ).exists()
                
                if (0 < real_progress < 100) or (real_progress == 0 and has_activity):
                    # Récupérer la dernière activité via LessonProgress
                    last_lesson_progress = LessonProgress.objects.filter(
                        user=user,
                        lesson__module__course=course
                    ).order_by('-completed_at').first()
                    
                    last_activity = last_lesson_progress.completed_at if last_lesson_progress else enrollment.enrolled_at
                    
                    reminder_data = {
                        'id': 0,  # ID temporaire
                        'course_id': course.id,
                        'course_title': course.title,
                        'course_thumbnail': course.thumbnail.url if course.thumbnail else None,
                        'progress_percentage': round(real_progress, 1),
                        'last_activity': last_activity.isoformat() if last_activity else None,
                        'next_lesson': None,
                        'days_inactive': 0,
                    }
                    active_reminders.append(reminder_data)
                    print(f"🔍 DEBUG: Rappel créé pour {course.title} - {real_progress:.1f}%")
            
            # Trier par progression décroissante (montrer d'abord les cours les plus avancés)
            active_reminders.sort(key=lambda x: x['progress_percentage'], reverse=True)
            
            print(f"🔍 DEBUG: Total rappels créés pour {user.username}: {len(active_reminders)}")
            
            return JsonResponse({
                'reminders': active_reminders,
                'total_count': len(active_reminders),
                'debug_user': user.username,
                'debug_user_id': user.id,
                'debug_note': f'Basé sur {len(active_reminders)} cours en progression pour {user.username}'
            })
            
        except Exception as e:
            import traceback
            print(f"🔍 DEBUG: Erreur: {str(e)}")
            print(f"🔍 DEBUG: Traceback: {traceback.format_exc()}")
            return JsonResponse({
                'error': f'Erreur serveur: {str(e)}',
                'reminders': [],
                'total_count': 0
            }, status=500)
    
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


@login_required
def dismiss_course_reminder(request, reminder_id):
    """
    API pour masquer un rappel spécifique
    """
    if request.method == 'POST':
        try:
            reminder = CourseReminder.objects.get(
                id=reminder_id,
                user=request.user
            )
            reminder.is_active = False
            reminder.reminder_count += 1
            reminder.last_reminder_sent = timezone.now()
            reminder.save()
            
            return JsonResponse({'success': True})
        except CourseReminder.DoesNotExist:
            return JsonResponse({'error': 'Rappel non trouvé'}, status=404)
    
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


@login_required
def update_course_progress(request):
    """
    API pour mettre à jour la progression et créer/mettre à jour les rappels
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            course_id = data.get('course_id')
            lesson_id = data.get('lesson_id')
            progress_percentage = data.get('progress_percentage', 0)
            
            course = get_object_or_404(Course, id=course_id)
            lesson = get_object_or_404(Lesson, id=lesson_id) if lesson_id else None
            
            # Mettre à jour ou créer le rappel
            reminder = CourseReminder.update_or_create_reminder(
                user=request.user,
                course=course,
                lesson=lesson
            )
            
            # Logger l'activité
            ActivityLog.objects.create(
                user=request.user,
                action='view_lesson',
                course=course,
                lesson=lesson
            )
            
            return JsonResponse({
                'success': True,
                'reminder_id': reminder.id,
                'progress_percentage': reminder.progress_percentage
            })
            
        except (json.JSONDecodeError, KeyError):
            return JsonResponse({'error': 'Données invalides'}, status=400)
    
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


@login_required
def get_user_progress_summary(request):
    """
    API pour obtenir un résumé de progression pour le profil utilisateur
    """
    if request.method == 'GET':
        user = request.user
        
        # Récupérer tous les cours avec progression
        learner_progress = LearnerProgress.objects.filter(
            user=user
        ).select_related('course').order_by('-last_accessed')
        
        progress_summary = []
        incomplete_courses = []
        
        for progress in learner_progress:
            course_data = {
                'course_id': progress.course.id,
                'course_title': progress.course.title,
                'course_thumbnail': progress.course.thumbnail.url if progress.course.thumbnail else None,
                'progress_percentage': progress.completion_percentage,
                'last_accessed': progress.last_accessed,
                'is_completed': progress.is_completed,
                'completed_lessons': progress.completed_lessons.count(),
                'total_lessons': progress.course.get_total_lessons(),
            }
            
            progress_summary.append(course_data)
            
            # Ajouter aux cours inachevés si < 100%
            if progress.completion_percentage < 100:
                # Calculer jours d'inactivité
                days_inactive = (timezone.now() - progress.last_accessed).days
                if days_inactive >= 3:  # Seuils de 3 jours
                    incomplete_courses.append({
                        **course_data,
                        'days_inactive': days_inactive,
                        'needs_reminder': True
                    })
        
        return JsonResponse({
            'progress_summary': progress_summary,
            'incomplete_courses': incomplete_courses,
            'total_courses': len(progress_summary),
            'completed_courses': len([p for p in progress_summary if p['is_completed']]),
            'incomplete_count': len(incomplete_courses)
        })
    
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
