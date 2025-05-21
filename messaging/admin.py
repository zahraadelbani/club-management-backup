from django.contrib import admin
from .models import ChatRoom, Message, DirectChatRoom, DirectMessage

@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ("club", "created_at")
    search_fields = ("club__name",)
    list_filter = ("created_at",)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("sender", "room", "content", "timestamp")
    search_fields = ("sender__name", "content", "room__club__name")
    list_filter = ("timestamp",)


@admin.register(DirectChatRoom)
class DirectChatRoomAdmin(admin.ModelAdmin):
    list_display = ("user1", "user2", "created_at")
    search_fields = ("user1__name", "user2__name")
    list_filter = ("created_at",)

@admin.register(DirectMessage)
class DirectMessageAdmin(admin.ModelAdmin):
    list_display = ("sender", "receiver", "room", "content", "timestamp")
    search_fields = ("sender__name", "receiver__name", "content")
    list_filter = ("timestamp",)