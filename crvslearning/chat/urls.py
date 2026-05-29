from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    # Vues principales
    path('', views.chat_list, name='list'),
    path('room/<int:room_id>/', views.chat_room, name='room'),
    path('room/<int:room_id>/simple/', views.chat_room_simple, name='room_simple'),
    path('room/<int:room_id>/send/', views.send_message, name='send_message'),
    path('create/', views.create_room, name='create'),
    path('room/<int:room_id>/edit/', views.edit_room, name='edit'),
    
    # Gestion des participants
    path('room/<int:room_id>/add-participant/', views.add_participant, name='add_participant'),
    path('room/<int:room_id>/remove-participant/', views.remove_participant, name='remove_participant'),
    
    # Gestion des messages
    path('room/<int:room_id>/upload/', views.upload_attachment, name='upload'),
    path('message/<int:message_id>/delete/', views.delete_message, name='delete_message'),
    path('message/<int:message_id>/edit/', views.edit_message, name='edit_message'),
    path('room/<int:room_id>/mark-read/', views.mark_messages_read, name='mark_read'),
    
    # API
    path('search-users/', views.search_users, name='search_users'),
    path('online-users/', views.online_users, name='online_users'),
    
    # API pour le temps réel (polling)
    path('conversation/<int:user_id>/new-messages/', views.get_new_messages, name='get_new_messages'),
    path('conversation/<int:user_id>/send-message/', views.send_message_ajax, name='send_message_ajax'),
]
