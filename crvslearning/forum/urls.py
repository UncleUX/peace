from django.urls import path
from . import views

app_name = 'forum'

urlpatterns = [
    path('', views.ForumHomeView.as_view(), name='home'),
    path('question/<int:pk>/', views.QuestionDetailView.as_view(), name='question_detail'),
    path('create/', views.CreateQuestionView.as_view(), name='create_question'),
    path('answer/<int:pk>/', views.answer_question, name='answer_question'),
    path('vote-question/<int:pk>/', views.vote_question, name='vote_question'),
    path('vote/<int:pk>/', views.vote_answer, name='vote_answer'),
    path('validate/<int:pk>/', views.validate_answer, name='validate_answer'),
    path('close/<int:pk>/', views.close_question, name='close_question'),
    path('delete-question/<int:pk>/', views.delete_question, name='delete_question'),
    path('delete-answer/<int:pk>/', views.delete_answer, name='delete_answer'),
    path('comment/<int:answer_id>/', views.comment_answer, name='comment_answer'),
]
