from django.conf import settings
from django.db import models
from django.utils import timezone
from clubs.models import Club
from cryptography.fernet import Fernet
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils.translation import gettext_lazy as _


cipher_suite = Fernet(settings.SECRET_ENCRYPTION_KEY.encode())

class ElectionManager(models.Manager):
    def get_live_elections(self):
        now = timezone.now()
        return self.filter(start_date__lte=now, end_date__gte=now, is_active=True)

class Election(models.Model):
    name = models.CharField(max_length=255)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    nomination_start = models.DateTimeField(null=True, blank=True)
    nomination_end = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=False)
    results_verified = models.BooleanField(default=False)

    objects = ElectionManager()  # Assign ElectionManager as the model manager

    def __str__(self):
        return self.name

    def has_ended(self):
        return timezone.now() > self.end_date

    def has_started(self):
        return timezone.now() >= self.start_date

    def is_nomination_open(self):
        now = timezone.now()
        return self.nomination_start and self.nomination_end and self.nomination_start <= now <= self.nomination_end

    @classmethod
    def get_current_election(cls):
        now = timezone.now()
        return cls.objects.filter(
            is_active=True,
            start_date__lte=now,
            end_date__gte=now
        ).order_by('-start_date').first()


class Position(models.Model):
    name = models.CharField(max_length=100)
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name="positions")
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name="positions", null=True, blank=True)

    def __str__(self):
        return f"{self.name} - {self.club.name if self.club else 'No Club'}"


class Candidate(models.Model):
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name="candidates")
    position = models.ForeignKey(Position, on_delete=models.CASCADE, related_name="candidates")
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name="candidates", null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    manifesto = models.TextField(blank=True, null=True)
    votes = models.IntegerField(default=0)
    self_nominated = models.BooleanField(default=False)
    approved = models.BooleanField(default=False)

    def __str__(self):
        club_part = self.club.name if self.club else "No Club"
        return f"{self.user.name} - {self.position.name} ({club_part})"

class Vote(models.Model):
    election = models.ForeignKey("Election", on_delete=models.CASCADE, related_name="votes")
    voter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    position = models.ForeignKey("Position", on_delete=models.CASCADE, related_name="votes")
    candidate = models.ForeignKey("Candidate", on_delete=models.CASCADE, related_name="candidate_votes")
    encrypted_candidate = models.BinaryField(editable=False, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("election", "voter", "position")
        verbose_name = _("Vote")
        verbose_name_plural = _("Votes")

    def save(self, *args, **kwargs):
        if self.candidate:
            self.encrypted_candidate = cipher_suite.encrypt(self.candidate.user.name.encode())

            # ✅ Update candidate vote count
            self.candidate.votes += 1
            self.candidate.save()

        super().save(*args, **kwargs)

        # 🔁 Broadcast updated results via WebSocket
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"election_{self.election.id}",
            {"type": "broadcast_vote_update"}
        )

    def get_decrypted_candidate(self):
        return cipher_suite.decrypt(self.encrypted_candidate).decode() if self.encrypted_candidate else None