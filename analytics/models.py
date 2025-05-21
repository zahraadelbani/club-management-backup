from django.db import models
from django.utils.translation import gettext_lazy as _
from clubs.models import Club

class ClubAnalytics(models.Model):
    """Stores analytics for a club."""
    club = models.OneToOneField(
        Club,
        on_delete=models.CASCADE,
        related_name="analytics",
        verbose_name=_("Club")
    )
    total_members = models.PositiveIntegerField(default=0, verbose_name=_("Total Members"))
    total_events = models.PositiveIntegerField(default=0, verbose_name=_("Total Events"))
    total_polls = models.PositiveIntegerField(default=0, verbose_name=_("Total Polls"))
    total_feedback = models.PositiveIntegerField(default=0, verbose_name=_("Total Feedback"))
    total_documents = models.PositiveIntegerField(default=0, verbose_name=_("Total Documents"))
    total_announcements = models.PositiveIntegerField(default=0, verbose_name=_("Total Announcements"))
    total_meetings = models.PositiveIntegerField(default=0, verbose_name=_("Total Meetings"))
    last_updated = models.DateTimeField(auto_now=True, verbose_name=_("Last Updated"))

    def update_stats(self):
        """Recalculate analytics data based on current state."""
        self.total_members = self.club.memberships.filter(membership_type__in=["member", "leader"]).count()
        self.total_events = self.club.events.count()
        self.total_polls = self.club.polls.count()
        self.total_feedback = self.club.feedbacks.count()
        self.total_documents = self.club.documents.count()
        self.total_announcements = self.club.announcements.count()
        self.total_meetings = self.club.meetings.count()
        self.save()

    def members_percentage(self):
        """Calculate percentage of members based on club quota."""
        if self.club.quota > 0:
            return round((self.total_members / self.club.quota) * 100, 2)
        return 0

    def __str__(self):
        return _("Analytics for %(club)s") % {"club": self.club.name}
