from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Q
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import CustomUser
from subscriptions.models import Subscription
from .forms import CustomUserCreationForm
from courses.models import Course, Category  # 
from .forms import ProfileForm
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash

def instructor_public(request, username: str):
    trainer = get_object_or_404(CustomUser, username=username)
    # Vérifier si l'utilisateur est un formateur ou un administrateur
    if getattr(trainer, 'role', None) not in ['trainer', 'admin'] and not trainer.is_superuser:
        # Rediriger vers le profil public si l'utilisateur n'est pas un formateur
        return redirect('users:profile')
    
    # Le reste du code s'exécute pour les formateurs et les administrateurs
    
    # Vérifier si l'utilisateur actuel est abonné à ce formateur
    is_subscribed = False
    if request.user.is_authenticated and request.user != trainer:
        is_subscribed = Subscription.objects.filter(
            subscriber=request.user,
            trainer=trainer,
            is_active=True
        ).exists()
    
    # Compter le nombre d'abonnés
    subscribers_count = trainer.subscribers.filter(is_active=True).count()
    
    courses = Course.objects.filter(created_by=trainer).select_related('category').order_by('-created_at')
    teacher_courses = Course.objects.filter(created_by=trainer).order_by('title')
    categories = Category.objects.all().order_by('name')
    
    # Récupérer toutes les vidéos des cours du formateur
    from courses.models import LessonVideo
    videos = []
    for course in courses:
        course_videos = LessonVideo.objects.filter(
            lesson__module__course=course
        ).select_related('lesson__module').order_by('lesson__module__order', 'lesson__order', 'order')
        
        for video in course_videos:
            videos.append({
                'id': video.id,
                'title': video.title or video.lesson.title,
                'description': video.lesson.description or '',
                'thumbnail_url': video.lesson.thumbnail.url if video.lesson.thumbnail else (
                    course.thumbnail.url if course.thumbnail else None
                ),
                'course_title': course.title,
                'course_id': course.id,
                'duration': video.duration,
                'created_at': getattr(video.lesson, 'created_at', timezone.now()),
                'lesson_id': video.lesson.id
            })
    
    upcoming_sessions = []
    try:
        from classrooms.models import LiveSession
        upcoming_sessions = list(
            LiveSession.objects.filter(classroom__created_by=trainer, start_at__gte=timezone.now())
            .select_related('classroom')
            .order_by('start_at')[:6]
        )
    except Exception:
        upcoming_sessions = []
    
    stats = {
        'courses': courses.count(),
    }
    
    # Vérifier si l'utilisateur vient d'une recherche
    from_search = request.GET.get('from_search') == 'true'
    
    # Récupérer le nombre de messages non lus si l'utilisateur est connecté
    unread_count = 0
    if request.user.is_authenticated and request.user == trainer:
        try:
            from chat.models_simple import DirectMessage
            unread_count = DirectMessage.objects.filter(
                conversation__participant2=request.user,
                conversation__participant1__ne=request.user,
                read_by__user=request.user
            ).count()
        except Exception:
            pass
    
    return render(request, 'users/instructor_public.html', {
        'trainer': trainer,
        'courses': courses,
        'teacher_courses': teacher_courses,
        'upcoming_sessions': upcoming_sessions,
        'stats': stats,
        'categories': categories,
        'is_subscribed': is_subscribed,
        'subscribers_count': subscribers_count,
        'from_search': from_search,
        'unread_count': unread_count,
        'videos': videos,
    })

@login_required
def learner_public(request, username: str):
    learner = get_object_or_404(CustomUser, username=username)
    # Ensure the handle matches the logged-in learner
    if request.user.id != learner.id and not request.user.is_superuser:
        return redirect('users:dashboard')
    user = learner
    categories = Category.objects.all()
    category_slug = request.GET.get('category')
    if category_slug:
        courses = Course.objects.filter(category__slug=category_slug)
    else:
        courses = Course.objects.all()
    context = {
        'user': user,
        'courses': courses,
        'categories': categories,
        'selected_category': category_slug,
    }
    return render(request, 'users/dashboard.html', context)

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        next_url = request.POST.get('next', '')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            
            # Enregistrer l'activité de connexion
            if hasattr(request, '_activity_tracking_middleware'):
                request._activity_tracking_middleware.log_activity(
                    user=user,
                    action='login',
                    request=request
                )
            
            # Vérifier s'il y a une URL de redirection valide
            if next_url and next_url != 'None' and not next_url.startswith('/admin/'):
                return redirect(next_url)
                
            # Redirection selon le rôle de l'utilisateur
            if user.is_superuser or user.role == 'admin':
                # Rediriger les administrateurs vers le dashboard admin personnalisé
                return redirect('users:admin_dashboard')
            elif user.role == 'trainer':
                # Rediriger les formateurs vers leur page publique
                return redirect('handle_profile', username=user.username)
            else:
                # Pour les autres rôles, rediriger vers le profil
                return redirect('users:profile')
        else:
            messages.error(request, "Identifiants invalides.")
    
    # Afficher le formulaire de connexion
    next_url = request.GET.get('next', '')
    return render(request, 'users/login.html', {'next': next_url})

@login_required
def user_logout(request):
    # Enregistrer l'activité de déconnexion avant de déconnecter l'utilisateur
    if hasattr(request, '_activity_tracking_middleware'):
        request._activity_tracking_middleware.log_activity(
            user=request.user,
            action='logout',
            request=request
        )
    
    # Déconnecter l'utilisateur
    logout(request)
    # Rediriger tout le monde vers le dashboard public après déconnexion
    return redirect('users:dashboard')

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                user = form.save(commit=False)
                # S'assurer que les champs optionnels sont correctement définis
                if not hasattr(user, 'fonction'):
                    user.fonction = None
                user.save()
                messages.success(request, "Compte créé avec succès, vous pouvez maintenant vous connecter.")
                return redirect('users:login')
            except Exception as e:
                messages.error(request, f"Une erreur est survenue lors de la création du compte : {str(e)}")
        else:
            # Afficher les erreurs de validation
            for field, errors in form.errors.items():
                field_label = field
                try:
                    field_label = form.fields[field].label or field
                except KeyError:
                    pass
                for error in errors:
                    messages.error(request, f"{field_label}: {error}")
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'users/register.html', {'form': form})

# @login_required
# def dashboard(request):
    user = request.user

    # Récupérer toutes les catégories pour les filtres
    categories = Category.objects.all()

    # Récupérer le slug de catégorie depuis la query string (ex: ?category=python)
    category_slug = request.GET.get('category')

    # Récupérer tous les cours ou filtrer par catégorie si spécifiée
    if category_slug:
        courses = Course.objects.filter(category__slug=category_slug)
    else:
        courses = Course.objects.all()

    context = {
        'user': user,
        'courses': courses,
        'categories': categories,
        'selected_category': category_slug,
    }

    # Logique spécifique selon le rôle (facultative ici)
    if user.role == 'trainer':
        context['trainer_view'] = True
    elif user.role == 'learner':
        context['learner_view'] = True
    elif user.is_superuser or user.role == 'admin':
        context['admin_view'] = True

    return render(request, 'users/dashboard.html', context)

def dashboard(request):
    user = request.user
    categories = Category.objects.all()
    category_slug = request.GET.get('category')

    # Récupérer les cours en fonction de la catégorie sélectionnée
    if category_slug:
        courses = Course.objects.filter(category__slug=category_slug)
    else:
        courses = Course.objects.all()

    # Initialiser les statistiques
    completed_courses = 0
    enrolled_courses = 0
    total_lessons = 0
    certificates_count = 0
    learning_hours = 0
    progress_percentage = 0
    is_first_connection = True
    
    # Initialiser les variables de dernière activité pour tous les utilisateurs
    last_course = None
    last_lesson = None
    last_activity_date = None

    # Récupérer les vraies statistiques (seulement si connecté)
    if user.is_authenticated:
        # Vérifier si c'est la première connexion
        from django.utils import timezone
        is_first_connection = (
            user.last_login is None or 
            (user.last_login and user.date_joined and 
             (user.last_login - user.date_joined).total_seconds() < 300)  # 5 minutes
        )

        # Importer les modèles nécessaires
        from courses.models import LessonProgress, Enrollment, CourseCompletion, LearningPath
        
        # Cours terminés
        completed_courses = CourseCompletion.objects.filter(
            user=user
        ).count()

        # Cours inscrits
        enrolled_courses = Enrollment.objects.filter(
            user=user
        ).count()

        # Leçons suivies
        total_lessons = LessonProgress.objects.filter(
            user=user
        ).count()

        # Certificats (uniquement les vrais certificats obtenus après évaluation)
        from certifications.models import Certification
        certificates_count = Certification.objects.filter(
            user=user,
            is_valid=True
        ).count()

        # Temps d'apprentissage (depuis LearningPath)
        try:
            learning_path = user.learning_path
            learning_hours = learning_path.time_spent.total_seconds() / 3600 if learning_path.time_spent else 0
            learning_hours = round(learning_hours, 1)
            
            # Récupérer le dernier cours/leçon suivi (plusieurs méthodes)
            last_progress = LessonProgress.objects.filter(
                user=user
            ).order_by('-updated_at').first()
            
            if last_progress:
                last_lesson = last_progress.lesson
                last_course = last_lesson.module.course
                last_activity_date = last_progress.updated_at
            else:
                # Si pas de progression, vérifier le cours actuel dans LearningPath
                if learning_path.current_course:
                    last_course = learning_path.current_course
                    # Prendre la première leçon du cours
                    first_module = last_course.modules.first()
                    if first_module:
                        first_lesson = first_module.lessons.first()
                        if first_lesson:
                            last_lesson = first_lesson
                            last_activity_date = learning_path.last_activity
                
            # Progression basée sur les cours complétés vs inscrits
            if enrolled_courses > 0:
                progress_percentage = round((completed_courses / enrolled_courses) * 100, 1)
        except Exception as e:
            # En cas d'erreur, essayer de récupérer au moins le cours actuel
            try:
                learning_path = user.learning_path
                if learning_path.current_course:
                    last_course = learning_path.current_course
                    last_activity_date = learning_path.last_activity
            except:
                pass

    # Récupérer les leçons terminées par l'utilisateur (seulement si connecté)
    from courses.models import LessonProgress
    completed_lessons = []
    if user.is_authenticated:
        completed_lessons = LessonProgress.objects.filter(
            user=user,
            is_completed=True
        ).values_list('lesson_id', flat=True)

    # Récupérer les notifications non lues (seulement si connecté)
    from notifications.models import Notification
    unread_notifications = []
    if user.is_authenticated:
        unread_notifications = Notification.objects.filter(
            user=user,
            is_read=False
        ).order_by('-created_at')[:5]  # 5 dernières notifications non lues

    context = {
        'user': user,
        'courses': courses,
        'categories': categories,
        'selected_category': category_slug,
        'completed_lessons': list(completed_lessons),  # Convertir en liste pour le template
        'unread_notifications': unread_notifications,
        # Statistiques réelles
        'completed_courses': completed_courses,
        'enrolled_courses': enrolled_courses,
        'total_lessons': total_lessons,
        'certificates_count': certificates_count,
        'learning_hours': learning_hours,
        'progress_percentage': progress_percentage,
        'is_first_connection': is_first_connection,
        'last_course': last_course,
        'last_lesson': last_lesson,
        'last_activity_date': last_activity_date,
    }

    # Logique spécifique selon le rôle (seulement si connecté)
    if user.is_authenticated:
        if user.role == 'trainer':
            context['trainer_view'] = True
        elif user.role == 'learner':
            context['learner_view'] = True
        elif user.is_superuser or user.role == 'admin':
            context['admin_view'] = True

    return render(request, 'users/dashboard.html', context)
    
@login_required
def instructor_dashboard(request):
    return redirect('handle_profile', username=request.user.username)

@login_required
def learner_dashboard(request):
    context = {'user': request.user, 'message': "Bienvenue sur votre dashboard apprenant !"}
    return render(request, 'users/learner_dashboard.html', context)

@login_required
def learner_dashboard_handle(request, username: str):
    learner = get_object_or_404(CustomUser, username=username)
    if request.user.id != learner.id and not request.user.is_superuser:
        return redirect('users:dashboard')
    # Reuse dashboard content logic
    categories = Category.objects.all()
    category_slug = request.GET.get('category')
    if category_slug:
        courses = Course.objects.filter(category__slug=category_slug)
    else:
        courses = Course.objects.all()
    context = {
        'user': learner,
        'courses': courses,
        'categories': categories,
        'selected_category': category_slug,
    }
    return render(request, 'users/dashboard.html', context)

@login_required
def my_profile(request):
    user = request.user
    
    # Courses created (if trainer)
    created_courses = Course.objects.filter(created_by=user)
    
    # Enrollments and courses liked/rated
    try:
        from courses.models import Enrollment, CourseLike, CourseRating, LessonProgress, Lesson
        enrollments = Enrollment.objects.filter(user=user).select_related('course')
        likes = CourseLike.objects.filter(user=user).select_related('course')
        ratings = CourseRating.objects.filter(user=user).select_related('course')
        
        # Récupérer les IDs des cours auxquels l'utilisateur est inscrit
        enrolled_course_ids = list(enrollments.values_list('course_id', flat=True))
        
        # Récupérer les leçons terminées (5 plus récentes) uniquement pour les cours auxquels l'utilisateur est inscrit
        recent_completed_lessons = LessonProgress.objects.filter(
            user=user,
            is_completed=True,
            lesson__module__course_id__in=enrolled_course_ids
        ).select_related('lesson', 'lesson__module').order_by('-completed_at')[:5]
        
        # Récupérer les IDs des cours auxquels l'utilisateur est inscrit
        enrolled_course_ids = enrollments.values_list('course_id', flat=True)
        
        # Calculer les totaux uniquement pour les cours auxquels l'utilisateur est inscrit
        completed_lessons_count = LessonProgress.objects.filter(
            user=user,
            is_completed=True,
            lesson__module__course_id__in=enrolled_course_ids
        ).count()
        
        # Compter uniquement les leçons des cours auxquels l'utilisateur est inscrit
        total_lessons = Lesson.objects.filter(
            is_active=True,
            module__course_id__in=enrolled_course_ids
        ).count()
        
        progress_percentage = int((completed_lessons_count / total_lessons * 100)) if total_lessons > 0 else 0
        
    except Exception as e:
        print(f"[ERROR] Erreur lors de la récupération des données de progression: {str(e)}")
        enrollments, likes, ratings = [], [], []
        recent_completed_lessons = []
        completed_lessons_count = 0
        total_lessons = 0
        progress_percentage = 0
    
    # Classrooms memberships
    try:
        from classrooms.models import ClassroomMembership
        classroom_memberships = ClassroomMembership.objects.filter(user=user).select_related('classroom')
    except Exception as e:
        print(f"[ERROR] Erreur lors de la récupération des salles de classe: {str(e)}")
        classroom_memberships = []
    
    # Certifications
    try:
        from certifications.models import Certification
        certifications = Certification.objects.filter(
            user=user,
            is_valid=True
        ).select_related('course').order_by('-issued_at')
    except Exception as e:
        print(f"[ERROR] Erreur lors de la récupération des certifications: {str(e)}")
        certifications = []
    
    # Nombre de messages non lus
    try:
        from chat.models_simple import DirectMessage
        unread_count = DirectMessage.objects.filter(
            conversation__participant2=user,
            conversation__participant1__ne=user,
            read_by__user=user
        ).count()
    except Exception as e:
        print(f"[ERROR] Erreur lors de la récupération des messages: {str(e)}")
        unread_count = 0

    # Quiz results - uniquement pour les cours auxquels l'utilisateur est inscrit
    try:
        from courses.models import QuizAttempt, Quiz
        # Récupérer les IDs des cours auxquels l'utilisateur est inscrit
        enrolled_course_ids = enrollments.values_list('course_id', flat=True)
        
        # Récupérer les quiz de ces cours via les leçons et modules
        quiz_results = QuizAttempt.objects.filter(
            user=user,
            quiz__lesson__module__course_id__in=enrolled_course_ids
        ).select_related(
            'quiz',
            'quiz__lesson',
            'quiz__lesson__module',
            'quiz__lesson__module__course'
        ).order_by('-completed_at')
    except Exception as e:
        print(f"[ERROR] Erreur lors de la récupération des quiz: {str(e)}")
        quiz_results = []

    context = {
        'me': user,
        'created_courses': created_courses,
        'enrollments': enrollments,
        'likes': likes,
        'ratings': ratings,
        'classroom_memberships': classroom_memberships,
        'certifications': certifications,
        'unread_count': unread_count,
        'is_own_profile': True,
        'progress_percentage': progress_percentage,
        'recent_completed_lessons': recent_completed_lessons,
        'completed_lessons_count': completed_lessons_count,
        'total_lessons': total_lessons,
        'quiz_results': quiz_results,
    }
    return render(request, 'users/profile.html', context)

@login_required
def edit_profile(request):
    user = request.user
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profil mis à jour.")
            return redirect('users:profile')
    else:
        form = ProfileForm(instance=user)
    return render(request, 'users/profile_edit.html', {'form': form})

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Mot de passe modifié.")
            return redirect('users:profile')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'users/password_change.html', {'form': form})

@login_required
def upload_avatar(request):
    if request.method == 'POST' and request.FILES.get('avatar'):
        try:
            request.user.avatar = request.FILES['avatar']
            request.user.save(update_fields=['avatar'])
            response_data = {
                'success': True,
                'message': 'Photo de profil mise à jour avec succès.',
                'avatar_url': request.user.avatar.url if request.user.avatar else None
            }
            response = JsonResponse(response_data)
            response['Content-Type'] = 'application/json'
            return response
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erreur lors du téléchargement de la photo de profil: {str(e)}'
            }, status=400)
    return JsonResponse({
        'success': False,
        'message': 'Aucun fichier fourni.'
    }, status=400)

@login_required
def upload_cover(request):
    if request.method == 'POST' and request.FILES.get('cover'):
        try:
            request.user.cover = request.FILES['cover']
            request.user.save(update_fields=['cover'])
            response_data = {
                'success': True,
                'message': 'Image de couverture mise à jour avec succès.',
                'cover_url': request.user.cover.url if request.user.cover else None
            }
            response = JsonResponse(response_data)
            response['Content-Type'] = 'application/json'
            return response
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erreur lors du téléchargement de l\'image de couverture: {str(e)}'
            }, status=400)
    return JsonResponse({
        'success': False,
        'message': 'Aucun fichier fourni.'
    }, status=400)

def search_trainers(request):
    """
    Vue pour rechercher des formateurs par nom d'utilisateur ou nom complet
    """
    query = request.GET.get('q', '').strip()
    
    if not query or len(query) < 2:
        return JsonResponse({'trainers': []})
    
    # Recherche des formateurs correspondant à la requête
    trainers = CustomUser.objects.filter(
        Q(role='trainer') | Q(is_superuser=True),
        Q(username__icontains=query) | 
        Q(first_name__icontains=query) | 
        Q(last_name__icontains=query)
    ).distinct()
    
    # Préparation des données des formateurs
    results = []
    current_user = request.user if request.user.is_authenticated else None
    
    for trainer in trainers:
        # Vérifier si l'utilisateur actuel est abonné à ce formateur
        is_subscribed = False
        if current_user and current_user.is_authenticated and current_user != trainer:
            is_subscribed = Subscription.objects.filter(
                subscriber=current_user,
                trainer=trainer,
                is_active=True
            ).exists()
        
        # Compter le nombre d'abonnés et de cours
        subscribers_count = trainer.subscribers.filter(is_active=True).count()
        courses_count = Course.objects.filter(created_by=trainer).count()
        
        results.append({
            'id': trainer.id,
            'username': trainer.username,
            'full_name': trainer.get_full_name(),
            'avatar': trainer.avatar.url if trainer.avatar else None,
            'is_subscribed': is_subscribed,
            'subscribers_count': subscribers_count,
            'courses_count': courses_count
        })
    
    return JsonResponse({'trainers': results})

# Les vues de gestion des abonnements ont été déplacées vers l'application 'subscriptions'

import logging
logger = logging.getLogger(__name__)

import psutil
import platform
from datetime import datetime

from django.views.decorators.cache import never_cache

@never_cache
@login_required
@user_passes_test(lambda u: u.is_staff)
@require_http_methods(["GET"])
def activity_logs_api(request):
    """
    API pour récupérer les logs d'activité récents.
    """
    try:
        from tracking.models import ActivityLog
        from django.utils import timezone
        
        last_id = request.GET.get('last_id', 0)
        
        # Récupérer les logs récents (connexions/déconnexions)
        logs = ActivityLog.objects.filter(
            action__in=['login', 'logout']
        ).select_related('user').order_by('-timestamp')
        
        # Filtrer par ID si spécifié
        if last_id and last_id.isdigit():
            logs = logs.filter(id__gt=int(last_id))
        
        # Si pas de last_id, on prend les 20 derniers logs
        if not last_id or not last_id.isdigit():
            logs = logs[:20]
        
        # Préparer les données pour la réponse JSON
        logs_data = []
        for log in logs:
            try:
                logs_data.append({
                    'id': log.id,
                    'action': log.action,
                    'action_display': log.get_action_display(),
                    'timestamp': log.timestamp.isoformat(),
                    'time_ago': timezone.now() - log.timestamp,
                    'ip_address': log.ip_address or '',
                    'user_agent': log.user_agent or '',
                    'user': {
                        'id': log.user.id,
                        'username': log.user.username,
                        'email': log.user.email,
                        'first_name': log.user.first_name or '',
                        'last_name': log.user.last_name or '',
                        'avatar': log.user.avatar.url if hasattr(log.user, 'avatar') and log.user.avatar else None,
                    }
                })
            except Exception as user_error:
                logger.error(f"Error processing log {log.id}: {str(user_error)}")
                continue
    
        logger.info(f"Returning {len(logs_data)} logs")
        return JsonResponse({
            'status': 'success',
            'logs': logs_data,
            'debug': {
                'total_logs': logs.count(),
                'returned_logs': len(logs_data)
            }
        })
    
    except Exception as e:
        logger.error(f"Error in activity_logs_api: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


# Vues pour la gestion des préférences utilisateur
@login_required
@require_http_methods(["GET", "POST"])
def user_preferences(request):
    """
    Vue pour afficher et modifier les préférences utilisateur
    """
    from .models import UserPreference
    
    preferences, created = UserPreference.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Mettre à jour les préférences
        preferences.theme = request.POST.get('theme', preferences.theme)
        preferences.language = request.POST.get('language', preferences.language)
        preferences.email_notifications = request.POST.get('email_notifications') == 'on'
        preferences.push_notifications = request.POST.get('push_notifications') == 'on'
        preferences.auto_play_video = request.POST.get('auto_play_video') == 'on'
        preferences.show_progress = request.POST.get('show_progress') == 'on'
        preferences.download_for_offline = request.POST.get('download_for_offline') == 'on'
        
        preferences.save()
        
        # Mettre à jour les préférences dans la requête et le cookie
        request.user_preferences.update(preferences.to_cookie_data())
        request._update_preferences = True
        
        messages.success(request, 'Vos préférences ont été mises à jour avec succès.')
        return redirect('users:preferences')
    
    return render(request, 'users/preferences.html', {
        'preferences': preferences,
        'user_preferences': request.user_preferences
    })


@login_required
@require_POST
def toggle_favorite_module(request):
    """
    Vue pour ajouter/retirer un module des favoris (AJAX)
    """
    from .models import UserPreference
    from courses.models import Module
    
    module_id = request.POST.get('module_id')
    if not module_id:
        return JsonResponse({'status': 'error', 'message': 'Module ID manquant'}, status=400)
    
    try:
        module = Module.objects.get(id=module_id)
        preferences, created = UserPreference.objects.get_or_create(user=request.user)
        
        if module_id in preferences.get_favorite_modules_ids():
            preferences.remove_favorite_module(module_id)
            is_favorite = False
        else:
            preferences.add_favorite_module(module_id)
            is_favorite = True
        
        # Mettre à jour les préférences dans la requête
        request.user_preferences['favorite_modules'] = preferences.get_favorite_modules_ids()
        request._update_preferences = True
        
        return JsonResponse({
            'status': 'success',
            'is_favorite': is_favorite,
            'message': 'Module retiré des favoris' if not is_favorite else 'Module ajouté aux favoris'
        })
        
    except Module.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Module non trouvé'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
@require_POST
def toggle_favorite_category(request):
    """
    Vue pour ajouter/retirer une catégorie des favoris (AJAX)
    """
    from .models import UserPreference
    from courses.models import Category
    
    category_id = request.POST.get('category_id')
    if not category_id:
        return JsonResponse({'status': 'error', 'message': 'Category ID manquant'}, status=400)
    
    try:
        category = Category.objects.get(id=category_id)
        preferences, created = UserPreference.objects.get_or_create(user=request.user)
        
        if category_id in preferences.get_favorite_categories_ids():
            preferences.remove_favorite_category(category_id)
            is_favorite = False
        else:
            preferences.add_favorite_category(category_id)
            is_favorite = True
        
        # Mettre à jour les préférences dans la requête
        request.user_preferences['favorite_categories'] = preferences.get_favorite_categories_ids()
        request._update_preferences = True
        
        return JsonResponse({
            'status': 'success',
            'is_favorite': is_favorite,
            'message': 'Catégorie retirée des favoris' if not is_favorite else 'Catégorie ajoutée aux favoris'
        })
        
    except Category.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Catégorie non trouvée'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
@require_POST
def update_session_preference(request):
    """
    Vue pour mettre à jour une préférence de session (AJAX)
    """
    from .models import UserPreference
    
    key = request.POST.get('key')
    value = request.POST.get('value')
    
    if not key:
        return JsonResponse({'status': 'error', 'message': 'Clé manquante'}, status=400)
    
    try:
        preferences, created = UserPreference.objects.get_or_create(user=request.user)
        
        # Mettre à jour la préférence de session
        preferences.update_session_preference(key, value)
        
        # Mettre à jour les préférences dans la requête
        request.user_preferences['session_preferences'] = preferences.session_preferences
        request._update_preferences = True
        
        return JsonResponse({
            'status': 'success',
            'message': 'Préférence de session mise à jour'
        })
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@never_cache
@login_required
@user_passes_test(lambda u: u.is_staff)
@require_http_methods(["GET"])
def system_metrics_api(request):
    """
    API pour récupérer les métriques système (RAM, disque, température)
    """
    try:
        # Métriques RAM
        memory = psutil.virtual_memory()
        ram_metrics = {
            'total': memory.total,
            'available': memory.available,
            'used': memory.used,
            'percentage': memory.percent
        }
        
        # Métriques disque - Toutes les partitions
        disk_metrics = {}
        try:
            # Récupérer toutes les partitions sur Windows
            if platform.system() == 'Windows':
                partitions = psutil.disk_partitions()
                for partition in partitions:
                    try:
                        usage = psutil.disk_usage(partition.mountpoint)
                        disk_metrics[partition.mountpoint] = {
                            'device': partition.device,
                            'mountpoint': partition.mountpoint,
                            'fstype': partition.fstype,
                            'total': usage.total,
                            'used': usage.used,
                            'free': usage.free,
                            'percentage': (usage.used / usage.total) * 100
                        }
                    except PermissionError:
                        # Ignorer les partitions inaccessibles
                        continue
            else:
                # Pour Linux/Mac, garder le comportement racine
                disk = psutil.disk_usage('/')
                disk_metrics['/'] = {
                    'device': '/',
                    'mountpoint': '/',
                    'fstype': 'unknown',
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percentage': (disk.used / disk.total) * 100
                }
        except Exception as e:
            logger.error(f"Error getting disk metrics: {str(e)}")
            disk_metrics = {'error': str(e)}
        
        # Métriques CPU
        cpu_metrics = {
            'percentage': psutil.cpu_percent(interval=1),
            'count': psutil.cpu_count(),
            'frequency': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
        }
        
        # Température (si disponible)
        temperature_metrics = {}
        try:
            if hasattr(psutil, 'sensors_temperatures'):
                temps = psutil.sensors_temperatures()
                if temps:
                    for name, entries in temps.items():
                        if entries:
                            temperature_metrics[name] = [
                                {
                                    'label': entry.label or 'Core',
                                    'current': entry.current,
                                    'high': entry.high,
                                    'critical': entry.critical
                                } for entry in entries
                            ]
        except Exception:
            temperature_metrics = {'error': 'Non disponible'}
        
        # Informations système
        system_info = {
            'platform': platform.system(),
            'platform_release': platform.release(),
            'platform_version': platform.version(),
            'architecture': platform.machine(),
            'processor': platform.processor(),
            'hostname': platform.node()
        }
        
        # Timestamp
        timestamp = datetime.now().isoformat()
        
        return JsonResponse({
            'status': 'success',
            'timestamp': timestamp,
            'ram': ram_metrics,
            'disk': disk_metrics,
            'cpu': cpu_metrics,
            'temperature': temperature_metrics,
            'system_info': system_info
        })
        
    except Exception as e:
        logger.error(f"Error in system_metrics_api: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


def get_user_preferences(request):
    """
    Vue API pour récupérer les préférences utilisateur (JSON)
    """
    if request.user.is_authenticated:
        from .models import UserPreference
        try:
            preferences, created = UserPreference.objects.get_or_create(user=request.user)
            return JsonResponse({
                'status': 'success',
                'preferences': preferences.to_cookie_data(),
                'session_preferences': preferences.session_preferences
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    else:
        # Pour les utilisateurs non connectés, retourner les préférences du cookie
        return JsonResponse({
            'status': 'success',
            'preferences': request.user_preferences,
            'session_preferences': {}
        })
