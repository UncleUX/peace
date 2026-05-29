from django.shortcuts import get_object_or_404, render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q
import json
from datetime import timedelta

from .models import Lesson, LessonProgress, Quiz, QuizAttempt, CourseResult


@login_required
@require_POST
def update_lesson_progress(request, lesson_id):
    """Met à jour la progression d'une leçon (pour le suivi vidéo)"""
    lesson = get_object_or_404(Lesson, id=lesson_id)
    
    # Créer ou récupérer la progression
    progress, created = LessonProgress.objects.get_or_create(
        user=request.user,
        lesson=lesson,
        defaults={
            'watch_percentage': 0.0,
            'watch_time': timedelta(0)
        }
    )
    
    # Récupérer les données du POST
    try:
        data = json.loads(request.body)
        watch_percentage = float(data.get('percentage', 0))
        watch_time_seconds = int(data.get('watch_time', 0))
        last_position = int(data.get('last_position', 0))
        
        # Mettre à jour la progression
        progress.watch_percentage = min(watch_percentage, 100.0)
        progress.watch_time = timedelta(seconds=watch_time_seconds)
        
        # Vérifier si on atteint 80% pour la complétion automatique
        if watch_percentage >= 80 and not progress.auto_completed:
            progress.auto_completed = True
            progress.auto_completed_at = timezone.now()
            
            # Calculer la complétion complète
            progress.calculate_completion()
            
            # Mettre à jour le résultat du cours
            update_course_result(request.user, lesson.module.course)
            
            return JsonResponse({
                'success': True,
                'auto_completed': True,
                'fully_completed': progress.is_fully_completed,
                'message': 'Leçon complétée automatiquement à 80%'
            })
        
        progress.save()
        
        return JsonResponse({
            'success': True,
            'watch_percentage': progress.watch_percentage,
            'auto_completed': progress.auto_completed,
            'fully_completed': progress.is_fully_completed
        })
        
    except (json.JSONDecodeError, ValueError) as e:
        return JsonResponse({
            'success': False,
            'error': 'Données invalides'
        }, status=400)


@login_required
@require_POST
def mark_lesson_manually_completed(request, lesson_id):
    """Marque une leçon comme terminée manuellement"""
    lesson = get_object_or_404(Lesson, id=lesson_id)
    
    progress, created = LessonProgress.objects.get_or_create(
        user=request.user,
        lesson=lesson
    )
    
    # Marquer comme complété manuellement
    progress.manually_marked = True
    progress.manually_marked_at = timezone.now()
    
    # Calculer la complétion complète
    was_fully_completed = progress.is_fully_completed
    progress.calculate_completion()
    
    # Mettre à jour le résultat du cours si nouvellement complété
    if not was_fully_completed and progress.is_fully_completed:
        update_course_result(request.user, lesson.module.course)
    
    return JsonResponse({
        'success': True,
        'fully_completed': progress.is_fully_completed,
        'completion_percentage': progress.get_completion_percentage(),
        'message': 'Leçon marquée comme terminée avec succès'
    })


@login_required
def get_lesson_progress(request, lesson_id):
    """Retourne la progression actuelle d'une leçon"""
    lesson = get_object_or_404(Lesson, id=lesson_id)
    
    try:
        progress = LessonProgress.objects.get(user=request.user, lesson=lesson)
        
        return JsonResponse({
            'success': True,
            'watch_percentage': progress.watch_percentage,
            'auto_completed': progress.auto_completed,
            'manually_marked': progress.manually_marked,
            'fully_completed': progress.is_fully_completed,
            'completion_percentage': progress.get_completion_percentage(),
            'watch_time': str(progress.watch_time) if progress.watch_time else None
        })
        
    except LessonProgress.DoesNotExist:
        return JsonResponse({
            'success': True,
            'watch_percentage': 0.0,
            'auto_completed': False,
            'manually_marked': False,
            'fully_completed': False,
            'completion_percentage': 0.0,
            'watch_time': None
        })


@login_required
def get_course_progress(request, course_id):
    """Retourne la progression complète d'un cours"""
    course = get_object_or_404(Course, id=course_id)
    
    # Récupérer le résultat du cours
    result = course.calculate_user_result(request.user)
    details = result.get_progress_details()
    
    # Récupérer la progression détaillée des leçons
    lessons = Lesson.objects.filter(module__course=course)
    lesson_progress = []
    
    for lesson in lessons:
        try:
            progress = LessonProgress.objects.get(user=request.user, lesson=lesson)
            lesson_progress.append({
                'lesson_id': lesson.id,
                'lesson_title': lesson.title,
                'watch_percentage': progress.watch_percentage,
                'auto_completed': progress.auto_completed,
                'manually_marked': progress.manually_marked,
                'fully_completed': progress.is_fully_completed,
                'completion_percentage': progress.get_completion_percentage()
            })
        except LessonProgress.DoesNotExist:
            lesson_progress.append({
                'lesson_id': lesson.id,
                'lesson_title': lesson.title,
                'watch_percentage': 0.0,
                'auto_completed': False,
                'manually_marked': False,
                'fully_completed': False,
                'completion_percentage': 0.0
            })
    
    return JsonResponse({
        'success': True,
        'course': {
            'id': course.id,
            'title': course.title,
            'total_lessons': details['total_lessons'],
            'completed_lessons': details['completed_lessons'],
            'total_quizzes': details['total_quizzes'],
            'passed_quizzes': details['passed_quizzes']
        },
        'result': {
            'lesson_score': result.lesson_score,
            'quiz_score': result.quiz_score,
            'final_score': result.final_score,
            'is_passed': result.is_passed,
            'started_at': result.started_at.isoformat(),
            'completed_at': result.completed_at.isoformat() if result.completed_at else None
        },
        'lesson_progress': lesson_progress
    })


@login_required
@require_POST
def submit_quiz_attempt(request, quiz_id):
    """Soumet une tentative de quiz"""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    try:
        data = json.loads(request.body)
        score = int(data.get('score', 0))
        
        # Créer la tentative
        attempt = QuizAttempt.objects.create(
            quiz=quiz,
            user=request.user,
            score=score,
            completed_at=timezone.now()
        )
        
        # Mettre à jour le résultat du cours
        update_course_result(request.user, quiz.lesson.module.course)
        
        return JsonResponse({
            'success': True,
            'attempt_id': attempt.id,
            'score': attempt.score,
            'is_passed': attempt.is_passed,
            'message': 'Quiz soumis avec succès'
        })
        
    except (json.JSONDecodeError, ValueError) as e:
        return JsonResponse({
            'success': False,
            'error': 'Données invalides'
        }, status=400)


@login_required
def get_quiz_results(request, quiz_id):
    """Retourne les résultats d'un quiz pour l'utilisateur"""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    attempts = QuizAttempt.objects.filter(quiz=quiz, user=request.user).order_by('-score')
    best_attempt = attempts.first()
    
    return JsonResponse({
        'success': True,
        'quiz': {
            'id': quiz.id,
            'title': quiz.title,
            'total_questions': quiz.total_questions,
            'passing_score': quiz.passing_score
        },
        'best_score': best_attempt.score if best_attempt else 0,
        'attempts_count': attempts.count(),
        'has_passed': quiz.has_user_passed(request.user),
        'attempts': [
            {
                'id': attempt.id,
                'score': attempt.score,
                'is_passed': attempt.is_passed,
                'completed_at': attempt.completed_at.isoformat() if attempt.completed_at else None,
                'time_taken': str(attempt.time_taken) if attempt.time_taken else None
            }
            for attempt in attempts[:5]  # Limiter à 5 dernières tentatives
        ]
    })


def update_course_result(user, course):
    """Met à jour le résultat d'un cours après une progression"""
    result, created = CourseResult.objects.get_or_create(
        user=user,
        course=course,
        defaults={
            'lesson_weight': 0.3,
            'quiz_weight': 0.7,
            'passing_score': 70.0
        }
    )
    
    # Calculer les scores
    result.calculate_scores()
    return result


@login_required
def refresh_playlist_data(request, course_id):
    """Rafraîchit les données de la playlist après complétion d'une leçon"""
    course = get_object_or_404(Course, id=course_id)
    
    # Récupérer les leçons du cours avec leur statut
    lessons = Lesson.objects.filter(module__course=course).order_by('module__order', 'order')
    
    playlist_data = []
    for lesson in lessons:
        try:
            progress = LessonProgress.objects.get(user=request.user, lesson=lesson)
            is_completed = progress.is_fully_completed
        except LessonProgress.DoesNotExist:
            is_completed = False
        
        playlist_data.append({
            'id': lesson.id,
            'title': lesson.title,
            'module_title': lesson.module.title,
            'href': f"/courses/lessons/{lesson.id}/",
            'is_current': lesson.id == request.GET.get('current_lesson_id'),
            'has_video': lesson.lessonvideo_set.exists(),
            'is_completed': is_completed
        })
    
    return JsonResponse({
        'success': True,
        'playlist_data': playlist_data
    })


@login_required
def student_dashboard(request):
    """Tableau de bord de progression de l'étudiant"""
    # Récupérer tous les cours où l'étudiant est inscrit
    enrolled_courses = request.user.enrollment_set.all()
    
    course_progress = []
    for enrollment in enrolled_courses:
        course = enrollment.course
        progress_summary = course.get_user_progress_summary(request.user)
        course_progress.append(progress_summary)
    
    # Statistiques globales
    total_courses = len(course_progress)
    completed_courses = len([c for c in course_progress if c['is_passed']])
    in_progress_courses = total_courses - completed_courses
    
    # Score moyen
    if course_progress:
        average_score = sum(c['final_score'] for c in course_progress) / len(course_progress)
    else:
        average_score = 0
    
    context = {
        'course_progress': course_progress,
        'total_courses': total_courses,
        'completed_courses': completed_courses,
        'in_progress_courses': in_progress_courses,
        'average_score': round(average_score, 1)
    }
    
    return render(request, 'courses/student_dashboard.html', context)
