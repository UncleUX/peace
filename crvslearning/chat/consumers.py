import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import ChatRoom, Message, UserStatus, MessageRead

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Connexion WebSocket"""
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        
        # Vérifier si l'utilisateur est authentifié
        if not self.scope["user"].is_authenticated:
            await self.close()
            return
        
        # Vérifier si l'utilisateur a accès à ce salon
        if not await self.user_has_room_access(self.scope["user"], self.room_id):
            await self.close()
            return
        
        # Rejoindre le groupe du salon
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        # Mettre à jour le statut de l'utilisateur
        await self.update_user_status(True, self.room_id)
        
        await self.accept()
        
        # Notifier les autres utilisateurs que quelqu'un a rejoint
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_joined',
                'user': {
                    'id': self.scope["user"].id,
                    'username': self.scope["user"].username,
                    'first_name': self.scope["user"].first_name,
                    'last_name': self.scope["user"].last_name,
                }
            }
        )
    
    async def disconnect(self, close_code):
        """Déconnexion WebSocket"""
        if hasattr(self, 'room_group_name'):
            # Mettre à jour le statut de l'utilisateur
            await self.update_user_status(False)
            
            # Notifier les autres utilisateurs que quelqu'un a quitté
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_left',
                    'user': {
                        'id': self.scope["user"].id,
                        'username': self.scope["user"].username,
                    }
                }
            )
            
            # Quitter le groupe
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Réception d'un message"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type', 'message')
            
            if message_type == 'message':
                await self.handle_message(data)
            elif message_type == 'typing':
                await self.handle_typing(data)
            elif message_type == 'mark_read':
                await self.handle_mark_read(data)
                
        except json.JSONDecodeError:
            pass
    
    async def handle_message(self, data):
        """Gestion des messages"""
        content = data.get('content', '').strip()
        reply_to_id = data.get('reply_to')
        
        if not content:
            return
        
        # Créer le message
        message = await self.create_message(content, reply_to_id)
        
        # Envoyer le message au groupe
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': await self.serialize_message(message)
            }
        )
    
    async def handle_typing(self, data):
        """Gestion des notifications de frappe"""
        is_typing = data.get('is_typing', False)
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_typing',
                'user': {
                    'id': self.scope["user"].id,
                    'username': self.scope["user"].username,
                },
                'is_typing': is_typing
            }
        )
    
    async def handle_mark_read(self, data):
        """Gestion des messages lus"""
        message_id = data.get('message_id')
        if message_id:
            await self.mark_message_as_read(message_id)
    
    async def chat_message(self, event):
        """Envoi d'un message au client"""
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['message']
        }))
    
    async def user_joined(self, event):
        """Notification d'arrivée d'un utilisateur"""
        await self.send(text_data=json.dumps({
            'type': 'user_joined',
            'user': event['user']
        }))
    
    async def user_left(self, event):
        """Notification de départ d'un utilisateur"""
        await self.send(text_data=json.dumps({
            'type': 'user_left',
            'user': event['user']
        }))
    
    async def user_typing(self, event):
        """Notification de frappe"""
        await self.send(text_data=json.dumps({
            'type': 'user_typing',
            'user': event['user'],
            'is_typing': event['is_typing']
        }))
    
    @database_sync_to_async
    def user_has_room_access(self, user, room_id):
        """Vérifie si l'utilisateur a accès au salon"""
        try:
            room = ChatRoom.objects.get(id=room_id)
            return room.participants.filter(id=user.id).exists()
        except ChatRoom.DoesNotExist:
            return False
    
    @database_sync_to_async
    def create_message(self, content, reply_to_id=None):
        """Crée un nouveau message"""
        room = ChatRoom.objects.get(id=self.room_id)
        reply_to = None
        if reply_to_id:
            try:
                reply_to = Message.objects.get(id=reply_to_id, room=room)
            except Message.DoesNotExist:
                pass
        
        return Message.objects.create(
            room=room,
            sender=self.scope["user"],
            content=content,
            reply_to=reply_to
        )
    
    @database_sync_to_async
    def serialize_message(self, message):
        """Sérialise un message pour l'envoi"""
        attachments = []
        for attachment in message.attachments.all():
            attachments.append({
                'id': attachment.id,
                'filename': attachment.filename,
                'file_size': attachment.get_file_size_display(),
                'file_type': attachment.file_type,
                'url': attachment.file.url,
                'is_image': attachment.is_image(),
                'is_pdf': attachment.is_pdf(),
                'is_document': attachment.is_document(),
            })
        
        reply_to = None
        if message.reply_to:
            reply_to = {
                'id': message.reply_to.id,
                'content': message.reply_to.content[:100] + '...' if len(message.reply_to.content) > 100 else message.reply_to.content,
                'sender': message.reply_to.sender.username,
            }
        
        return {
            'id': message.id,
            'content': message.content,
            'sender': {
                'id': message.sender.id,
                'username': message.sender.username,
                'first_name': message.sender.first_name,
                'last_name': message.sender.last_name,
            },
            'timestamp': message.timestamp.isoformat(),
            'time_display': message.get_time_display(),
            'is_edited': message.is_edited,
            'reply_to': reply_to,
            'attachments': attachments,
        }
    
    @database_sync_to_async
    def update_user_status(self, is_online, room_id=None):
        """Met à jour le statut de l'utilisateur"""
        status, created = UserStatus.objects.get_or_create(
            user=self.scope["user"],
            defaults={'is_online': is_online}
        )
        
        status.is_online = is_online
        if room_id and is_online:
            try:
                status.current_room = ChatRoom.objects.get(id=room_id)
            except ChatRoom.DoesNotExist:
                pass
        elif not is_online:
            status.current_room = None
        
        status.save()
    
    @database_sync_to_async
    def mark_message_as_read(self, message_id):
        """Marque un message comme lu"""
        try:
            message = Message.objects.get(id=message_id)
            MessageRead.objects.get_or_create(
                message=message,
                user=self.scope["user"]
            )
        except Message.DoesNotExist:
            pass

class OnlineUsersConsumer(AsyncWebsocketConsumer):
    """Consumer pour suivre les utilisateurs en ligne"""
    
    async def connect(self):
        if not self.scope["user"].is_authenticated:
            await self.close()
            return
        
        self.group_name = 'online_users'
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.update_user_status(True)
        await self.accept()
        
        # Envoyer la liste des utilisateurs en ligne
        await self.send_online_users_list()
    
    async def disconnect(self, close_code):
        await self.update_user_status(False)
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
    
    @database_sync_to_async
    def update_user_status(self, is_online):
        """Met à jour le statut en ligne"""
        status, created = UserStatus.objects.get_or_create(
            user=self.scope["user"],
            defaults={'is_online': is_online}
        )
        
        status.is_online = is_online
        status.save()
    
    @database_sync_to_async
    def get_online_users(self):
        """Retourne la liste des utilisateurs en ligne"""
        online_statuses = UserStatus.objects.filter(is_online=True).select_related('user')
        return [
            {
                'id': status.user.id,
                'username': status.user.username,
                'first_name': status.user.first_name,
                'last_name': status.user.last_name,
                'last_seen': status.last_seen.isoformat(),
                'current_room': status.current_room.id if status.current_room else None,
            }
            for status in online_statuses
        ]
    
    async def send_online_users_list(self):
        """Envoie la liste des utilisateurs en ligne"""
        online_users = await self.get_online_users()
        await self.send(text_data=json.dumps({
            'type': 'online_users',
            'users': online_users
        }))
