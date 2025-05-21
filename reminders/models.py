from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from clubs.models import Event

class EventReminder(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='event_reminders',
        verbose_name=_("User")
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='reminders',
        verbose_name=_("Event")
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    scheduled_for = models.DateTimeField(verbose_name=_("Scheduled For"))

    class Meta:
        unique_together = ('user', 'event')
        verbose_name = _("Event Reminder")
        verbose_name_plural = _("Event Reminders")

    def __str__(self):
        return f"{_('Reminder for')} {self.user} - {self.event}"
