from django.urls import re_path
from . import consumers_realtime

websocket_urlpatterns = [
    re_path(r'^ws/chat/(?P<user_id>\d+)/$', consumers_realtime.ChatConsumer.as_asgi()),
    re_path(r'^ws/online-users/$', consumers_realtime.OnlineUsersConsumer.as_asgi()),
]
