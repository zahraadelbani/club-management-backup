# messaging/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from clubs.models import Club
from .models import ChatRoom

@receiver(post_save, sender=Club)
def create_chat_room(sender, instance, created, **kwargs):
    if created and not hasattr(instance, "chat_room"):
        ChatRoom.objects.create(club=instance, name=f"{instance.name} Chat")