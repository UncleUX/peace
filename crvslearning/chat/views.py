from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
import json
import os

from .models import ChatRoom, Message, MessageAttachment, MessageRead, UserStatus
from .forms import ChatRoomForm, MessageForm

User = get_user_model()

@login_required
def chat_list(request):
    """Liste des salons de discussion de l'utilisateur"""
    rooms = ChatRoom.objects.filter(participants=request.user).annotate(
        last_message_time=Count('messages'),
        unread_count=Count('messages', filter=Q(messages__read_by__user=request.user) & ~Q(messages__sender=request.user))
    ).order_by('-messages__timestamp')
    
    # Statistiques
    total_rooms = rooms.count()
    online_users = UserStatus.objects.filter(is_online=True).select_related('user').count()
    
    context = {
        'rooms': rooms,
        'total_rooms': total_rooms,
        'online_users': online_users,
    }
    return render(request, 'chat/chat_list.html', context)

@login_required
def chat_room_simple(request, room_id):
    """Vue simplifiée d'un salon de discussion (sans WebSocket)"""
    room = get_object_or_404(ChatRoom, id=room_id, participants=request.user)
    
    # Messages avec pagination
    messages = room.messages.select_related('sender', 'reply_to').prefetch_related('attachments').order_by('timestamp')
    paginator = Paginator(messages, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Marquer les messages comme lus
    unread_messages = room.messages.exclude(
        Q(sender=request.user) | Q(read_by__user=request.user)
    )
    for message in unread_messages:
        MessageRead.objects.get_or_create(message=message, user=request.user)
    
    context = {
        'room': room,
        'messages': page_obj,
    }
    return render(request, 'chat/chat_room_simple.html', context)

@login_required
def chat_room(request, room_id):
    """Vue d'un salon de discussion"""
    room = get_object_or_404(ChatRoom, id=room_id, participants=request.user)
    
    # Messages avec pagination
    messages = room.messages.select_related('sender', 'reply_to').prefetch_related('attachments').order_by('timestamp')
    paginator = Paginator(messages, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Marquer les messages comme lus
    unread_messages = room.messages.exclude(
        Q(sender=request.user) | Q(read_by__user=request.user)
    )
    for message in unread_messages:
        MessageRead.objects.get_or_create(message=message, user=request.user)
    
    # Participants en ligne
    online_participants = UserStatus.objects.filter(
        is_online=True,
        current_room=room
    ).select_related('user')
    
    context = {
        'room': room,
        'messages': page_obj,
        'online_participants': online_participants,
        'form': MessageForm(),
    }
    return render(request, 'chat/chat_room.html', context)

@login_required
def create_room(request):
    """Créer un nouveau salon de discussion"""
    if request.method == 'POST':
        form = ChatRoomForm(request.POST)
        if form.is_valid():
            room = form.save(commit=False)
            room.created_by = request.user
            room.save()
            room.participants.add(request.user)
            
            # Ajouter d'autres participants si spécifiés
            participants = form.cleaned_data.get('participants')
            if participants:
                room.participants.set([request.user] + list(participants))
            
            return redirect('chat:room', room_id=room.id)
    else:
        form = ChatRoomForm()
    
    return render(request, 'chat/create_room.html', {'form': form})

@login_required
def edit_room(request, room_id):
    """Modifier un salon de discussion"""
    room = get_object_or_404(ChatRoom, id=room_id, created_by=request.user)
    
    if request.method == 'POST':
        form = ChatRoomForm(request.POST, instance=room)
        if form.is_valid():
            form.save()
            return redirect('chat:room', room_id=room.id)
    else:
        form = ChatRoomForm(instance=room)
    
    return render(request, 'chat/edit_room.html', {'form': form, 'room': room})

@login_required
@require_POST
def add_participant(request, room_id):
    """Ajouter un participant à un salon"""
    room = get_object_or_404(ChatRoom, id=room_id, created_by=request.user)
    
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        user = User.objects.get(id=user_id)
        room.participants.add(user)
        
        return JsonResponse({'success': True, 'username': user.username})
    except (json.JSONDecodeError, User.DoesNotExist):
        return JsonResponse({'success': False, 'error': 'Utilisateur introuvable'})

@login_required
@require_POST
def remove_participant(request, room_id):
    """Retirer un participant d'un salon"""
    room = get_object_or_404(ChatRoom, id=room_id, created_by=request.user)
    
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        user = User.objects.get(id=user_id)
        room.participants.remove(user)
        
        return JsonResponse({'success': True})
    except (json.JSONDecodeError, User.DoesNotExist):
        return JsonResponse({'success': False, 'error': 'Utilisateur introuvable'})

@login_required
@csrf_exempt
@require_POST
def upload_attachment(request, room_id):
    """Uploader une pièce jointe"""
    room = get_object_or_404(ChatRoom, id=room_id, participants=request.user)
    
    if 'file' not in request.FILES:
        return JsonResponse({'success': False, 'error': 'Aucun fichier fourni'})
    
    file = request.FILES['file']
    
    # Vérifier la taille du fichier (max 10MB)
    if file.size > 10 * 1024 * 1024:
        return JsonResponse({'success': False, 'error': 'Fichier trop volumineux (max 10MB)'})
    
    # Vérifier le type de fichier
    allowed_types = [
        'image/jpeg', 'image/png', 'image/gif', 'image/bmp', 'image/webp',
        'application/pdf',
        'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.ms-powerpoint', 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
    ]
    
    if file.content_type not in allowed_types:
        return JsonResponse({'success': False, 'error': 'Type de fichier non autorisé'})
    
    # Créer un message temporaire pour l'attachement
    message = Message.objects.create(
        room=room,
        sender=request.user,
        content=f"📎 Fichier partagé: {file.name}"
    )
    
    # Créer l'attachement
    attachment = MessageAttachment.objects.create(
        message=message,
        file=file,
        filename=file.name,
        file_size=file.size,
        file_type=file.content_type
    )
    
    return JsonResponse({
        'success': True,
        'attachment': {
            'id': attachment.id,
            'filename': attachment.filename,
            'file_size': attachment.get_file_size_display(),
            'file_type': attachment.file_type,
            'url': attachment.file.url,
            'is_image': attachment.is_image(),
            'is_pdf': attachment.is_pdf(),
            'is_document': attachment.is_document(),
        },
        'message_id': message.id
    })

@login_required
def search_users(request):
    """Rechercher des utilisateurs pour ajouter à un salon"""
    query = request.GET.get('q', '')
    room_id = request.GET.get('room_id')
    
    if not query:
        return JsonResponse({'users': []})
    
    users = User.objects.filter(
        Q(username__icontains=query) | 
        Q(first_name__icontains=query) | 
        Q(last_name__icontains=query)
    ).exclude(id=request.user.id)[:10]
    
    if room_id:
        room = get_object_or_404(ChatRoom, id=room_id, participants=request.user)
        users = users.exclude(id__in=room.participants.all())
    
    user_data = []
    for user in users:
        user_data.append({
            'id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': f"{user.first_name} {user.last_name}".strip() or user.username,
        })
    
    return JsonResponse({'users': user_data})

@login_required
def online_users(request):
    """Liste des utilisateurs en ligne"""
    online_statuses = UserStatus.objects.filter(is_online=True).select_related('user')
    
    users_data = []
    for status in online_statuses:
        users_data.append({
            'id': status.user.id,
            'username': status.user.username,
            'first_name': status.user.first_name,
            'last_name': status.user.last_name,
            'last_seen': status.last_seen.isoformat(),
            'current_room': status.current_room.id if status.current_room else None,
            'current_room_name': status.current_room.name if status.current_room else None,
        })
    
    return JsonResponse({'users': users_data})

@login_required
@require_POST
def mark_messages_read(request, room_id):
    """Marquer tous les messages d'un salon comme lus"""
    room = get_object_or_404(ChatRoom, id=room_id, participants=request.user)
    
    unread_messages = room.messages.exclude(
        Q(sender=request.user) | Q(read_by__user=request.user)
    )
    
    read_count = 0
    for message in unread_messages:
        MessageRead.objects.get_or_create(message=message, user=request.user)
        read_count += 1
    
    return JsonResponse({'success': True, 'read_count': read_count})

@login_required
def delete_message(request, message_id):
    """Supprimer un message"""
    message = get_object_or_404(Message, id=message_id, sender=request.user)
    
    if request.method == 'POST':
        message.delete()
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})

@login_required
def send_message(request, room_id):
    """Envoyer un message (version simple sans WebSocket)"""
    room = get_object_or_404(ChatRoom, id=room_id, participants=request.user)
    
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        file = request.FILES.get('file')
        
        if content or file:
            message = Message.objects.create(
                room=room,
                sender=request.user,
                content=content or "📎 Fichier partagé"
            )
            
            # Gérer l'upload de fichier
            if file:
                # Vérifier la taille du fichier (max 10MB)
                if file.size > 10 * 1024 * 1024:
                    messages.error(request, 'Fichier trop volumineux (max 10MB)')
                    return redirect('chat:room', room_id=room.id)
                
                # Vérifier le type de fichier
                allowed_types = [
                    'image/jpeg', 'image/png', 'image/gif', 'image/bmp', 'image/webp',
                    'application/pdf',
                    'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    'application/vnd.ms-powerpoint', 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
                ]
                
                if file.content_type not in allowed_types:
                    messages.error(request, 'Type de fichier non autorisé')
                    return redirect('chat:room', room_id=room.id)
                
                # Créer l'attachement
                MessageAttachment.objects.create(
                    message=message,
                    file=file,
                    filename=file.name,
                    file_size=file.size,
                    file_type=file.content_type
                )
        
        return redirect('chat:room', room_id=room.id)
    
    return redirect('chat:room', room_id=room.id)

@login_required
def edit_message(request, message_id):
    """Éditer un message"""
    message = get_object_or_404(Message, id=message_id, sender=request.user)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            new_content = data.get('content', '').strip()
            
            if new_content:
                message.content = new_content
                message.is_edited = True
                message.save()
                
                return JsonResponse({
                    'success': True,
                    'content': message.content,
                    'is_edited': message.is_edited
                })
        except json.JSONDecodeError:
            pass
    
    return JsonResponse({'success': False, 'error': 'Requête invalide'})

# Vues pour le temps réel avec polling
@login_required
def get_new_messages(request, user_id):
    """API pour récupérer les nouveaux messages (polling)"""
    other_user = get_object_or_404(User, id=user_id)
    last_message_id = request.GET.get('last_id', 0)
    
    try:
        # Utiliser les modèles simples pour le chat direct
        from .models_simple import Conversation, DirectMessage
        
        # Récupérer ou créer la conversation
        conversation = Conversation.objects.filter(
            Q(participant1=request.user, participant2=other_user) |
            Q(participant1=other_user, participant2=request.user)
        ).first()
        
        if not conversation:
            return JsonResponse({'messages': []})
        
        # Récupérer les messages plus récents que last_id
        messages = DirectMessage.objects.filter(
            conversation=conversation,
            id__gt=last_message_id
        ).select_related('sender').order_by('timestamp')
        
        messages_data = []
        for msg in messages:
            messages_data.append({
                'id': msg.id,
                'content': msg.content,
                'sender': {
                    'id': msg.sender.id,
                    'get_full_name': msg.sender.get_full_name() or msg.sender.username
                },
                'get_time_display': msg.get_time_display(),
                'is_edited': msg.is_edited,
                'attachments': []
            })
        
        return JsonResponse({'messages': messages_data})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_POST
def send_message_ajax(request, user_id):
    """API pour envoyer un message via AJAX"""
    other_user = get_object_or_404(User, id=user_id)
    
    try:
        data = json.loads(request.body)
        content = data.get('content', '').strip()
        
        if not content:
            return JsonResponse({'success': False, 'error': 'Message vide'}, status=400)
        
        # Utiliser les modèles simples
        from .models_simple import Conversation, DirectMessage
        
        # Récupérer ou créer la conversation
        conversation, created = Conversation.objects.get_or_create(
            participant1=request.user,
            participant2=other_user
        )
        
        # Créer le message
        message = DirectMessage.objects.create(
            conversation=conversation,
            sender=request.user,
            content=content
        )
        
        # Mettre à jour le timestamp de la conversation
        conversation.save()
        
        return JsonResponse({
            'success': True,
            'message': {
                'id': message.id,
                'content': message.content,
                'sender': {
                    'id': message.sender.id,
                    'get_full_name': message.sender.get_full_name() or message.sender.username
                },
                'get_time_display': message.get_time_display(),
                'is_edited': message.is_edited,
                'attachments': []
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON invalide'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
