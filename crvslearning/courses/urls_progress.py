from django.urls import path
from . import views_progress

app_name = 'progress'

urlpatterns = [
    # Progression des leçons
    path('lesson/<int:lesson_id>/progress/', views_progress.get_lesson_progress, name='get_lesson_progress'),
    path('lesson/<int:lesson_id>/update/', views_progress.update_lesson_progress, name='update_lesson_progress'),
    path('lesson/<int:lesson_id>/mark-completed/', views_progress.mark_lesson_manually_completed, name='mark_lesson_completed'),
    
    # Progression des cours
    path('course/<int:course_id>/progress/', views_progress.get_course_progress, name='get_course_progress'),
    
    # Quiz
    path('quiz/<int:quiz_id>/submit/', views_progress.submit_quiz_attempt, name='submit_quiz_attempt'),
    path('quiz/<int:quiz_id>/results/', views_progress.get_quiz_results, name='get_quiz_results'),
    
    # Dashboard
    path('dashboard/', views_progress.student_dashboard, name='student_dashboard'),
]
