import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models_simple import Conversation, DirectMessage, DirectMessageAttachment, DirectMessageRead

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Extraire l'ID de l'autre utilisateur de l'URL
        self.other_user_id = self.scope['url_route']['kwargs']['user_id']
        self.other_user = await self.get_user(self.other_user_id)
        
        if not self.other_user:
            await self.close()
            return
        
        # Créer ou récupérer la conversation
        self.conversation = await self.get_or_create_conversation(self.user, self.other_user)
        
        # Créer un nom de groupe unique pour cette conversation
        self.room_group_name = f"chat_{self.conversation.id}"
        
        # Rejoindre le groupe de la conversation
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        # Marquer l'utilisateur comme en ligne
        await self.mark_user_online(self.user)
        
        await self.accept()
    
    async def disconnect(self, close_code):
        # Marquer l'utilisateur comme hors ligne
        await self.mark_user_offline(self.user)
        
        # Quitter le groupe
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type', 'message')
            
            if message_type == 'message':
                content = text_data_json.get('content', '').strip()
                
                if content:
                    # Créer le message
                    message = await self.create_message(content)
                    
                    # Envoyer le message à tous les participants
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'chat_message',
                            'message': {
                                'id': message.id,
                                'content': message.content,
                                'sender': {
                                    'id': self.user.id,
                                    'username': self.user.username,
                                    'first_name': self.user.first_name,
                                    'get_full_name': self.user.get_full_name() or self.user.username,
                                    'get_avatar_url': await self.get_user_avatar_url(self.user)
                                },
                                'timestamp': message.timestamp.isoformat(),
                                'get_time_display': message.get_time_display(),
                                'is_edited': message.is_edited,
                                'attachments': await self.get_message_attachments(message)
                            }
                        }
                    )
            
            elif message_type == 'typing':
                # Gérer l'indicateur "en train d'écrire"
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'typing_indicator',
                        'user': {
                            'id': self.user.id,
                            'username': self.user.username,
                            'get_full_name': self.user.get_full_name() or self.user.username
                        },
                        'is_typing': text_data_json.get('is_typing', False)
                    }
                )
            
            elif message_type == 'mark_read':
                message_id = text_data_json.get('message_id')
                if message_id:
                    await self.mark_message_as_read(message_id)
                    
        except json.JSONDecodeError:
            pass
        except Exception as e:
            print(f"Erreur dans receive: {e}")
    
    async def chat_message(self, event):
        message = event['message']
        
        # Envoyer le message au WebSocket client
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': message
        }))
    
    async def typing_indicator(self, event):
        # Ne pas renvoyer l'indicateur à l'expéditeur
        if event['user']['id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'typing',
                'user': event['user'],
                'is_typing': event['is_typing']
            }))
    
    @database_sync_to_async
    def get_user(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None
    
    @database_sync_to_async
    def get_or_create_conversation(self, user1, user2):
        conversation, created = Conversation.objects.get_or_create(
            participant1=user1,
            participant2=user2
        )
        return conversation
    
    @database_sync_to_async
    def create_message(self, content):
        message = DirectMessage.objects.create(
            conversation=self.conversation,
            sender=self.user,
            content=content
        )
        
        # Mettre à jour le timestamp de la conversation
        self.conversation.save()
        
        return message
    
    @database_sync_to_async
    def get_message_attachments(self, message):
        attachments = []
        for attachment in message.attachments.all():
            attachments.append({
                'id': attachment.id,
                'filename': attachment.filename,
                'file_url': attachment.file.url,
                'file_size': attachment.file_size,
                'file_type': attachment.file_type,
                'is_image': attachment.is_image(),
                'is_pdf': attachment.is_pdf(),
                'is_document': attachment.is_document()
            })
        return attachments
    
    @database_sync_to_async
    def get_user_avatar_url(self, user):
        try:
            return user.get_avatar_url()
        except:
            return None
    
    @database_sync_to_async
    def mark_user_online(self, user):
        try:
            from users.models import UserStatus
            status, created = UserStatus.objects.get_or_create(
                user=user,
                defaults={'is_online': True}
            )
            if not created:
                status.is_online = True
                status.save()
        except:
            pass
    
    @database_sync_to_async
    def mark_user_offline(self, user):
        try:
            from users.models import UserStatus
            UserStatus.objects.filter(user=user).update(is_online=False)
        except:
            pass
    
    @database_sync_to_async
    def mark_message_as_read(self, message_id):
        try:
            message = DirectMessage.objects.get(id=message_id)
            if message.sender != self.user:
                DirectMessageRead.objects.get_or_create(
                    message=message,
                    user=self.user
                )
        except DirectMessage.DoesNotExist:
            pass


class OnlineUsersConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Rejoindre le groupe des utilisateurs en ligne
        await self.channel_layer.group_add(
            "online_users",
            self.channel_name
        )
        
        # Marquer l'utilisateur comme en ligne
        await self.mark_user_online(self.user)
        
        await self.accept()
        
        # Envoyer la liste des utilisateurs en ligne
        await self.send_online_users_list()
    
    async def disconnect(self, close_code):
        # Marquer l'utilisateur comme hors ligne
        await self.mark_user_offline(self.user)
        
        # Quitter le groupe
        await self.channel_layer.group_discard(
            "online_users",
            self.channel_name
        )
    
    async def user_status_changed(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_status',
            'user': event['user'],
            'is_online': event['is_online']
        }))
    
    @database_sync_to_async
    def mark_user_online(self, user):
        try:
            from users.models import UserStatus
            status, created = UserStatus.objects.get_or_create(
                user=user,
                defaults={'is_online': True}
            )
            if not created:
                status.is_online = True
                status.save()
            
            # Notifier les autres utilisateurs
            from channels.layers import get_channel_layer
            channel_layer = get_channel_layer()
            await channel_layer.group_send(
                "online_users",
                {
                    'type': 'user_status_changed',
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'get_full_name': user.get_full_name() or user.username,
                        'get_avatar_url': user.get_avatar_url() if hasattr(user, 'get_avatar_url') else None
                    },
                    'is_online': True
                }
            )
        except:
            pass
    
    @database_sync_to_async
    def mark_user_offline(self, user):
        try:
            from users.models import UserStatus
            UserStatus.objects.filter(user=user).update(is_online=False)
            
            # Notifier les autres utilisateurs
            from channels.layers import get_channel_layer
            channel_layer = get_channel_layer()
            await channel_layer.group_send(
                "online_users",
                {
                    'type': 'user_status_changed',
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'get_full_name': user.get_full_name() or user.username,
                        'get_avatar_url': user.get_avatar_url() if hasattr(user, 'get_avatar_url') else None
                    },
                    'is_online': False
                }
            )
        except:
            pass
    
    @database_sync_to_async
    def send_online_users_list(self):
        try:
            from users.models import UserStatus
            online_users = UserStatus.objects.filter(is_online=True).select_related('user')
            
            users_data = []
            for status in online_users:
                user = status.user
                users_data.append({
                    'id': user.id,
                    'username': user.username,
                    'get_full_name': user.get_full_name() or user.username,
                    'get_avatar_url': user.get_avatar_url() if hasattr(user, 'get_avatar_url') else None,
                    'is_online': True
                })
            
            await self.send(text_data=json.dumps({
                'type': 'online_users_list',
                'users': users_data
            }))
        except:
            pass
