from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
import json

from .models_simple import Conversation, DirectMessage, DirectMessageAttachment, DirectMessageRead

User = get_user_model()

@login_required
def chat_view(request, user_id=None):
    """Vue principale du chat - liste des conversations ou conversation spécifique"""
    # Récupérer toutes les conversations de l'utilisateur
    conversations = Conversation.objects.filter(
        Q(participant1=request.user) | Q(participant2=request.user)
    ).select_related('participant1', 'participant2').annotate(
        last_message_time=Count('messages'),
        unread_count=Count('messages', filter=Q(messages__sender__isnull=False) & ~Q(messages__sender=request.user) & ~Q(messages__read_by__user=request.user))
    ).order_by('-updated_at')
    
    # Utilisateurs en ligne - utilise la fonction existante is_online du CustomUser
    online_users = User.objects.filter(
        last_seen__isnull=False
    ).exclude(id=request.user.id)
    
    # Variables pour la conversation actuelle
    other_user = None
    messages = None
    current_conversation = None
    
    if user_id:
        # Afficher une conversation spécifique
        other_user = get_object_or_404(User, id=user_id)
        
        # Récupérer ou créer la conversation - S'assurer qu'il n'y en a qu'une seule
        try:
            # Chercher une conversation existante entre les deux utilisateurs
            current_conversation = Conversation.objects.get(
                Q(participant1=request.user, participant2=other_user) | 
                Q(participant1=other_user, participant2=request.user)
            )
        except Conversation.DoesNotExist:
            # Créer une nouvelle conversation
            current_conversation = Conversation.objects.create(
                participant1=request.user,
                participant2=other_user
            )
        except Conversation.MultipleObjectsReturned:
            # S'il y en a plusieurs, prendre la plus ancienne et supprimer les autres
            all_convs = Conversation.objects.filter(
                Q(participant1=request.user, participant2=other_user) | 
                Q(participant1=other_user, participant2=request.user)
            ).order_by('id')
            current_conversation = all_convs.first()
            all_convs.exclude(id=current_conversation.id).delete()
        
        # Messages avec pagination
        messages = current_conversation.messages.select_related('sender').prefetch_related('attachments').order_by('timestamp')
        
        # Marquer les messages comme lus
        unread_messages = current_conversation.messages.exclude(
            Q(sender=request.user) | Q(read_by__user=request.user)
        )
        for message in unread_messages:
            DirectMessageRead.objects.get_or_create(message=message, user=request.user)
    
    context = {
        'conversations': conversations,
        'online_users': online_users,
        'other_user': other_user,
        'messages': messages,
        'current_conversation': current_conversation,
    }
    return render(request, 'chat/chat.html', context)

@login_required
def conversation_detail(request, user_id):
    """Conversation avec un utilisateur spécifique - redirige vers la vue unifiée"""
    return chat_view(request, user_id)

@login_required
@require_POST
def send_direct_message(request, user_id):
    """Envoyer un message direct"""
    other_user = get_object_or_404(User, id=user_id)
    
    # Récupérer ou créer la conversation - S'assurer qu'il n'y en a qu'une seule
    try:
        # Chercher une conversation existante entre les deux utilisateurs
        conversation = Conversation.objects.get(
            Q(participant1=request.user, participant2=other_user) | 
            Q(participant1=other_user, participant2=request.user)
        )
    except Conversation.DoesNotExist:
        # Créer une nouvelle conversation
        conversation = Conversation.objects.create(
            participant1=request.user,
            participant2=other_user
        )
    except Conversation.MultipleObjectsReturned:
        # S'il y en a plusieurs, prendre la plus ancienne et supprimer les autres
        all_convs = Conversation.objects.filter(
            Q(participant1=request.user, participant2=other_user) | 
            Q(participant1=other_user, participant2=request.user)
        ).order_by('id')
        conversation = all_convs.first()
        all_convs.exclude(id=conversation.id).delete()
    
    content = request.POST.get('content', '').strip()
    file = request.FILES.get('file')
    
    if content or file:
        message = DirectMessage.objects.create(
            conversation=conversation,
            sender=request.user,
            content=content or "📎 Fichier partagé"
        )
        
        # Gérer l'upload de fichier
        if file:
            # Vérifier la taille du fichier (max 10MB)
            if file.size > 10 * 1024 * 1024:
                messages.error(request, 'Fichier trop volumineux (max 10MB)')
                return redirect('chat:conversation', user_id=user_id)
            
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
                return redirect('chat:conversation', user_id=user_id)
            
            # Créer l'attachement
            DirectMessageAttachment.objects.create(
                message=message,
                file=file,
                filename=file.name,
                file_size=file.size,
                file_type=file.content_type
            )
        
        # Mettre à jour le timestamp de la conversation
        conversation.save()
    
    return redirect('chat:conversation', user_id=user_id)

@login_required
def search_users(request):
    """Rechercher des utilisateurs pour démarrer une conversation"""
    query = request.GET.get('q', '')
    
    # Si la requête est vide ou très courte, retourner tous les utilisateurs
    if not query or len(query) < 2:
        users = User.objects.exclude(id=request.user.id).order_by('first_name', 'last_name')[:20]
    else:
        users = User.objects.filter(
            Q(username__icontains=query) | 
            Q(first_name__icontains=query) | 
            Q(last_name__icontains=query)
        ).exclude(id=request.user.id)[:10]
    
    user_data = []
    for user in users:
        # Utilise la fonction is_online existante du CustomUser
        user_data.append({
            'id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': f"{user.first_name} {user.last_name}".strip() or user.username,
            'is_online': user.is_online,
        })
    
    return JsonResponse({'users': user_data})

@login_required
@require_POST
def mark_message_read(request, message_id):
    """Marquer un message spécifique comme lu"""
    try:
        message = get_object_or_404(DirectMessage, id=message_id)
        
        # Vérifier que l'utilisateur a le droit de marquer ce message comme lu
        if message.conversation.participant1 == request.user or message.conversation.participant2 == request.user:
            # Ne pas marquer son propre message comme lu
            if message.sender != request.user:
                DirectMessageRead.objects.get_or_create(
                    message=message,
                    user=request.user
                )
                return JsonResponse({'success': True})
        
        return JsonResponse({'success': False, 'error': 'Non autorisé'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def start_conversation(request):
    """Démarrer une nouvelle conversation"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_id = data.get('user_id')
            other_user = get_object_or_404(User, id=user_id)
            
            return JsonResponse({
                'success': True,
                'redirect_url': f'/chat/conversation/{user_id}/'
            })
        except (json.JSONDecodeError, User.DoesNotExist):
            return JsonResponse({'success': False, 'error': 'Utilisateur introuvable'})
    
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})
