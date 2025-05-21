from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from clubs.models import Club, Event, ClubDocument, Announcement, Meeting
from feedback.models import Feedback
from users.models import Membership
from polls.models import Poll  # Assuming polls are in a separate app
from analytics.models import ClubAnalytics

def update_analytics(club):
    if hasattr(club, "analytics"):
        club.analytics.update_stats()

# Membership
@receiver([post_save, post_delete], sender=Membership)
def update_membership_stats(sender, instance, **kwargs):
    update_analytics(instance.club)

# Events
@receiver([post_save, post_delete], sender=Event)
def update_event_stats(sender, instance, **kwargs):
    update_analytics(instance.club)

# Polls
@receiver([post_save, post_delete], sender=Poll)
def update_poll_stats(sender, instance, **kwargs):
    update_analytics(instance.club)

# Feedback
@receiver([post_save, post_delete], sender=Feedback)
def update_feedback_stats(sender, instance, **kwargs):
    update_analytics(instance.club)

# Documents
@receiver([post_save, post_delete], sender=ClubDocument)
def update_document_stats(sender, instance, **kwargs):
    update_analytics(instance.club)

# Announcements
@receiver([post_save, post_delete], sender=Announcement)
def update_announcement_stats(sender, instance, **kwargs):
    if instance.club:
        update_analytics(instance.club)

# Meetings
@receiver([post_save, post_delete], sender=Meeting)
def update_meeting_stats(sender, instance, **kwargs):
    update_analytics(instance.club)
