from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from clubs.models import Club
from polls.models import Poll


class ChatRoom(models.Model):
    club = models.OneToOneField(Club, on_delete=models.CASCADE, related_name='chat_room', verbose_name=_("Club"))
    name = models.CharField(max_length=100, verbose_name=_("Room Name"))
    slug = models.SlugField(max_length=100, unique=True, blank=True, verbose_name=_("Slug"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({_('Club')}: {self.club.name})"


class Message(models.Model):
    TEXT = 'text'
    POLL = 'poll'

    MESSAGE_TYPES = [
    (TEXT, _('Text')),
    (POLL, _('Poll')),
    ]

    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages', verbose_name=_("Room"))
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name=_("Sender"))
    content = models.TextField(verbose_name=_("Message Content"))
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name=_("Timestamp"))
    message_type = models.CharField(max_length=10, choices=[('text', 'Text'), ('poll', 'Poll')], default='text')
    poll = models.ForeignKey(
        Poll,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="chat_messages"
        )

    def __str__(self):
        if self.message_type == self.POLL:
            return f"{self.sender.name}  {_('created a poll')}"
        return f"{self.sender.name}: {self.content[:30]}..."


class DirectChatRoom(models.Model):
    user1 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_user1', verbose_name=_("User 1"))
    user2 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_user2', verbose_name=_("User 2"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))

    class Meta:
        unique_together = ('user1', 'user2')
        verbose_name = _("Direct Chat Room")
        verbose_name_plural = _("Direct Chat Rooms")

    def __str__(self):
        return f"{_('Chat between')} {self.user1.name} & {self.user2.name}"

    @classmethod
    def get_or_create_between_users(cls, user_a, user_b):
        user1, user2 = sorted([user_a, user_b], key=lambda u: u.id)
        room, created = cls.objects.get_or_create(user1=user1, user2=user2)
        return room, created


class DirectMessage(models.Model):
    room = models.ForeignKey(DirectChatRoom, on_delete=models.CASCADE, related_name='messages', verbose_name=_("Room"))
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_direct_messages",
        blank=True,
        null=True,
        verbose_name=_("Sender")
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_direct_messages",
        blank=True,
        null=True,
        verbose_name=_("Receiver")
    )
    content = models.TextField(verbose_name=_("Message Content"))
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name=_("Timestamp"))

    class Meta:
        ordering = ['timestamp']
        verbose_name = _("Direct Message")
        verbose_name_plural = _("Direct Messages")

    def __str__(self):
        return f"{_('From')} {self.sender.name} {_('to')} {self.receiver.name}: {self.content[:30]}"
