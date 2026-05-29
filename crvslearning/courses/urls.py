from django.urls import path
from . import views
from . import views_progress
from . import views_learning_path

app_name = 'courses'

urlpatterns = [
    path('', views.all_courses, name='all_courses'),  # page d'accueil des cours
    path('search/', views.search, name='search'),
    path('search/suggest/', views.search_suggest, name='search_suggest'),
    path('api/my-courses/', views.api_my_courses, name='api_my_courses'),
    path('api/courses/<int:course_id>/modules/', views.api_modules_for_course, name='api_modules_for_course'),
    path('api/modules/<int:module_id>/lessons/', views.api_lessons_for_module, name='api_lessons_for_module'),
    path('api/lessons/create/', views.api_create_lesson, name='api_create_lesson'),
    path('api/videos/create/', views.api_create_video, name='api_videos_create'),
    path('videos/ajouter/', views.api_create_video, name='add_video'),
    path('<int:course_id>/', views.course_detail, name='course_detail'),
    path('<int:course_id>/completed/', views.course_completed_view, name='course_completed'),
    path('<int:course_id>/enroll/', views.enroll_course, name='enroll_course'),
    path('<int:course_id>/modules/', views.module_list, name='module_list'),
    path('lessons/<int:lesson_id>/', views.lesson_detail, name='lesson_detail'),
    path('lessons/<int:lesson_id>/videos/create/', views.lesson_video_create, name='lesson_video_create'),
    path('lessons/<int:lesson_id>/complete/', views.mark_lesson_completed, name='mark_lesson_completed'),
    path('<int:course_id>/modules/<int:module_id>/complete/', views.mark_module_completed, name='mark_module_completed'),
    path('<int:course_id>/complete/', views.mark_course_completed, name='mark_course_completed'),
    path('lessons/<int:lesson_id>/comment/', views.add_comment, name='add_comment'),
    path('<int:course_id>/rate/', views.rate_course, name='rate_course'),
    path('<int:course_id>/like/', views.toggle_like, name='toggle_like'),
    path('<int:course_id>/like/ajax/', views.toggle_like_ajax, name='toggle_like_ajax'),
    
    # URL pour nettoyer les messages de session SweetAlert
    path('clear-session-message/', views.clear_session_message, name='clear_session_message'),
    
    # URL pour nettoyer les messages d'évaluation
    path('clear-evaluation-success-message/', views.clear_evaluation_success_message, name='clear_evaluation_success_message'),
    path('clear-evaluation-failure-message/', views.clear_evaluation_failure_message, name='clear_evaluation_failure_message'),

    # Vues pour formateurs (création/gestion)
    path('manage/', views.course_list, name='manage'),
    path('create/', views.course_create, name='course_create'),
    path('categories/create/', views.create_category, name='create_category'),
    path('<int:course_id>/modules/<int:module_id>/', views.module_detail, name='module_detail'),
    path('<int:course_id>/modules/create/', views.module_create, name='module_create'),
    path('<int:course_id>/modules/<int:module_id>/lessons/create/', views.lesson_create, name='lesson_create'),
    
    # URL pour la création et l'édition unifiée de cours
    path('create/unified/', views.unified_course_creation, name='unified_course_creation'),
    path('edit/<int:course_id>/', views.unified_course_creation, name='course_edit'),
    path('delete/<int:course_id>/', views.course_delete, name='course_delete'),
    
    # URL pour les catégories
    path('categories/<slug:slug>/', views.CategoryDetailView.as_view(), name='category_detail'),
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    
    # URLs pour le suivi de progression
    path('progress/lesson/<int:lesson_id>/', views_progress.get_lesson_progress, name='get_lesson_progress'),
    path('progress/lesson/<int:lesson_id>/update/', views_progress.update_lesson_progress, name='update_lesson_progress'),
    path('progress/lesson/<int:lesson_id>/mark-completed/', views_progress.mark_lesson_manually_completed, name='mark_lesson_completed'),
    path('progress/course/<int:course_id>/progress/', views_progress.get_course_progress, name='get_course_progress'),
    path('progress/course/<int:course_id>/refresh-playlist/', views_progress.refresh_playlist_data, name='refresh_playlist_data'),
    path('progress/quiz/<int:quiz_id>/submit/', views_progress.submit_quiz_attempt, name='submit_quiz_attempt'),
    path('progress/quiz/<int:quiz_id>/results/', views_progress.get_quiz_results, name='get_quiz_results'),
    path('progress/dashboard/', views_progress.student_dashboard, name='student_dashboard'),
    
    # URLs pour les parcours d'apprentissage
    path('learning-path/', views_learning_path.learning_path_dashboard, name='learning_path_dashboard'),
    path('learning-path/welcome/', views_learning_path.learning_path_welcome, name='learning_path_welcome'),
    path('learning-path/assign/', views_learning_path.assign_learning_path, name='assign_learning_path'),
    path('learning-path/goals/', views_learning_path.update_learning_goals, name='update_learning_goals'),
    path('learning-path/progress/', views_learning_path.learning_path_progress, name='learning_path_progress'),
    path('learning-path/analytics/', views_learning_path.learning_path_analytics, name='learning_path_analytics'),
    path('learning-path/comparison/', views_learning_path.LearningPathComparisonView.as_view(), name='learning_path_comparison'),
]
