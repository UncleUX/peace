from django.urls import path
from . import views_simple

app_name = 'chat'

urlpatterns = [
    # Messagerie unifiée - liste des conversations ou conversation spécifique
    path('', views_simple.chat_view, name='chat'),
    path('conversation/<int:user_id>/', views_simple.chat_view, name='conversation'),
    
    # API
    path('search-users/', views_simple.search_users, name='search_users'),
    path('start-conversation/', views_simple.start_conversation, name='start_conversation'),
    
    # Envoi de messages
    path('conversation/<int:user_id>/send/', views_simple.send_direct_message, name='send_message'),
    
    # Actions sur les messages
    path('conversation/mark-read/<int:message_id>/', views_simple.mark_message_read, name='mark_message_read'),
]
