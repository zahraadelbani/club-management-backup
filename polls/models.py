from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from clubs.models import Club

class Poll(models.Model):
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name="polls", verbose_name=_("Club"))
    question = models.TextField(verbose_name=_("Poll Question"))
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name=_("Created By"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))

    class Meta:
        verbose_name = _("Poll")
        verbose_name_plural = _("Polls")

    def __str__(self):
        return f"{self.question} ({self.club.name})"


class Choice(models.Model):
    poll = models.ForeignKey("Poll", on_delete=models.CASCADE, related_name="choices", verbose_name=_("Poll"))
    text = models.CharField(max_length=255, verbose_name=_("Choice Text"))
    vote_count = models.PositiveIntegerField(default=0, verbose_name=_("Vote Count"))

    class Meta:
        verbose_name = _("Choice")
        verbose_name_plural = _("Choices")

    def __str__(self):
        return f"{self.text} ({_('Poll')}: {self.poll.question})"


class PollVote(models.Model):
    poll = models.ForeignKey("Poll", on_delete=models.CASCADE, related_name="poll_votes", verbose_name=_("Poll"))
    choice = models.ForeignKey("Choice", on_delete=models.CASCADE, verbose_name=_("Choice"))
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="poll_votes", verbose_name=_("User"))
    voted_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Voted At"))

    class Meta:
        unique_together = ("poll", "user")
        verbose_name = _("Poll Vote")
        verbose_name_plural = _("Poll Votes")

    def __str__(self):
        return f"{getattr(self.user, 'name', _('Unknown User'))} {_('voted for')} '{self.choice.text}'"
