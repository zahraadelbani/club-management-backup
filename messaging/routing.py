from django.urls import re_path
from .import consumers 

websocket_urlpatterns = [
    re_path(r"ws/chat/(?P<room_slug>[^/]+)/$", consumers.ChatConsumer.as_asgi()),
    re_path(r"ws/direct/(?P<user_id>\d+)/$", consumers.DirectChatConsumer.as_asgi()),
]