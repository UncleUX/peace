from django.urls import path
from . import views
from .views_admin import (
    send_notification_form, 
    bulk_notification_form,
    notification_with_attachment_form,
    bulk_notification_with_attachment_form
)

app_name = 'notifications'

urlpatterns = [
    path('', views.notification_list, name='list'),
    path('<int:notification_id>/read/', views.mark_as_read, name='mark_read'),
    path('<int:notification_id>/delete/', views.delete_notification, name='delete'),
    path('delete-selected/', views.delete_selected_notifications, name='delete_selected'),
    path('mark-all-read/', views.mark_all_as_read, name='mark_all_read'),
    path('clear-all/', views.clear_all_notifications, name='clear_all'),
    
    # URLs admin pour envoyer des notifications
    path('send/', send_notification_form, name='send_notification_form'),
    path('bulk/', bulk_notification_form, name='bulk_notification_form'),
    path('send-with-attachment/', notification_with_attachment_form, name='notification_with_attachment_form'),
    path('bulk-with-attachment/', bulk_notification_with_attachment_form, name='bulk_notification_with_attachment_form'),
]