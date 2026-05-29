import logging
import json
import traceback
from datetime import datetime, timedelta
from django.db import transaction
from django.db import models
try:
    from classrooms.models import LiveSession
except ImportError:
    LiveSession = None

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError
from django.forms import modelformset_factory
from django.http import (
    HttpResponse, JsonResponse, HttpResponseBadRequest, 
    HttpResponseForbidden, HttpResponseRedirect
)
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST, require_GET
from django.views.generic import (
    DetailView, ListView, CreateView, 
    UpdateView, DeleteView, TemplateView
)

from evaluations.models import EvaluationLevel
from certifications.models import Certification
from exercices.models import Exercise, UserExerciseAttempt

from .models import (
    Course, Module, Lesson, Enrollment, 
    Comment, CourseRating, CourseLike, 
    LessonVideo, Category, CourseCompletion,
    LessonProgress
)
from .forms import CourseForm, ModuleForm, LessonForm, CategoryForm
from django.views.decorators.http import require_http_methods
import json
from django import template
from users.models import CustomUser as User
from exercices.models import UserExerciseAttempt

class LessonDetailView(DetailView):
    model = Lesson
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_attempts = {}
        if self.request.user.is_authenticated:
            from exercices.models import UserExerciseAttempt
            attempts = UserExerciseAttempt.objects.filter(
                user=self.request.user,
                exercise__in=self.object.exercises.all()
            ).select_related('selected_choice', 'exercise')
            
            for attempt in attempts:
                user_attempts[attempt.exercise.id] = {
                    'choice_id': attempt.selected_choice.id,
                    'is_correct': attempt.is_correct
                }
        
        context['user_exercise_attempts'] = user_attempts
        return context

class CategoryListView(ListView):
    model = Category
    template_name = 'courses/category_all.html'
    context_object_name = 'categories'
    
    def get_queryset(self):
        return Category.objects.filter(course__is_published=True).distinct().order_by('name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Ajouter les statistiques pour chaque catégorie
        categories_with_stats = []
        total_courses = 0
        total_modules = 0
        
        print(f"DEBUG: Found {len(context['categories'])} categories")
        
        for category in context['categories']:
            course_count = Course.objects.filter(category=category, is_published=True).count()
            # Calculer le nombre de modules pour cette catégorie
            modules_count = 0
            courses_in_category = Course.objects.filter(category=category, is_published=True)
            for course in courses_in_category:
                modules_count += course.modules.count()
            
            print(f"DEBUG: Category {category.name} - {course_count} courses, {modules_count} modules")
            
            categories_with_stats.append({
                'category': category,
                'course_count': course_count,
                'module_count': modules_count
            })
            
            total_courses += course_count
            total_modules += modules_count
        
        context['categories_with_stats'] = categories_with_stats
        context['total_courses'] = total_courses
        context['total_modules'] = total_modules
        context['avg_courses_per_category'] = total_courses / len(categories_with_stats) if categories_with_stats else 0
        
        print(f"DEBUG: Total - {total_courses} courses, {total_modules} modules")
        return context

def is_formateur(user):
    return (
        user.is_authenticated and (
            getattr(user, 'role', None) == 'trainer' or getattr(user, 'role', None) == 'admin' or user.is_superuser
        )
    )


@user_passes_test(is_formateur)
@login_required
def course_list(request):
    courses = Course.objects.all()
    return render(request, 'courses/course_list.html', {'courses': courses})


from django.db.models import Count, Q

@login_required
def course_detail(request, course_id):
    from .models import LessonProgress
    from evaluations.models import Attempt
    from django.db.models import Count, Q, Prefetch
    from users.models import CustomUser
    
    course = get_object_or_404(Course, id=course_id)
    is_enrolled = False
    is_course_completed = False
    progress_percent = 0
    completed_count = 0
    total_lessons = 0
    completed_lesson_ids = set()
    
    # Vérifier si l'utilisateur a réussi une évaluation pour ce cours
    has_passed_evaluation = False
    if request.user.is_authenticated:
        has_passed_evaluation = Attempt.objects.filter(
            user=request.user,
            evaluation__course=course,
            passed=True
        ).exists()
    
    # Précharger les modules avec leurs leçons actives et la progression
    modules = course.modules.prefetch_related(
        Prefetch(
            'lessons',
            queryset=Lesson.objects.filter(is_active=True).prefetch_related(
                Prefetch(
                    'lessonprogress_set',
                    queryset=LessonProgress.objects.filter(user=request.user) if request.user.is_authenticated else LessonProgress.objects.none(),
                    to_attr='user_progress'
                )
            )
        )
    ).annotate(
        total_lessons=Count('lessons', filter=Q(lessons__is_active=True)),
        completed_lessons=Count(
            'lessons',
            filter=Q(
                lessons__lessonprogress__user=request.user, 
                lessons__lessonprogress__is_completed=True,
                lessons__is_active=True
            ) if request.user.is_authenticated else Q(pk__in=[]),
            distinct=True
        )
    )
    
    # Calculer la progression globale en ne considérant que les leçons actives
    active_lessons = Lesson.objects.filter(module__course=course, is_active=True)
    total_lessons = active_lessons.count()
    
    # Vérifier si l'utilisateur est inscrit
    is_enrolled = False
    completed_count = 0
    is_course_completed = False
    
    if request.user.is_authenticated:
        is_enrolled = Enrollment.objects.filter(
            user=request.user, 
            course=course
        ).exists()
        
        if is_enrolled:
            # Compter uniquement les leçons actives terminées
            completed_lessons = LessonProgress.objects.filter(
                user=request.user,
                is_completed=True,
                lesson__in=active_lessons
            )
            completed_lesson_ids = set(completed_lessons.values_list('lesson_id', flat=True))
            completed_count = len(completed_lesson_ids)
            
            # Calculer le pourcentage de progression
            if total_lessons > 0:
                progress_percent = int((completed_count / total_lessons) * 100)
                
                # Marquer le cours comme terminé si toutes les leçons sont terminées
                if completed_count == total_lessons:
                    CourseCompletion.objects.get_or_create(
                        user=request.user,
                        course=course,
                        defaults={'completed_at': timezone.now()}
                    )
                    is_course_completed = True
                else:
                    is_course_completed = CourseCompletion.objects.filter(
                        user=request.user,
                        course=course
                    ).exists()
            else:
                progress_percent = 0
    else:
        progress_percent = 0
    
    # Obtenir les utilisateurs inscrits
    enrolled_users = course.enrollments.select_related('user').all()
    nombre_inscrits = enrolled_users.count()
    
    # Calculer la progression par niveau
    level_labels = {
        'beginner': 'Débutant',
        'intermediate': 'Intermédiaire',
        'advanced': 'Avancé',
    }
    levels_progress = []
    
    for level_key, level_name in level_labels.items():
        level_modules = [m for m in modules if m.level == level_key]
        lesson_ids_level = []
        
        # Récupérer toutes les leçons pour ce niveau
        for m in level_modules:
            lesson_ids_level.extend(list(m.lessons.values_list('id', flat=True)))
        
        total_level = len(lesson_ids_level)
        done_level = 0
        percent_level = 0
        is_level_completed = False
        
        # Calculer la progression pour ce niveau
        if total_level and request.user.is_authenticated:
            done_level = LessonProgress.objects.filter(
                user=request.user, 
                lesson_id__in=lesson_ids_level, 
                is_completed=True
            ).count()
            percent_level = int((done_level / total_level * 100)) if total_level > 0 else 0
            is_level_completed = (done_level == total_level) and (total_level > 0)
        
        # Vérifier s'il y a une évaluation pour ce niveau
        evaluation = None
        certification = None
        if request.user.is_authenticated:
            evaluation = EvaluationLevel.objects.filter(
                course=course, 
                level=level_key, 
                is_active=True
            ).first()
            
            certification = Certification.objects.filter(
                user=request.user, 
                course=course, 
                level=level_key, 
                is_valid=True
            ).first()
        
        # Ajouter les informations de progression pour ce niveau
        levels_progress.append({
            'key': level_key,
            'name': level_name,
            'label': level_name,
            'total': total_level,
            'completed_lessons': done_level,
            'total_lessons': total_level,
            'percent': percent_level,
            'is_completed': is_level_completed,
            'evaluation': evaluation,
            'certification': certification
        })

    # Récupérer le score du quiz s'il existe
    quiz_score = None
    if request.user.is_authenticated and is_enrolled:
        # Récupérer tous les exercices du cours
        course_exercises = Exercise.objects.filter(lesson__module__course=course)
        
        if course_exercises.exists():
            # Récupérer les tentatives de l'utilisateur pour ces exercices
            user_attempts = UserExerciseAttempt.objects.filter(
                user=request.user,
                exercise__in=course_exercises
            ).select_related('exercise', 'selected_choice')
            
            if user_attempts.exists():
                # Calculer le score
                total_questions = course_exercises.count()
                correct_answers = user_attempts.filter(is_correct=True).count()
                score_percentage = int((correct_answers / total_questions) * 100) if total_questions > 0 else 0
                
                quiz_score = {
                    'score': score_percentage,
                    'total_questions': total_questions,
                    'correct_answers': correct_answers,
                    'last_attempt': user_attempts.latest('created_at').created_at
                }

    # Préparer le contexte
    context = {
        'course': course,
        'modules': modules,
        'is_enrolled': is_enrolled,
        'is_course_completed': is_course_completed,
        'completed_count': completed_count,
        'completed_lesson_ids': completed_lesson_ids,
        'progress_percent': progress_percent,
        'total_lessons': total_lessons,
        'levels_progress': levels_progress,
        'enrolled_users': enrolled_users,
        'nombre_inscrits': nombre_inscrits,
        'has_passed_evaluation': has_passed_evaluation,
        'quiz_score': quiz_score,  # Ajout du score du quiz
    }

    # Course rating & like context
    from django.db.models import Avg
    avg_rating = CourseRating.objects.filter(course=course).aggregate(Avg('rating'))['rating__avg']
    if avg_rating is not None:
        avg_rating = round(avg_rating, 1)
    like_count = CourseLike.objects.filter(course=course).count()
    user_rating_value = None
    user_liked = False
    if request.user.is_authenticated:
        ur = CourseRating.objects.filter(course=course, user=request.user).first()
        if ur:
            user_rating_value = ur.rating
        user_liked = CourseLike.objects.filter(course=course, user=request.user).exists()

    context.update({
        'avg_rating': avg_rating,
        'like_count': like_count,
        'user_rating_value': user_rating_value,
        'user_liked': user_liked,
    })

    return render(request, 'courses/course_detail.html', context)


@login_required
def module_detail(request, course_id, module_id):
    module = get_object_or_404(Module, id=module_id, course__id=course_id)
    lessons = module.lessons.order_by('order')
    return render(request, 'courses/module_detail.html', {'module': module, 'lessons': lessons})


from django.utils import timezone
from django.db.models import Count

@login_required
def lesson_detail(request, lesson_id):
    from .models import LessonProgress, VideoView
    from django.contrib import messages
    
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.module.course

    is_enrolled = Enrollment.objects.filter(user=request.user, course=course).exists()
    first_module = course.modules.order_by('order').first()
    first_lesson = first_module.lessons.order_by('order').first() if first_module else None

    # Vérifier si l'utilisateur est inscrit
    if not is_enrolled and lesson != first_lesson:
        messages.warning(request, "Veuillez vous inscrire pour accéder à cette leçon.")
        return redirect('courses:course_detail', course_id=course.id)
    
    # Vérifier si le module est verrouillé (sauf pour le premier module)
    if lesson.module.is_locked and lesson != first_lesson:
        # Vérifier si l'utilisateur a un accès individuel à ce module
        from payments.models import ModuleAccess
        access = ModuleAccess.objects.filter(
            user=request.user,
            module=lesson.module,
            is_active=True
        ).first()
        
        if not access:
            messages.warning(request, "Vous devez d'abord terminer le module précédent pour accéder à ce module.")
            return redirect('courses:course_detail', course_id=course.id)
    
    # Vérifier si le module est payant et si l'utilisateur a accès
    if lesson.module.is_paid:
        from payments.models import ModuleAccess
        access = ModuleAccess.objects.filter(
            user=request.user,
            module=lesson.module,
            is_active=True
        ).first()
        
        if not access or not access.is_valid:
            messages.error(
                request,
                f"Ce module est payant. Vous devez payer {lesson.module.price} FCFA pour y accéder."
            )
            return redirect('payments:module_payment', module_id=lesson.module.id)
    
    # Vérifier si l'utilisateur a réussi le quiz du module précédent (sauf pour le premier module et les modules avancés)
    if lesson.module.order > 1 and lesson.module.level != 'advanced':
        previous_module = course.modules.filter(
            order=lesson.module.order - 1
        ).first()
        
        if previous_module:
            from exercices.models import Exercise, UserExerciseAttempt
            
            # Vérifier si le module précédent a un quiz
            has_quiz = Exercise.objects.filter(lesson__module=previous_module).exists()
            
            if has_quiz:
                # Vérifier si l'utilisateur a réussi le quiz
                exercises = Exercise.objects.filter(lesson__module=previous_module)
                user_attempts = UserExerciseAttempt.objects.filter(
                    user=request.user,
                    exercise__in=exercises
                )
                
                # Calculer le score
                correct_answers = user_attempts.filter(is_correct=True).count()
                total_questions = exercises.count()
                score = (correct_answers / total_questions * 100) if total_questions > 0 else 0
                
                if score < 80:  # Seuil de réussite à 80%
                    messages.warning(
                        request,
                        f"Vous devez d'abord réussir le quiz du module précédent avec au moins 80% de bonnes réponses."
                    )
                    return redirect('courses:course_detail', course_id=course.id)
    
    # Pour les modules avancés, vérifier uniquement le paiement (pas de quiz requis)
    # La vérification de paiement est déjà faite plus haut (lignes 348-361)
    # Build context for the page
    progress, created = LessonProgress.objects.get_or_create(
        user=request.user,
        lesson=lesson,
        defaults={'is_completed': False}
    )

    # Compte des inscrits
    enrollment_count = Enrollment.objects.filter(course=course).count()

    # Leçon suivante / précédente et playlist suivante
    # Leçons suivantes pour la navigation (ancienne logique)
    next_lesson_qs = Lesson.objects.filter(module=lesson.module, order__gt=lesson.order).order_by('order')
    next_lesson = next_lesson_qs.first()
    previous_lesson = Lesson.objects.filter(module=lesson.module, order__lt=lesson.order).order_by('-order').first()
    next_lessons = list(next_lesson_qs)

    # Videos: active video for current lesson and media for next lessons
    lesson_videos = list(lesson.videos.all())
    active_video = None
    active_video_url = None
    
    print(f"DEBUG: lesson_videos count: {len(lesson_videos)}")
    
    if lesson_videos:
        active_video = lesson_videos[0]
        print(f"DEBUG: active_video found: {active_video}")
        print(f"DEBUG: active_video.video_file: {active_video.video_file}")
        
        active_video_url = active_video.video_file.url if active_video.video_file else None
        print(f"DEBUG: active_video_url: {active_video_url}")
        
        # Enregistrer la vue de la vidéo
        if active_video:
            VideoView.objects.create(
                video=active_video,
                user=request.user if request.user.is_authenticated else None,
                ip_address=request.META.get('REMOTE_ADDR')
            )
    
    if not active_video_url and getattr(lesson, 'video_file', None):
        # fallback to legacy field
        try:
            active_video_url = lesson.video_file.url
            print(f"DEBUG: fallback video_url: {active_video_url}")
        except Exception:
            active_video_url = None
    # Build playlist entries with media_url to avoid dict subscripting in template
    next_playlist = []
    for nl in next_lessons:
        media_url = None
        first_vid = nl.videos.first()
        if first_vid and first_vid.video_file:
            try:
                media_url = first_vid.video_file.url
            except Exception:
                media_url = None
        if not media_url and getattr(nl, 'video_file', None):
            try:
                media_url = nl.video_file.url
            except Exception:
                media_url = None
        next_playlist.append({'lesson': nl, 'media_url': media_url})

    # Completed lessons for this course (for 'lu' markers)
    completed_ids = set(LessonProgress.objects.filter(
        user=request.user,
        lesson__module__course=course,
        is_completed=True
    ).values_list('lesson_id', flat=True))

    # SOLUTION AMÉLIORÉE : Playlist de TOUTES les vidéos du module actuel
    simple_playlist = []  # Initialisation par défaut
    
    print("="*50)
    print("DÉBUT CRÉATION PLAYLIST COMPLÈTE DU MODULE")
    print("="*50)
    print(f"Leçon actuelle ID: {lesson.id}")
    print(f"Leçon actuelle titre: {lesson.title}")
    print(f"Module actuel ID: {lesson.module.id}")
    print(f"Module actuel titre: {lesson.module.title}")
    
    try:
        # Récupérer toutes les leçons du module actuel (triées par ordre)
        current_module_lessons = lesson.module.lessons.filter(is_active=True).order_by('order')
        print(f"Leçons du module actuel: {current_module_lessons.count()}")
        
        video_index = 0
        
        # Parcourir toutes les leçons du module
        for module_lesson in current_module_lessons:
            print(f"\nTraitement leçon {module_lesson.order}: {module_lesson.title}")
            
            # Récupérer les vidéos de cette leçon
            module_lesson_videos = list(module_lesson.videos.all())
            main_video_url = None
            
            # Vérifier la vidéo principale de la leçon
            if hasattr(module_lesson, 'video_file') and module_lesson.video_file:
                try:
                    main_video_url = module_lesson.video_file.url
                    print(f"  URL vidéo principale: {main_video_url}")
                except Exception as e:
                    print(f"  Erreur URL vidéo principale: {e}")
            
            # Ajouter la vidéo principale si elle existe
            if main_video_url:
                video_index += 1
                is_current_lesson = (module_lesson.id == lesson.id)
                
                playlist_item = {
                    'lesson_id': module_lesson.id,
                    'title': f"{module_lesson.title} - Vidéo principale",
                    'module_title': lesson.module.title,
                    'href': reverse('courses:lesson_detail', args=[module_lesson.id]),
                    'video_url': main_video_url,
                    'has_video': True,
                    'is_current': is_current_lesson,
                    'is_completed': module_lesson.id in completed_ids,
                    'video_part': 'principale',
                    'lesson_order': module_lesson.order
                }
                simple_playlist.append(playlist_item)
                print(f"  Ajouté vidéo principale: {playlist_item}")
            
            # Ajouter toutes les vidéos additionnelles de la leçon
            for idx, lesson_video in enumerate(module_lesson_videos):
                video_url = None
                video_title = f"Partie {idx + 1}"
                
                if lesson_video.title:
                    video_title = lesson_video.title
                
                if lesson_video.video_file:
                    try:
                        video_url = lesson_video.video_file.url
                        print(f"  URL vidéo {idx + 1}: {video_url}")
                    except Exception as e:
                        print(f"  Erreur URL vidéo {idx + 1}: {e}")
                
                if video_url:
                    video_index += 1
                    is_current_lesson = (module_lesson.id == lesson.id)
                    
                    playlist_item = {
                        'lesson_id': module_lesson.id,
                        'title': f"{module_lesson.title} - {video_title}",
                        'module_title': lesson.module.title,
                        'href': reverse('courses:lesson_detail', args=[module_lesson.id]),
                        'video_url': video_url,
                        'has_video': True,
                        'is_current': is_current_lesson,
                        'is_completed': module_lesson.id in completed_ids,
                        'video_part': video_title,
                        'lesson_order': module_lesson.order
                    }
                    simple_playlist.append(playlist_item)
                    print(f"  Ajouté vidéo {idx + 1}: {playlist_item}")
        
        # Vérifier si le module suivant est déverrouillé et ajouter ses vidéos
        print("\nVérification du module suivant...")
        next_module = course.modules.filter(order__gt=lesson.module.order).order_by('order').first()
        
        if next_module:
            print(f"Module suivant trouvé: {next_module.title}")
            
            # Vérifier si le module suivant est accessible
            is_next_module_locked = next_module.is_locked
            needs_payment = next_module.is_paid
            
            if not is_next_module_locked and not needs_payment:
                print("Module suivant accessible, ajout de ses vidéos...")
                
                # Récupérer les leçons du module suivant
                next_module_lessons = next_module.lessons.filter(is_active=True).order_by('order')
                
                for next_lesson in next_module_lessons:
                    print(f"  Traitement leçon suivante: {next_lesson.title}")
                    
                    # Récupérer les vidéos de la leçon suivante
                    next_lesson_videos = list(next_lesson.videos.all())
                    next_main_video_url = None
                    
                    if hasattr(next_lesson, 'video_file') and next_lesson.video_file:
                        try:
                            next_main_video_url = next_lesson.video_file.url
                        except Exception:
                            next_main_video_url = None
                    
                    # Ajouter la vidéo principale de la leçon suivante
                    if next_main_video_url:
                        video_index += 1
                        playlist_item = {
                            'lesson_id': next_lesson.id,
                            'title': f"{next_lesson.title} - Vidéo principale",
                            'module_title': next_lesson.title,
                            'href': reverse('courses:lesson_detail', args=[next_lesson.id]),
                            'video_url': next_main_video_url,
                            'has_video': True,
                            'is_current': False,
                            'is_completed': next_lesson.id in completed_ids,
                            'is_next_module': True,
                            'is_paid_module': False,
                            'lesson_order': next_lesson.order
                        }
                        simple_playlist.append(playlist_item)
                        print(f"    Ajouté vidéo principale leçon suivante: {playlist_item}")
                    
                    # Ajouter les vidéos additionnelles de la leçon suivante
                    for idx, next_video in enumerate(next_lesson_videos):
                        next_video_url = None
                        next_video_title = f"Partie {idx + 1}"
                        
                        if next_video.title:
                            next_video_title = next_video.title
                        
                        if next_video.video_file:
                            try:
                                next_video_url = next_video.video_file.url
                            except Exception:
                                next_video_url = None
                        
                        if next_video_url:
                            video_index += 1
                            playlist_item = {
                                'lesson_id': next_lesson.id,
                                'title': f"{next_lesson.title} - {next_video_title}",
                                'module_title': next_lesson.title,
                                'href': reverse('courses:lesson_detail', args=[next_lesson.id]),
                                'video_url': next_video_url,
                                'has_video': True,
                                'is_current': False,
                                'is_completed': next_lesson.id in completed_ids,
                                'is_next_module': True,
                                'is_paid_module': False,
                                'lesson_order': next_lesson.order
                            }
                            simple_playlist.append(playlist_item)
                            print(f"    Ajouté vidéo leçon suivante {idx + 1}: {playlist_item}")
            elif needs_payment:
                print("Module suivant payant sans accès, ajout d'une indication de paiement")
                # Ajouter une indication que le module suivant est payant
                playlist_item = {
                    'lesson_id': None,
                    'title': f"{next_module.title} - Module premium",
                    'module_title': next_module.title,
                    'href': reverse('payments:module_payment', args=[next_module.id]),
                    'video_url': None,
                    'has_video': False,
                    'is_current': False,
                    'is_completed': False,
                    'is_next_module': True,
                    'is_paid_module': True,
                    'module_price': next_module.price
                }
                simple_playlist.append(playlist_item)
                print(f"  Ajouté indication module payant: {playlist_item}")
            else:
                print("Module suivant verrouillé, aucune vidéo ajoutée")
        else:
            print("Aucun module suivant trouvé")
        
        print(f"\nPlaylist complète créée avec {len(simple_playlist)} vidéos")
        print(f"Leçon actuelle: {lesson.title}")
        print(f"Vidéos avec URL valide: {sum(1 for p in simple_playlist if p['has_video'])}")
        
        # Afficher les premiers éléments pour vérification
        if simple_playlist:
            print(f"Premiers éléments de la playlist:")
            for i, item in enumerate(simple_playlist[:3]):
                print(f"  {i+1}. {item}")
        
    except Exception as e:
        print(f"ERREUR lors de la création de la playlist: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        simple_playlist = []
    
    print("="*50)
    print("FIN CRÉATION PLAYLIST COMPLÈTE DU MODULE")
    print("="*50)

    # Level completion and evaluation for CTA
    level_key = getattr(lesson.module, 'level', None)
    level_completed = False
    level_evaluation = None
    if is_enrolled and level_key:
        level_lessons_qs = Lesson.objects.filter(module__course=course, module__level=level_key)
        total_level_lessons = level_lessons_qs.count()
        done_in_level = LessonProgress.objects.filter(user=request.user, lesson__in=level_lessons_qs, is_completed=True).count()
        level_completed = total_level_lessons > 0 and done_in_level == total_level_lessons
        from evaluations.models import EvaluationLevel
        level_evaluation = EvaluationLevel.objects.filter(course=course, level=level_key, is_active=True).first()

    # Récupérer l'URL de la miniature du cours
    course_thumbnail_url = course.thumbnail.url if course.thumbnail else None
    
    # Combined hierarchical playlist: all current lesson videos then all next lessons videos
    combined_playlist = []
    # current lesson videos
    for idx, lv in enumerate(lesson_videos):
        try:
            url = lv.video_file.url
        except Exception:
            url = None
        if url:
            combined_playlist.append({
                'lesson_id': lesson.id,
                'title': lv.title or f"{lesson.title} - Partie {idx+1}",
                'media_url': url,
                'href': reverse('courses:lesson_detail', args=[lesson.id]),
                'thumbnail_url': course_thumbnail_url,  # Utiliser la miniature du cours
            })
    # fallback if no LessonVideo
    if not combined_playlist and getattr(lesson, 'video_file', None):
        try:
            combined_playlist.append({
                'lesson_id': lesson.id, 
                'title': lesson.title, 
                'media_url': lesson.video_file.url, 
                'href': reverse('courses:lesson_detail', args=[lesson.id]),
                'thumbnail_url': course_thumbnail_url,  # Utiliser la miniature du cours
            })
        except Exception:
            pass
    # next lessons videos
    for nl in next_lessons:
        vids = list(nl.videos.all())
        if vids:
            for j, v in enumerate(vids):
                try:
                    url = v.video_file.url
                except Exception:
                    url = None
                if url:
                    combined_playlist.append({
                        'lesson_id': nl.id,
                        'title': v.title or f"{nl.title} - Partie {j+1}",
                        'media_url': url,
                        'href': reverse('courses:lesson_detail', args=[nl.id]),
                        'thumbnail_url': course_thumbnail_url,  # Utiliser la miniature du cours
                    })
        elif getattr(nl, 'video_file', None):
            try:
                combined_playlist.append({
                    'lesson_id': nl.id, 
                    'title': nl.title, 
                    'media_url': nl.video_file.url, 
                    'href': reverse('courses:lesson_detail', args=[nl.id]),
                    'thumbnail_url': course_thumbnail_url,  # Utiliser la miniature du cours
                })
            except Exception:
                pass

    # Get user exercise attempts
    user_exercise_attempts = {}
    if request.user.is_authenticated:
        from exercices.models import UserExerciseAttempt
        attempts = UserExerciseAttempt.objects.filter(
            user=request.user,
            exercise__in=lesson.exercises.all()
        ).select_related('selected_choice', 'exercise')
        
        for attempt in attempts:
            user_exercise_attempts[attempt.exercise.id] = {
                'choice_id': attempt.selected_choice.id,
                'is_correct': attempt.is_correct
            }

    # Comments and ratings context
    comments = list(Comment.objects.filter(lesson=lesson).select_related('user').order_by('-created_at')[:50])
    print(f"Commentaires chargés pour la leçon {lesson.id}: {len(comments)}")
    for c in comments:
        print(f"Commentaire {c.id}: {c.content[:50]}... (par {c.user.username}, {c.created_at})")
    from django.db.models import Avg
    avg_rating = CourseRating.objects.filter(course=course).aggregate(Avg('rating'))['rating__avg']
    if avg_rating is not None:
        avg_rating = round(avg_rating, 1)
    user_rating_value = None
    like_count = CourseLike.objects.filter(course=course).count()
    user_liked = False
    if request.user.is_authenticated:
        ur = CourseRating.objects.filter(course=course, user=request.user).first()
        if ur:
            user_rating_value = ur.rating
    # Vérifier si la leçon est marquée comme terminée
    lesson_completed = progress.is_completed if hasattr(progress, 'is_completed') else False
    
    # Compter le nombre de vues uniques pour la leçon
    video_views_count = 0
    if active_video:
        video_views_count = VideoView.objects.filter(video=active_video).count()

    # Récupérer la miniature du cours
    course_thumbnail_url = course.thumbnail.url if course.thumbnail else None
    
    # URL du fichier de sous-titres s'il existe
    subtitle_url = lesson.subtitle_file.url if lesson.subtitle_file and hasattr(lesson.subtitle_file, 'url') else None

    context = {
        'lesson': lesson,
        'module': lesson.module,
        'course': course,
        'course_thumbnail_url': course_thumbnail_url,  # Ajout de la miniature du cours
        'progress': progress,
        'completed_lesson_ids': list(completed_ids),
        'enrollment_count': enrollment_count,
        'next_lesson': next_lesson,
        'previous_lesson': previous_lesson,
        'next_lessons': next_lessons,
        'next_playlist': next_playlist,
        'is_enrolled': is_enrolled,
        'first_lesson': first_lesson,
        'level_key': level_key,
        'level_completed': level_completed,
        'level_evaluation': level_evaluation,
        'comments': comments,
        'avg_rating': avg_rating,
        'user_rating_value': user_rating_value,
        'like_count': like_count,
        'user_liked': user_liked,
        'lesson_videos': lesson_videos,
        'simple_playlist': simple_playlist,  # Nouvelle playlist simple
        'active_video_url': active_video_url,
        'combined_playlist': combined_playlist,
        'user_exercise_attempts': user_exercise_attempts,
        'lesson_completed': lesson_completed,
        'video_views_count': video_views_count,
        'active_video': active_video,  # Ajouté pour le débogage
        'subtitle_url': subtitle_url,  # URL du fichier de sous-titres
    }
    print("="*50)
    print("CONTEXTE ENVOYÉ AU TEMPLATE")
    print("="*50)
    print(f"Clés du contexte: {list(context.keys())}")
    print(f"simple_playlist dans le contexte: {'simple_playlist' in context}")
    if 'simple_playlist' in context:
        print(f"Longueur de simple_playlist: {len(context['simple_playlist'])}")
        if context['simple_playlist']:
            print(f"Premier élément: {context['simple_playlist'][0]}")
    print(f"completed_lesson_ids: {context.get('completed_lesson_ids', 'NOT_FOUND')[:5]}...")
    print("="*50)
    
    return render(request, 'courses/lesson_detail.html', context)


@login_required
@require_POST
def add_comment(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.module.course
    # Optional: restrict commenting to enrolled users
    if not Enrollment.objects.filter(user=request.user, course=course).exists():
        messages.error(request, "Vous devez être inscrit pour commenter.")
        return redirect('courses:lesson_detail', lesson_id=lesson_id)
    content = request.POST.get('content', '').strip()
    if content:
        Comment.objects.create(user=request.user, lesson=lesson, content=content)
        messages.success(request, "Commentaire ajouté.")
    else:
        messages.error(request, "Le commentaire est vide.")
    return redirect('courses:lesson_detail', lesson_id=lesson_id)

# 🎯 VUE POUR NETTOYER LES MESSAGES DE SESSION SWEETALERT
@login_required
@require_POST
def clear_session_message(request):
    """Nettoie le message de félicitations de la session après affichage du SweetAlert"""
    if 'module_completion_message' in request.session:
        del request.session['module_completion_message']
        request.session.modified = True
    
    return JsonResponse({'success': True})

# 🎉 VUES POUR NETTOYER LES MESSAGES D'ÉVALUATION
@login_required
@require_POST
def clear_evaluation_success_message(request):
    """Nettoie le message de succès d'évaluation de la session"""
    if 'evaluation_success_message' in request.session:
        del request.session['evaluation_success_message']
        request.session.modified = True
    
    return JsonResponse({'success': True})

@login_required
@require_POST
def clear_evaluation_failure_message(request):
    """Nettoie le message d'échec d'évaluation de la session"""
    if 'evaluation_failure_message' in request.session:
        del request.session['evaluation_failure_message']
        request.session.modified = True
    
    return JsonResponse({'success': True})

@login_required
@require_POST
def rate_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    try:
        rating = int(request.POST.get('rating', '0'))
    except ValueError:
        rating = 0
    if rating < 1 or rating > 5:
        messages.error(request, "Note invalide.")
        return redirect('courses:course_detail', course_id=course.id)
    obj, _ = CourseRating.objects.update_or_create(
        user=request.user, course=course, defaults={'rating': rating}
    )
    messages.success(request, "Votre note a été enregistrée.")
    # Revenir à la leçon si referer indique une leçon
    ref = request.META.get('HTTP_REFERER') or ''
    if '/lessons/' in ref:
        return redirect(ref)
    return redirect('courses:course_detail', course_id=course.id)


@csrf_exempt
@login_required
@require_POST
def toggle_like_ajax(request, course_id):
    """Vue AJAX pour gérer les likes des cours"""
    course = get_object_or_404(Course, id=course_id)
    
    try:
        like_obj = CourseLike.objects.filter(course=course, user=request.user).first()
        
        if like_obj:
            # Unlike
            like_obj.delete()
            is_liked = False
            message = "Vous n'aimez plus ce cours"
        else:
            # Like
            CourseLike.objects.create(course=course, user=request.user)
            is_liked = True
            message = "Cours ajouté à vos favoris"
        
        # Compter le nombre total de likes
        likes_count = course.likes.count()
        
        return JsonResponse({
            'success': True,
            'is_liked': is_liked,
            'likes_count': likes_count,
            'message': message
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_POST
def toggle_like(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    obj = CourseLike.objects.filter(course=course, user=request.user).first()
    if obj:
        obj.delete()
        messages.info(request, "Vous n'aimez plus ce cours.")
    else:
        CourseLike.objects.create(course=course, user=request.user)
        messages.success(request, "Cours ajouté à vos favoris.")
    ref = request.META.get('HTTP_REFERER') or ''
    if '/lessons/' in ref:
        return redirect(ref)
    return redirect('courses:course_detail', course_id=course.id)



@require_http_methods(["GET", "POST"])
@login_required
@user_passes_test(is_formateur)
def create_category(request):
    """
    Vue pour créer une nouvelle catégorie.
    Gère à la fois les requêtes AJAX et les requêtes normales.
    """
    logger = logging.getLogger(__name__)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        
        if form.is_valid():
            try:
                # La validation du formulaire et la vérification des doublons
                # sont maintenant gérées par le modèle et le formulaire
                category = form.save()
                logger.info(f"Nouvelle catégorie créée: {category.name} (ID: {category.id})")
                
                if is_ajax:
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Catégorie créée avec succès',
                        'category': {
                            'id': category.id,
                            'name': category.name,
                            'slug': category.slug
                        }
                    }, status=201)  # 201 Created
                
                messages.success(request, f'La catégorie "{category.name}" a été créée avec succès.')
                return redirect('courses:course_create')
                
            except ValidationError as e:
                # Gestion des erreurs de validation du modèle
                error_msg = str(e)
                logger.warning(f"Erreur de validation: {error_msg}")
                
                if is_ajax:
                    return JsonResponse({
                        'status': 'error',
                        'message': error_msg,
                        'code': 'validation_error'
                    }, status=400)
                    
                messages.error(request, error_msg)
                
            except Exception as e:
                # Gestion des autres erreurs inattendues
                logger.error(f"Erreur inattendue lors de la création de la catégorie: {str(e)}", exc_info=True)
                error_msg = "Une erreur est survenue lors de la création de la catégorie."
                
                if is_ajax:
                    return JsonResponse({
                        'status': 'error',
                        'message': error_msg,
                        'code': 'server_error'
                    }, status=500)
                    
                messages.error(request, error_msg)
        else:
            # Le formulaire n'est pas valide
            error_msg = form.errors.as_text()
            logger.warning(f"Formulaire invalide: {error_msg}")
            
            if is_ajax:
                return JsonResponse({
                    'status': 'error',
                    'message': error_msg,
                    'code': 'form_validation_error'
                }, status=400)
                
            messages.error(request, f"Erreur de validation: {error_msg}")
            
        return redirect('courses:course_create')
            
    else:  # GET request
        form = CategoryForm()
    
    # Si ce n'est pas une requête AJAX, afficher le formulaire
    if not is_ajax:
        return render(request, 'courses/category_form.html', {
            'form': form,
            'title': 'Ajouter une catégorie'
        })
    
    return JsonResponse(
        {'status': 'error', 'message': 'Méthode non autorisée'},
        status=405
    )


@user_passes_test(is_formateur)
@login_required
def course_create(request):
    """
    Redirige vers la vue unifiée de création de cours.
    Cette vue est conservée pour la rétrocompatibilité.
    """
    return redirect('courses:unified_course_creation')


@user_passes_test(is_formateur)
@login_required
@require_http_methods(["POST"])
def module_create(request, course_id):
    """
    Crée un nouveau module pour un cours existant.
    Gère les requêtes AJAX pour une expérience utilisateur fluide.
    """
    try:
        # Vérifier si le cours existe et que l'utilisateur a les droits
        course = get_object_or_404(Course, id=course_id)
        if course.created_by != request.user and not request.user.is_superuser:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Permission refusée'}, status=403)
            raise PermissionDenied("Vous n'avez pas la permission d'ajouter un module à ce cours.")
        
        # Récupérer les données du formulaire
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        order = request.POST.get('order', 1)
        
        # Validation des données
        if not title:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Le titre du module est obligatoire'}, status=400)
            messages.error(request, 'Le titre du module est obligatoire')
            return redirect('courses:course_detail', course_id=course_id)
        
        # Créer le module
        module = Module.objects.create(
            course=course,
            title=title,
            description=description,
            order=order
        )
        
        # Réponse pour les requêtes AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Module ajouté avec succès',
                'module_id': module.id,
                'module_title': module.title
            })
        
        messages.success(request, 'Le module a été ajouté avec succès.')
        return redirect('courses:course_detail', course_id=course_id)
        
    except Exception as e:
        error_msg = f"Une erreur est survenue lors de la création du module: {str(e)}"
        logger.error(error_msg)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': error_msg
            }, status=500)
            
        messages.error(request, error_msg)
        return redirect('courses:course_detail', course_id=course_id)


@user_passes_test(is_formateur)
@login_required
def lesson_create(request, course_id, module_id):
    """
    Redirige vers la vue unifiée de création de cours.
    Cette vue est conservée pour la rétrocompatibilité.
    """
    return redirect('courses:unified_course_creation')


@user_passes_test(is_formateur)
@login_required
def lesson_video_create(request, lesson_id):
    """
    Redirige vers la vue unifiée de création de cours.
    Cette vue est conservée pour la rétrocompatibilité.
    """
    return redirect('courses:unified_course_creation')


@login_required
@require_POST
def enroll_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    # Only learners can enroll
    if not request.user.is_authenticated or getattr(request.user, 'role', None) != 'learner':
        messages.error(request, "Seuls les apprenants peuvent s'inscrire à un cours.")
        return redirect('courses:course_detail', course_id=course.id)
    enrollment, created = Enrollment.objects.get_or_create(user=request.user, course=course)
    if created:
        messages.success(request, f"Vous êtes bien inscrit au cours {course.title}.")
    else:
        messages.info(request, f"Vous êtes déjà inscrit à ce cours.")
    return redirect('courses:course_detail', course_id=course.id)

def all_courses(request):
    from .models import Category
    category_slug = request.GET.get('category') or ''
    categories = list(Category.objects.all())

    qs = Course.objects.select_related('category').all()
    selected_category = None
    if category_slug:
        selected_category = next((c for c in categories if c.slug == category_slug), None)
        if selected_category:
            qs = qs.filter(category=selected_category)

    # text search
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))

    highlight_courses = list(Course.objects.order_by('-created_at')[:4])

    upcoming_sessions = []
    if LiveSession is not None:
        try:
            upcoming_sessions = list(
                LiveSession.objects.filter(start_at__gte=timezone.now())
                .select_related('classroom', 'classroom__course')
                .order_by('start_at')[:5]
            )
        except Exception:
            upcoming_sessions = []

    context = {
        'courses': qs,
        'categories': categories,
        'selected_category': selected_category,
        'q': q,
        'highlight_courses': highlight_courses,
        'upcoming_sessions': upcoming_sessions,
    }
    return render(request, 'courses/all_course.html', context)

def search(request):
    q = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'all')  # 'all', 'channels', 'videos'
    
    course_results = []
    video_results = []
    instructor_results = []
    
    if q:
        from django.contrib.auth import get_user_model
        from django.db.models import Count, Q, Prefetch, Case, When, Value, IntegerField, F
        from django.db.models.functions import Concat, Lower
        User = get_user_model()
        
        # Recherche de formateurs (chaînes)
        if search_type in ['all', 'channels']:
            from django.db.models import Subquery, OuterRef, Count, Q, Case, When, Value, IntegerField
            from django.db.models.functions import Concat
            
            # Sous-requête pour compter les abonnés actifs
            from subscriptions.models import Subscription
            active_subscribers = Subscription.objects.filter(
                trainer=OuterRef('pk'),
                is_active=True
            ).values('trainer').annotate(count=Count('id')).values('count')
            
            # Récupérer tous les formateurs correspondant à la recherche
            instructor_results = User.objects.filter(
                Q(username__icontains=q) | 
                Q(first_name__icontains=q) | 
                Q(last_name__icontains=q) |
                Q(bio__icontains=q) |
                Q(email__icontains=q),
                is_active=True,
                role='trainer'
            ).annotate(
                full_name=Concat('first_name', Value(' '), 'last_name'),
                courses_count=Count('courses', distinct=True),
                subscribers_count=Subquery(active_subscribers, output_field=IntegerField()),
                # Score de pertinence
                relevance=Case(
                    When(username__iexact=q, then=Value(100)),
                    When(username__istartswith=q, then=Value(80)),
                    When(full_name__iexact=q, then=Value(70)),
                    When(full_name__icontains=q, then=Value(50)),
                    When(bio__icontains=q, then=Value(30)),
                    default=Value(10),
                    output_field=IntegerField()
                )
            ).order_by('-relevance', '-subscribers_count')
            
            # Remplacer None par 0 pour les formateurs sans abonnés
            for instructor in instructor_results:
                if instructor.subscribers_count is None:
                    instructor.subscribers_count = 0
        
        # Recherche de cours
        if search_type in ['all', 'courses']:
            # Construction de la requête de base
            base_query = Course.objects.filter(
                Q(title__icontains=q) | 
                Q(description__icontains=q) |
                Q(category__name__icontains=q) |
                Q(created_by__username__icontains=q) |
                Q(created_by__first_name__icontains=q) |
                Q(created_by__last_name__icontains=q)
            )
            
            # Optimisation des requêtes avec select_related et prefetch_related
            base_query = base_query.select_related('category', 'created_by')
            
            # Préchargement des modules et leçons associés
            base_query = base_query.prefetch_related(
                Prefetch(
                    'modules',
                    queryset=Module.objects.prefetch_related('lessons')
                )
            )
            
            # Ajout des annotations pour le comptage et le score de pertinence
            from django.db.models import Count, Case, When, Value, IntegerField
            
            course_results = base_query.annotate(
                lessons_count=Count('modules__lessons', distinct=True),
                relevance=Case(
                    When(title__iexact=q, then=Value(100)),
                    When(title__istartswith=q, then=Value(80)),
                    When(title__icontains=q, then=Value(60)),
                    When(description__icontains=q, then=Value(30)),
                    default=Value(10),
                    output_field=IntegerField()
                )
            ).order_by('-relevance', '-created_at')[:12]
            
        # Recherche de vidéos
        if search_type in ['all', 'videos']:
            from datetime import datetime
            
            # Sous-requête pour compter les vues de chaque vidéo
            from django.db.models import Count, OuterRef, Subquery, IntegerField
            
            video_results = LessonVideo.objects.filter(
                Q(title__icontains=q) | 
                Q(lesson__title__icontains=q) |
                Q(lesson__module__course__title__icontains=q) |
                Q(lesson__module__course__created_by__username__icontains=q) |
                Q(lesson__module__course__created_by__first_name__icontains=q) |
                Q(lesson__module__course__created_by__last_name__icontains=q)
            ).select_related(
                'lesson', 
                'lesson__module', 
                'lesson__module__course', 
                'lesson__module__course__created_by',
                'lesson__module__course__category'
            ).annotate(
                course_title=F('lesson__module__course__title'),
                instructor_name=Concat(
                    'lesson__module__course__created_by__first_name',
                    Value(' '),
                    'lesson__module__course__created_by__last_name'
                ),
                # Compter les vues directement dans la requête (utiliser un nom différent de la propriété existante)
                video_views_count=Count('views'),
                # Score de pertinence
                relevance=Case(
                    When(title__iexact=q, then=Value(100)),
                    When(title__istartswith=q, then=Value(80)),
                    When(title__icontains=q, then=Value(60)),
                    When(lesson__title__iexact=q, then=Value(70)),
                    When(lesson__title__icontains=q, then=Value(50)),
                    When(lesson__module__course__title__iexact=q, then=Value(60)),
                    When(lesson__module__course__title__icontains=q, then=Value(40)),
                    When(lesson__module__course__created_by__username__iexact=q, then=Value(50)),
                    When(lesson__module__course__created_by__username__icontains=q, then=Value(30)),
                    default=Value(10),
                    output_field=IntegerField()
                )
            ).order_by('-relevance', '-id')
            
            # Si la recherche est spécifiquement pour un formateur, filtrer par son nom d'utilisateur
            if q.startswith('@'):
                username = q[1:].strip()
                video_results = video_results.filter(
                    lesson__module__course__created_by__username__iexact=username
                )
        
        # Si la recherche est spécifiquement pour un formateur et qu'on a un seul résultat exact
        if search_type == 'instructor' and len(instructor_results) == 1:
            exact_match = any([
                q.lower() == instructor_results[0].username.lower(),
                q.lower() == instructor_results[0].get_full_name().lower(),
                q.lower() == instructor_results[0].email.lower()
            ])
            if exact_match:
                return redirect('users:instructor_public', username=instructor_results[0].username)
    
    # Préparer les résultats pour le template
    context = {
        'q': q,
        'search_type': search_type,
        'video_results': video_results[:12] if search_type in ['all', 'videos'] else [],
        'instructor_results': instructor_results[:12] if search_type in ['all', 'channels'] else [],
        'has_results': bool(instructor_results.exists() if hasattr(instructor_results, 'exists') else instructor_results) or 
                      bool(video_results.exists() if hasattr(video_results, 'exists') else video_results),
    }
    
    # Si on est en recherche de formateurs et qu'il n'y a pas de résultats, proposer des suggestions
    if search_type == 'instructor' and not instructor_results and not instructor_channels:
        # Suggérer des formateurs populaires
        from django.db.models import Count
        suggested_instructors = User.objects.filter(
            is_active=True,
            role='trainer'
        ).annotate(
            courses_count=Count('course', distinct=True),
            subscribers_count=Count('subscribers', filter=Q(subscriptions__is_active=True), distinct=True)
        ).order_by('-subscribers_count', '-courses_count')[:5]
        
        if suggested_instructors.exists():
            context['suggested_instructors'] = suggested_instructors
    
    return render(request, 'courses/search.html', context)


def search_suggest(request):
    q = request.GET.get('q', '').strip()
    search_type = request.GET.get('search_type', 'course')
    
    if not q:
        return JsonResponse({'items': []})
        
    items = []
    
    if search_type == 'instructor':
        # Suggestions pour les formateurs
        from django.contrib.auth import get_user_model
        User = get_user_model()
        instructors = User.objects.filter(
            Q(username__icontains=q) | 
            Q(first_name__icontains=q) | 
            Q(last_name__icontains=q) |
            Q(bio__icontains=q) |
            Q(email__icontains=q),
            is_active=True,
            role='instructor'  # Utilisation du champ role au lieu de is_instructor
        ).distinct()[:5]
        
        for instructor in instructors:
            full_name = f"{instructor.first_name} {instructor.last_name}".strip()
            if not full_name:
                full_name = instructor.username
            items.append({
                'type': 'instructor', 
                'id': instructor.id, 
                'label': f"Formateur: {full_name}", 
                'url': reverse('handle_profile', args=[instructor.username])
            })
    else:
        # Suggestions pour les cours
        courses = Course.objects.filter(
            Q(title__icontains=q) |
            Q(created_by__username__icontains=q) |
            Q(created_by__first_name__icontains=q) |
            Q(created_by__last_name__icontains=q)
        ).select_related('created_by').distinct().order_by('title')[:5]
        
        for course in courses:
            items.append({
                'type': 'course', 
                'id': course.id, 
                'label': f"{course.title} (par {course.created_by.get_full_name() or course.created_by.username})", 
                'url': reverse('courses:course_detail', args=[course.id])
            })
            
        # Ajouter aussi les leçons si nécessaire
        lessons = Lesson.objects.filter(
            Q(title__icontains=q) | 
            Q(description__icontains=q)
        ).select_related('module', 'module__course').distinct().order_by('title')[:3]
        
        for lesson in lessons:
            items.append({
                'type': 'lesson', 
                'id': lesson.id, 
                'label': f"Leçon: {lesson.title} - {lesson.module.course.title}", 
                'url': reverse('courses:lesson_detail', args=[lesson.id])
            })
    
    return JsonResponse({'items': items})


# -------- Trainer helper APIs (JSON) --------
@login_required
@user_passes_test(is_formateur)
def api_my_courses(request):
    qs = Course.objects.filter(created_by=request.user).order_by('title').values('id', 'title')
    return JsonResponse({'courses': list(qs)})


@login_required
@user_passes_test(is_formateur)
def api_modules_for_course(request, course_id):
    course = get_object_or_404(Course, id=course_id, created_by=request.user)
    qs = course.modules.order_by('id').values('id', 'title')
    return JsonResponse({'modules': list(qs)})

@login_required
@user_passes_test(is_formateur)
def api_lessons_for_module(request, module_id):
    module = get_object_or_404(Module, id=module_id, course__created_by=request.user)
    qs = module.lessons.order_by('order', 'id').values('id', 'title')
    return JsonResponse({'lessons': list(qs)})

@require_http_methods(['POST'])
@login_required
def api_create_lesson(request):
    """
    API pour créer une nouvelle leçon dans un module existant.
    Attend un formulaire avec :
    - module_id: ID du module parent
    - title: Titre de la leçon
    - description: Description de la leçon (optionnel)
    - order: Ordre de la leçon (optionnel)
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f'Début création leçon - Données reçues: {request.POST}')
        
        # Vérifier si l'utilisateur est un formateur ou un administrateur
        if request.user.role not in ['trainer', 'admin']:
            error_msg = 'Accès refusé. Formateur requis.'
            logger.warning(f'Accès refusé - User: {request.user}')
            return JsonResponse(
                {'success': False, 'error': error_msg}, 
                status=403
            )
        
        module_id = request.POST.get('module_id')
        logger.info(f'Module ID reçu: {module_id}')
        
        if not module_id:
            error_msg = 'ID du module manquant'
            logger.error(error_msg)
            return JsonResponse(
                {'success': False, 'error': error_msg}, 
                status=400
            )
            
        try:
            module = Module.objects.get(id=module_id)
            logger.info(f'Module trouvé: {module.title} (ID: {module.id})')
        except Module.DoesNotExist:
            error_msg = f'Module avec ID {module_id} non trouvé'
            logger.error(error_msg)
            return JsonResponse(
                {'success': False, 'error': error_msg}, 
                status=404
            )
        
        # Vérifier que l'utilisateur a le droit de modifier ce module
        if module.course.created_by != request.user and request.user.role != 'admin':
            error_msg = f'Utilisateur non autorisé à modifier ce module. Créateur: {module.course.created_by}, Utilisateur: {request.user}'
            logger.warning(error_msg)
            return JsonResponse(
                {'success': False, 'error': 'Non autorisé à modifier ce module'}, 
                status=403
            )
        
        # Récupérer et valider les données
        title = request.POST.get('title', 'Nouvelle leçon')
        description = request.POST.get('description', '')
        order = request.POST.get('order')
        
        # Déterminer l'ordre si non fourni
        if not order:
            order = module.lessons.count() + 1
            logger.info(f'Ordre non fourni, utilisation de: {order}')
        
        logger.info(f'Création leçon avec - Titre: {title}, Ordre: {order}')
        
        # Créer la leçon
        lesson = Lesson(
            module=module,
            title=title,
            description=description,
            order=order
        )
        
        # Valider le modèle
        try:
            lesson.full_clean()
        except ValidationError as e:
            error_msg = f'Erreur de validation: {e}'
            logger.error(error_msg)
            return JsonResponse(
                {'success': False, 'error': 'Données invalides', 'details': str(e)}, 
                status=400
            )
        
        # Sauvegarder la leçon
        lesson.save()
        logger.info(f'Leçon créée avec succès - ID: {lesson.id}')
        
        return JsonResponse({
            'success': True,
            'lesson': {
                'id': lesson.id,
                'title': lesson.title,
                'order': lesson.order
            }
        })
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f'Erreur lors de la création de la leçon: {str(e)}\n{error_trace}')
        return JsonResponse(
            {'success': False, 'error': f'Erreur serveur: {str(e)}'}, 
            status=500
        )

@login_required
def module_list(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    is_enrolled = Enrollment.objects.filter(user=request.user, course=course).exists()
    if not is_enrolled:
        messages.error(request, "Vous devez être inscrit pour accéder aux modules.")
        return redirect('courses:course_detail', course_id=course.id)

    modules = course.modules.all()
    return render(request, 'courses/module_list.html', {
        'course': course,
        'modules': modules,
    })


# @require_http_methods(["POST"])
# @login_required
# def mark_lesson_completed(request, lesson_id):
#     from django.db import transaction
#     from django.utils import timezone
#     from django.http import JsonResponse
#     from django.db.models import Count, Q
#     from django.contrib import messages
    
#     try:
#         with transaction.atomic():
#             # Récupérer la leçon active avec ses relations
#             lesson = get_object_or_404(
#                 Lesson.objects.select_related('module', 'module__course'),
#                 id=lesson_id,
#                 is_active=True  # Ne traiter que les leçons actives
#             )
            
#             course = lesson.module.course
#             module = lesson.module
            
#             # Vérifier que l'utilisateur est inscrit au cours
#             if not Enrollment.objects.filter(
#                 user=request.user, 
#                 course=course
#             ).exists():
#                 return JsonResponse({
#                     'status': 'error',
#                     'message': 'Vous devez être inscrit à ce cours pour marquer des leçons comme terminées.'
#                 }, status=403)
                
#             # Vérifier si le module est verrouillé (sauf pour le premier module)
#             if module.is_locked and module.order > 1:
#                 return JsonResponse({
#                     'status': 'error',
#                     'message': 'Ce module est verrouillé. Terminez d\'abord le module précédent.'
#                 }, status=403)
            
#             # Vérifier si la leçon est déjà marquée comme terminée
#             progress, created = LessonProgress.objects.get_or_create(
#                 user=request.user,
#                 lesson=lesson,
#                 defaults={'is_completed': True, 'completed_at': timezone.now()}
#             )
            
#             # Si la leçon est déjà marquée comme terminée, retourner 204 No Content
#             if progress.is_completed and not created:
#                 from django.http import HttpResponse
#                 return HttpResponse(status=204)
            
#             # Basculer l'état de complétion
#             progress.is_completed = True
#             progress.completed_at = timezone.now()
#             progress.save()
            
#             # Si la leçon est marquée comme terminée, vérifier le déverrouillage du module suivant
#             if progress.is_completed:
#                 from exercices.views_quiz import QuizView
#                 quiz_view = QuizView()
#                 quiz_view._check_module_completion(request.user, module)
            
#             # Récupérer tous les modules du cours avec le nombre de leçons
#             modules = course.modules.annotate(
#                 total_lessons=Count('lessons'),
#                 completed_lessons=Count(
#                     'lessons',
#                     filter=Q(lessons__lessonprogress__user=request.user, 
#                            lessons__lessonprogress__is_completed=True)
#                 )
#             )
            
#             # Calculer la progression globale du cours
#             total_lessons = sum(m.total_lessons for m in modules)
#             completed_lessons = sum(m.completed_lessons for m in modules)
            
#             # Vérifier si le cours est maintenant terminé
#             course_completed = (completed_lessons == total_lessons)
            
#             # Mettre à jour l'achèvement du cours si nécessaire
#             if course_completed and progress.is_completed:
#                 CourseCompletion.objects.get_or_create(
#                     user=request.user,
#                     course=course,
#                     defaults={'completed_at': timezone.now()}
#                 )
#             elif not progress.is_completed:
#                 # Si on décoche une leçon, supprimer l'achèvement du cours s'il existe
#                 CourseCompletion.objects.filter(
#                     user=request.user,
#                     course=course
#                 ).delete()
            
#             # Préparer les données de progression des modules
#             modules_progress = []
#             for m in modules:
#                 module_completed = (m.completed_lessons == m.total_lessons)
#                 modules_progress.append({
#                     'id': m.id,
#                     'title': m.title,
#                     'completed': module_completed,
#                     'completed_lessons': m.completed_lessons,
#                     'total_lessons': m.total_lessons,
#                     'progress_percent': int((m.completed_lessons / m.total_lessons * 100)) if m.total_lessons > 0 else 0
#                 })
            
#             # Calculer la progression globale en pourcentage
#             progress_percent = int((completed_lessons / total_lessons * 100)) if total_lessons > 0 else 0
            
#             # Préparer la réponse simplifiée
#             response_data = {
#                 'status': 'success',
#                 'completed': progress.is_completed,
#                 'message': 'Progression mise à jour avec succès.'
#             }
            
#             # Retourner une réponse JSON avec le bon Content-Type
#             from django.http import JsonResponse
#             response = JsonResponse(response_data)
#             response['X-Requested-With'] = 'XMLHttpRequest'  # Aide à identifier les requêtes AJAX
#             return response
            
#     except Lesson.DoesNotExist:
#         return JsonResponse({
#             'status': 'error',
#             'message': 'Leçon non trouvée.'
#         }, status=404)
#     except Exception as e:
#         return JsonResponse({
#             'status': 'error',
#             'message': 'Une erreur est survenue lors de la mise à jour de la progression.'
#         }, status=500)

@login_required
def course_completed_view(request, course_id):
    """
    Page de succès quand un cours est terminé
    """
    course = get_object_or_404(Course, id=course_id)
    
    # Vérifier que l'utilisateur a bien terminé ce cours
    if not CourseCompletion.objects.filter(user=request.user, course=course).exists():
        messages.warning(request, "Vous devez d'abord terminer toutes les leçons de ce cours.")
        return redirect('courses:course_detail', course_id)
    
    # Calculer les statistiques
    total_lessons = Lesson.objects.filter(module__course=course).count()
    completed_lessons = LessonProgress.objects.filter(
        user=request.user,
        lesson__module__course=course,
        is_fully_completed=True
    ).count()
    
    # Récupérer le temps passé
    try:
        learning_path = request.user.learning_path
        time_spent = learning_path.time_spent
    except:
        time_spent = None
    
    # Trouver le cours suivant
    next_course = course.get_next_course(request.user.structure)
    
    context = {
        'course': course,
        'total_lessons': total_lessons,
        'completed_lessons': completed_lessons,
        'time_spent': time_spent,
        'next_course': next_course,
    }
    
    return render(request, 'courses/course_completed.html', context)


@login_required
@require_POST
def mark_lesson_completed(request, lesson_id):
    from django.db import transaction
    from django.utils import timezone
    from django.http import JsonResponse
    from django.db.models import Count, Q
    from django.contrib import messages
    
    print(f"DEBUG mark_lesson_completed: lesson_id={lesson_id}, user={request.user.username}")  # Debug
    
    # Écrire dans un fichier de log
    with open('debug_log.txt', 'a', encoding='utf-8') as f:
        f.write(f"DEBUG mark_lesson_completed: lesson_id={lesson_id}, user={request.user.username}\n")
    
    try:
        with transaction.atomic():
            # Récupérer la leçon active avec ses relations
            lesson = get_object_or_404(
                Lesson.objects.select_related('module', 'module__course'),
                id=lesson_id,
                is_active=True
            )
            
            course = lesson.module.course
            module = lesson.module
            
            print(f"DEBUG: lesson={lesson.title}, module={module.title}, course={course.title}")  # Debug
            with open('debug_log.txt', 'a', encoding='utf-8') as f:
                f.write(f"DEBUG: lesson={lesson.title}, module={module.title}, course={course.title}\n")
            
            # Vérifier que l'utilisateur est inscrit au cours
            if not Enrollment.objects.filter(
                user=request.user, 
                course=course
            ).exists():
                print("DEBUG: Utilisateur non inscrit")  # Debug
                return JsonResponse({
                    'status': 'error',
                    'message': 'Vous devez être inscrit à ce cours pour marquer des leçons comme terminées.'
                }, status=403)
                
            # Vérifier si le module est verrouillé (sauf pour le premier module)
            if module.is_locked and module.order > 1:
                print("DEBUG: Module verrouillé")  # Debug
                # Vérifier si l'utilisateur a un accès individuel à ce module
                from payments.models import ModuleAccess
                access = ModuleAccess.objects.filter(
                    user=request.user,
                    module=lesson.module,
                    is_active=True
                ).first()
                
                if not access:
                    print("DEBUG: Pas d'accès ModuleAccess")  # Debug
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Vous devez d\'abord terminer le module précédent pour accéder à ce module.'
                    }, status=403)
                else:
                    print("DEBUG: Accès ModuleAccess trouvé")  # Debug
            
            # Créer ou mettre à jour la progression de la leçon
            progress, created = LessonProgress.objects.get_or_create(
                user=request.user,
                lesson=lesson
            )
            
            # Basculer l'état de complétion
            if progress.is_completed:
                progress.is_completed = False
                progress.completed_at = None
                action = 'unmarked'
            else:
                progress.is_completed = True
                progress.completed_at = timezone.now()
                action = 'marked'
            progress.save()
            
            # Mettre à jour la progression du module
            from exercices.views_quiz import QuizView
            quiz_view = QuizView()
            print("DEBUG: Appel de _check_module_completion")  # Debug
            quiz_view._check_module_completion(request, module, request.user)
            print("DEBUG: _check_module_completion terminé")  # Debug
            
            # Calculer la progression globale
            modules = course.modules.annotate(
                total_lessons=Count('lessons'),
                completed_lessons=Count(
                    'lessons',
                    filter=Q(lessons__lessonprogress__user=request.user, 
                           lessons__lessonprogress__is_completed=True)
                )
            )
            
            total_lessons = sum(m.total_lessons for m in modules)
            completed_lessons = sum(m.completed_lessons for m in modules)
            
            # Mettre à jour l'achèvement du cours si nécessaire
            if completed_lessons == total_lessons and progress.is_completed:
                CourseCompletion.objects.get_or_create(
                    user=request.user,
                    course=course,
                    defaults={'completed_at': timezone.now()}
                )
                
                # Rediriger vers la page de succès du cours terminé
                return JsonResponse({
                    'status': 'success',
                    'action': action,
                    'completed': progress.is_completed,
                    'course_completed': True,
                    'redirect_url': f'/courses/{course.id}/completed/'
                })
            elif not progress.is_completed:
                CourseCompletion.objects.filter(
                    user=request.user,
                    course=course
                ).delete()
            
            # Préparer la réponse
            response_data = {
                'status': 'success',
                'action': action,
                'completed': progress.is_completed,
                'course_completed': (completed_lessons == total_lessons)
            }
            
            return JsonResponse(response_data)
            
    except Exception as e:
        print(f"ERROR mark_lesson_completed: {str(e)}")  # Debug
        import traceback
        print(f"TRACEBACK: {traceback.format_exc()}")  # Debug
        
        # Écrire dans le fichier de log
        with open('debug_log.txt', 'a', encoding='utf-8') as f:
            f.write(f"ERROR mark_lesson_completed: {str(e)}\n")
            f.write(f"TRACEBACK: {traceback.format_exc()}\n")
        
        return JsonResponse({
            'status': 'error',
            'message': 'Une erreur est survenue lors de la mise à jour de la progression.'
        }, status=500)


@login_required
@require_POST
def mark_module_completed(request, course_id, module_id):
    module = get_object_or_404(Module, id=module_id, course__id=course_id)

    if not Enrollment.objects.filter(user=request.user, course=module.course).exists():
        messages.error(request, "Vous devez être inscrit pour marquer ce module terminé.")
        return redirect('courses:course_detail', course_id=course_id)

    from .models import LessonProgress
    lesson_ids = list(module.lessons.values_list('id', flat=True))
    for lid in lesson_ids:
        lp, _ = LessonProgress.objects.get_or_create(user=request.user, lesson_id=lid)
        if not lp.is_completed:
            lp.is_completed = True
            lp.save(update_fields=['is_completed'])

    messages.success(request, "Module marqué comme terminé.")
    return redirect('courses:course_detail', course_id=course_id)

@require_http_methods(["POST"])
@login_required
def mark_course_completed(request, course_id):
    from django.http import JsonResponse
    from django.views.decorators.csrf import csrf_exempt
    from .models import CourseCompletion, LessonProgress
    from django.db import transaction
    
    # Initialize is_ajax at the start of the function
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    try:
        course = Course.objects.get(id=course_id)
        
        # Vérifier que l'utilisateur est inscrit au cours
        if not Enrollment.objects.filter(user=request.user, course=course).exists():
            if is_ajax:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Vous devez être inscrit pour marquer ce cours comme terminé.'
                }, status=403)
            messages.error(request, "Vous devez être inscrit pour marquer ce cours comme terminé.")
            return redirect('courses:course_detail', course_id=course_id)
        
        with transaction.atomic():
            # Vérifier si le cours est déjà marqué comme terminé
            completion, created = CourseCompletion.objects.get_or_create(
                user=request.user,
                course=course
            )
            
            if not created:
                # Si le cours était déjà marqué comme terminé, on le marque comme non terminé
                completion.delete()
                is_completed = False
                message = "Le cours n'est plus marqué comme terminé."
                progress_percent = 0
                total_lessons = Lesson.objects.filter(module__course=course).count()
            else:
                # Marquer toutes les leçons du cours comme terminées
                lessons = Lesson.objects.filter(module__course=course)
                total_lessons = lessons.count()
                
                for lesson in lessons:
                    LessonProgress.objects.update_or_create(
                        user=request.user,
                        lesson=lesson,
                        defaults={'is_completed': True}
                    )
                
                is_completed = True
                message = "Le cours a été marqué comme terminé avec succès."
                progress_percent = 100
        
        # Préparer la réponse
        response_data = {
            'status': 'success',
            'completed': is_completed,
            'message': message,
            'progress': {
                'completed': total_lessons if is_completed else 0,
                'total': total_lessons,
                'percent': progress_percent
            }
        }
        
        if is_ajax:
            return JsonResponse(response_data)
            
        messages.success(request, message)
        return redirect('courses:course_detail', course_id=course_id)
        
    except Course.DoesNotExist:
        error_message = 'Cours non trouvé.'
        if is_ajax:
            return JsonResponse({
                'status': 'error',
                'message': error_message
            }, status=404)
        messages.error(request, error_message)
        return redirect('courses:all_courses')
        
    except Exception as e:
        error_message = f'Une erreur est survenue: {str(e)}'
        if is_ajax:
            return JsonResponse({
                'status': 'error',
                'message': error_message
            }, status=500)
        messages.error(request, error_message)
        return redirect('courses:course_detail', course_id=course_id)

@login_required
@user_passes_test(is_formateur)
@require_http_methods(["GET", "POST"])
def unified_course_creation(request, course_id=None):
    """
    Vue unifiée pour la création et la modification de cours avec modules, leçons et vidéos.
    
    Args:
        request: La requête HTTP
        course_id: L'ID du cours à modifier (optionnel)
    """
    logger = logging.getLogger(__name__)
    course = None
    categories = Category.objects.all()
    
    # Mode édition si un ID de cours est fourni
    if course_id:
        course = get_object_or_404(Course, id=course_id)
        # Vérifier que l'utilisateur est bien le créateur du cours
        if course.created_by != request.user and not request.user.is_superuser:
            raise PermissionDenied("Vous n'avez pas la permission de modifier ce cours.")
    
    if request.method == 'POST':
        try:
            action = "modification" if course_id else "création"
            logger.info(f"Tentative de {action} d'un cours")
            
            # Récupérer les données du formulaire
            data = request.POST
            files = request.FILES
            
            # Journalisation des données reçues (sans les fichiers pour éviter les problèmes de sérialisation)
            logger.debug(f"Données POST reçues: {dict(data.items())}")
            
            # 1. Préparer les données du cours
            course_data = {
                'title': data.get('title'),
                'description': data.get('description'),
                'category': data.get('category'),
                'language': data.get('language', 'fr'),
                'is_published': False,
            }
            
            # Si c'est une création, on ajoute l'instructeur
            if not course_id:
                course_data['instructor'] = request.user.id
            
            # Gérer la miniature si fournie
            if 'thumbnail' in files:
                course_data['thumbnail'] = files['thumbnail']
            
            logger.debug(f"Données du cours: {course_data}")
            
            # Initialiser le formulaire avec ou sans instance existante
            course_form = CourseForm(course_data, files, instance=course) if course else CourseForm(course_data, files)
            
            if course_form.is_valid():
                logger.info("Formulaire de cours valide")
                
                try:
                    with transaction.atomic():
                        # Sauvegarder le cours
                        course = course_form.save(commit=False)
                        if not course_id:  # Nouveau cours
                            course.created_by = request.user
                        course.save()  # Utiliser save() normal pour la mise à jour
                        
                        logger.info(f"Cours créé avec l'ID: {course.id}")
                        
                        # 2. Traiter les données des modules, leçons et vidéos
                        modules_data = json.loads(data.get('modules_data', '[]'))
                        logger.debug(f"Données des modules: {modules_data}")
                        
                        for module_idx, module_data in enumerate(modules_data, 1):
                            # Créer le module
                            module = Module.objects.create(
                                course=course,
                                title=module_data.get('title', f'Module {module_idx}'),
                                description=module_data.get('description', ''),
                                order=module_data.get('order', module_idx)
                            )
                            
                            logger.debug(f"Module créé: {module.title} (ID: {module.id})")
                            
                            # Créer les leçons du module
                            for lesson_idx, lesson_data in enumerate(module_data.get('lessons', []), 1):
                                lesson = Lesson.objects.create(
                                    module=module,
                                    title=lesson_data.get('title', f'Leçon {lesson_idx}'),
                                    description=lesson_data.get('description', ''),
                                    order=lesson_data.get('order', lesson_idx)
                                )
                                
                                logger.debug(f"Leçon créée: {lesson.title} (ID: {lesson.id})")
                                
                                # Créer les vidéos de la leçon
                                for video_idx, video_data in enumerate(lesson_data.get('videos', []), 1):
                                    # Pour les fichiers, on les récupère depuis request.FILES
                                    video_file = None
                                    video_file_key = f"modules-{module_idx-1}-lessons-{lesson_idx-1}-videos-{video_idx-1}-video_file"
                                    
                                    if video_file_key in files:
                                        video_file = files[video_file_key]
                                        logger.debug(f"Fichier vidéo trouvé pour la clé: {video_file_key}")
                                    
                                    try:
                                        # Debug logging for video data
                                        duration_value = video_data.get('duration', 0)
                                        logger.debug(f"Raw duration value: {duration_value}, type: {type(duration_value)}")
                                        
                                        # Convert duration to integer and create timedelta
                                        try:
                                            duration_seconds = int(duration_value) if duration_value else 0
                                            duration_timedelta = timedelta(seconds=duration_seconds)
                                            logger.debug(f"Converted duration: {duration_timedelta}")
                                            
                                            # Création de l'entrée LessonVideo
                                            video = LessonVideo.objects.create(
                                                lesson=lesson,
                                                title=video_data.get('title', f'Vidéo {video_idx}'),
                                                video_file=video_file,
                                                duration=duration_timedelta,
                                                order=video_data.get('order', video_idx)
                                            )
                                            logger.debug(f"Vidéo créée: {video.title} (ID: {video.id})")
                                            
                                        except (ValueError, TypeError) as ve:
                                            logger.error(f"Erreur de conversion de la durée: {str(ve)}")
                                            # Fallback to None if duration is invalid
                                            video = LessonVideo.objects.create(
                                                lesson=lesson,
                                                title=video_data.get('title', f'Vidéo {video_idx}'),
                                                video_file=video_file,
                                                duration=None,
                                                order=video_data.get('order', video_idx)
                                            )
                                            
                                    except Exception as e:
                                        logger.error(f"Erreur lors de la création de la vidéo: {str(e)}")
                                        logger.error(traceback.format_exc())
                                        raise
                    
                    # Si c'est une requête AJAX, retourner une réponse JSON
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': True,
                            'redirect_url': reverse('courses:manage')
                        })
                    
                    messages.success(request, 'Le cours a été créé avec succès !')
                    return redirect('courses:manage')
                    
                except json.JSONDecodeError as e:
                    error_msg = f"Erreur de format des données des modules: {str(e)}"
                    logger.error(error_msg)
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': False,
                            'error': error_msg
                        }, status=400)
                    messages.error(request, error_msg)
                    
                except Exception as e:
                    error_msg = f"Erreur lors de la création du cours: {str(e)}"
                    logger.exception(error_msg)
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': False,
                            'error': error_msg
                        }, status=500)
                    messages.error(request, error_msg)
                    
            else:
                # Si le formulaire n'est pas valide, renvoyer les erreurs
                error_msg = "Le formulaire contient des erreurs. Veuillez vérifier les champs."
                logger.warning(f"Erreurs de validation du formulaire: {course_form.errors}")
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'errors': course_form.errors,
                        'error': error_msg
                    }, status=400)
                
                messages.error(request, error_msg)
                
        except Exception as e:
            # En cas d'erreur inattendue
            error_msg = f"Une erreur inattendue est survenue: {str(e)}"
            logger.exception(error_msg)
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': error_msg
                }, status=500)
            
            messages.error(request, error_msg)
    
    # Vérifier si on est en mode édition
    course = None
    if 'course_id' in request.resolver_match.kwargs:
        course_id = request.resolver_match.kwargs['course_id']
        try:
            course = Course.objects.get(id=course_id, created_by=request.user)
            # Préparer les données pour le formulaire
            initial_data = {
                'title': course.title,
                'description': course.description,
                'category': course.category.id if course.category else None,
                'language': course.language,
                'thumbnail': course.thumbnail
            }
            # Récupérer les modules, leçons et vidéos existants
            modules = course.modules.all().order_by('order')
            modules_data = []
            
            for module in modules:
                module_info = {
                    'id': module.id,
                    'title': module.title,
                    'description': module.description or '',
                    'order': module.order,
                    'lessons': []
                }
                
                # Récupérer les leçons du module
                lessons = module.lessons.all().order_by('order')
                for lesson in lessons:
                    lesson_info = {
                        'id': lesson.id,
                        'title': lesson.title,
                        'description': lesson.description or '',
                        'order': lesson.order,
                        'content_file': lesson.content_file.url if lesson.content_file else None,
                        'videos': []
                    }
                    
                    # Récupérer les vidéos de la leçon
                    videos = lesson.videos.all().order_by('order')
                    for video in videos:
                        video_info = {
                            'id': video.id,
                            'title': video.title,
                            'video_file': video.video_file.url if video.video_file else None,
                            'order': video.order
                        }
                        lesson_info['videos'].append(video_info)
                    
                    module_info['lessons'].append(lesson_info)
                
                modules_data.append(module_info)
            
            # Convertir en JSON pour le JavaScript (utilise l'import json global)
            modules_json = json.dumps(modules_data, ensure_ascii=False)
            
            course_form = CourseForm(initial=initial_data, instance=course)
            return render(request, 'courses/unified_course_creation.html', {
                'categories': categories,
                'course_form': course_form,
                'course': course,
                'modules_json': modules_json,
                'title': f'Modifier le cours: {course.title}'
            })
        except Course.DoesNotExist:
            messages.error(request, "Le cours demandé n'existe pas ou vous n'avez pas les droits pour le modifier.")
            return redirect('courses:manage')
    
    # Préparer le formulaire pour l'affichage
    form = CourseForm(instance=course) if course else CourseForm()
    
    # Si c'est une requête GET ou en cas d'erreur, afficher le formulaire
    return render(request, 'courses/unified_course_creation.html', {
        'categories': categories,
        'course_form': form,
        'course': course,
        'title': f"Modifier le cours: {course.title}" if course else 'Créer un nouveau cours'
    })

@login_required
@user_passes_test(is_formateur)
def course_delete(request, course_id):
    """
    Vue pour supprimer un cours existant.
    """
    if request.method == 'POST':
        try:
            course = get_object_or_404(Course, id=course_id, created_by=request.user)
            course_title = course.title
            course.delete()
            messages.success(request, f'Le cours "{course_title}" a été supprimé avec succès.')
            return redirect('courses:manage')
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du cours: {str(e)}")
            messages.error(request, 'Une erreur est survenue lors de la suppression du cours.')
            return redirect('courses:manage')
    
    # Si ce n'est pas une requête POST, rediriger vers la liste des cours
    return redirect('courses:manage')

@login_required
def api_create_video(request):
    """
    Vue pour créer une nouvelle vidéo pour une leçon existante.
    Gère à la fois les requêtes AJAX et les requêtes normales.
    
    Attend un formulaire avec :
    - lesson_id: ID de la leçon parente
    - title: Titre de la vidéo
    - video_file: Fichier vidéo à téléverser
    - order: Ordre de la vidéo (optionnel, par défaut 1)
    """
    logger = logging.getLogger(__name__)
    
    # Vérifier que l'utilisateur est un formateur ou un admin
    if request.user.role not in ['trainer', 'admin']:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse(
                {'success': False, 'error': 'Accès refusé. Formateur requis.'},
                status=403
            )
        messages.error(request, 'Accès refusé. Formateur requis.')
        return redirect('courses:all_courses')
    
    if request.method == 'POST':
        try:
            # Récupérer les données du formulaire
            lesson_id = request.POST.get('lesson_id')
            title = request.POST.get('title')
            order = request.POST.get('order', 1)
            video_file = request.FILES.get('video_file')
            
            # Validation des données requises
            if not all([lesson_id, title, video_file]):
                error_msg = 'Tous les champs obligatoires doivent être remplis.'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse(
                        {'success': False, 'error': error_msg},
                        status=400
                    )
                messages.error(request, error_msg)
                return redirect(request.META.get('HTTP_REFERER', 'courses:all_courses'))
            
            # Vérifier que la leçon existe
            try:
                lesson = Lesson.objects.get(id=lesson_id)
            except Lesson.DoesNotExist:
                error_msg = 'Leçon non trouvée.'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse(
                        {'success': False, 'error': error_msg},
                        status=404
                    )
                messages.error(request, error_msg)
                return redirect('courses:all_courses')
            
            # Vérifier que l'utilisateur a le droit de modifier ce module
            if lesson.module.course.created_by != request.user and request.user.role != 'admin':
                error_msg = 'Non autorisé à modifier cette leçon.'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse(
                        {'success': False, 'error': error_msg},
                        status=403
                    )
                messages.error(request, error_msg)
                return redirect('courses:all_courses')
            
            # Créer la vidéo
            video = LessonVideo(
                lesson=lesson,
                title=title,
                video_file=video_file,
                order=order
            )
            
            # Valider et enregistrer
            video.full_clean()
            video.save()
            
            # Message de succès
            success_msg = 'Vidéo ajoutée avec succès.'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': success_msg,
                    'video_id': video.id
                })
                
            messages.success(request, success_msg)
            return redirect('courses:manage')
            
        except Exception as e:
            logger.error(f"Erreur lors de la création de la vidéo: {str(e)}")
            error_msg = f'Erreur lors de l\'ajout de la vidéo: {str(e)}'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse(
                    {'success': False, 'error': error_msg},
                    status=500
                )
                
            messages.error(request, error_msg)
            return redirect(request.META.get('HTTP_REFERER', 'courses:all_courses'))
    
    # Si la méthode n'est pas POST, rediriger vers la page de gestion
    return redirect('courses:manage')


class CategoryDetailView(DetailView):
    model = Category
    template_name = 'courses/category_detail.html'
    context_object_name = 'category'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = self.get_object()
        
        # Récupérer tous les cours de cette catégorie
        courses = Course.objects.filter(
            category=category,
            is_published=True
        ).select_related('created_by').prefetch_related('modules', 'competences')
        
        # Filtrer par niveau si spécifié
        niveau_filter = self.request.GET.get('niveau')
        if niveau_filter:
            courses = courses.filter(niveau=niveau_filter)
        
        # Filtrer par cible si spécifié
        cible_filter = self.request.GET.get('cible')
        if cible_filter:
            courses = courses.filter(cible=cible_filter)
        
        # Calculer les statistiques
        total_courses = courses.count()
        total_modules = 0
        total_lessons = 0
        
        for course in courses:
            modules_count = course.modules.count()
            lessons_count = 0
            for module in course.modules.all():
                lessons_count += module.lessons.count()
            
            total_modules += modules_count
            total_lessons += lessons_count
        
        # Ajouter les options de filtre
        context['courses'] = courses
        context['niveau_choices'] = Course.LEVEL_CHOICES
        context['cible_choices'] = Course.CIBLE_CHOICES
        context['current_niveau'] = niveau_filter
        context['current_cible'] = cible_filter
        
        # Statistiques
        context['total_courses'] = total_courses
        context['total_modules'] = total_modules
        context['total_lessons'] = total_lessons
        
        return context
