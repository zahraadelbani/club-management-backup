from django.urls import path
from . import views

app_name = "messaging"

urlpatterns = [
    path("", views.messaging_rooms, name="rooms"),
    path("<slug:room_slug>/", views.group_chat, name="group_chat"),
    path("api/dm/history/<int:user_id>/", views.get_direct_chat_history, name="dm_history"),
    
]