from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.utils.html import format_html
from django.urls import reverse
from django.http import HttpResponseRedirect
from .models import Notification
from .views_admin import send_notification_form, bulk_notification_form
from django.db.models import Q

User = get_user_model()

@admin.action(description='Envoyer une notification avec pièce jointe')
def notification_with_attachment_action(modeladmin, request, queryset):
    """Action admin pour envoyer une notification avec pièce jointe"""
    return HttpResponseRedirect(reverse('notifications:notification_with_attachment_form'))

@admin.action(description='Envoyer des notifications avec pièces jointes')
def bulk_notification_with_attachment_action(modeladmin, request, queryset):
    """Action admin pour envoyer des notifications en masse avec pièces jointes"""
    return HttpResponseRedirect(reverse('notifications:bulk_notification_with_attachment_form'))

@admin.action(description='Envoyer une notification personnalisée')
def send_notification_action(modeladmin, request, queryset):
    """Action admin pour envoyer une notification"""
    return HttpResponseRedirect(reverse('admin:send_notification_form'))

@admin.action(description='Envoyer des notifications en masse')
def bulk_notification_action(modeladmin, request, queryset):
    """Action admin pour envoyer des notifications en masse"""
    return HttpResponseRedirect(reverse('admin:bulk_notification_form'))

@admin.action(description='Envoyer une notification rapide')
def quick_notification_action(modeladmin, request, queryset):
    """Action admin pour envoyer une notification rapide"""
    return render(request, 'admin/quick_notification.html')

class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'subject', 'is_read', 'created_at', 'has_attachment']
    list_filter = ['is_read', 'created_at']
    search_fields = ['message', 'subject', 'user__username', 'user__email']
    readonly_fields = ['created_at']
    actions = [
        notification_with_attachment_action,
        bulk_notification_with_attachment_action,
        send_notification_action,
        bulk_notification_action,
        quick_notification_action
    ]
    
    def get_actions(self, request):
        actions = super().get_actions(request)
        return actions
    
    def has_attachment(self, obj):
        return bool(obj.attachment)
    
    has_attachment.boolean = True
    has_attachment.short_description = "A une pièce jointe"
    
    def user_display(self, obj):
        if obj.user:
            return format_html(
                f"<strong>{obj.user.get_full_name() or obj.user.username}</strong><br>"
                f"<small>{obj.user.email}</small>"
            )
        return "Utilisateur supprimé"
    
    def subject_display(self, obj):
        return obj.subject[:50] + ('...' if len(obj.subject) > 50 else '')
    
    subject_display.short_description = "Sujet tronqué"
    
    def message_display(self, obj):
        return obj.message[:100] + ('...' if len(obj.message) > 100 else '')
    
    message_display.short_description = "Message tronqué"

admin.site.register(Notification, NotificationAdmin)


