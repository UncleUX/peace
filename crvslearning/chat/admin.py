from django.contrib import admin
from .models import ChatRoom, Message, MessageAttachment, MessageRead, UserStatus

@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_by', 'is_private', 'participant_count', 'created_at']
    list_filter = ['is_private', 'created_at']
    search_fields = ['name', 'description', 'created_by__username']
    readonly_fields = ['created_at']
    filter_horizontal = ['participants']
    
    def participant_count(self, obj):
        return obj.participants.count()
    participant_count.short_description = 'Participants'

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'room', 'content_preview', 'timestamp', 'is_edited']
    list_filter = ['timestamp', 'is_edited', 'room']
    search_fields = ['content', 'sender__username', 'room__name']
    readonly_fields = ['timestamp']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Message'

@admin.register(MessageAttachment)
class MessageAttachmentAdmin(admin.ModelAdmin):
    list_display = ['filename', 'message', 'file_size_display', 'file_type', 'uploaded_at']
    list_filter = ['file_type', 'uploaded_at']
    search_fields = ['filename', 'message__content']
    readonly_fields = ['uploaded_at']
    
    def file_size_display(self, obj):
        return obj.get_file_size_display()
    file_size_display.short_description = 'Taille'

@admin.register(MessageRead)
class MessageReadAdmin(admin.ModelAdmin):
    list_display = ['user', 'message', 'read_at']
    list_filter = ['read_at']
    search_fields = ['user__username', 'message__content']
    readonly_fields = ['read_at']

@admin.register(UserStatus)
class UserStatusAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_online', 'last_seen', 'current_room']
    list_filter = ['is_online', 'last_seen']
    search_fields = ['user__username']
    readonly_fields = ['last_seen']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'current_room')
