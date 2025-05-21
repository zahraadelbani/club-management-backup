from django.db import models
from django.utils.translation import gettext_lazy as _
from users.models import Membership
from clubs.models import Club

class MembershipTerminationRequest(models.Model):
    """Stores requests from members who want to leave a club."""

    STATUS_CHOICES = [
        ("pending", _("Pending")),
        ("approved", _("Approved")),
        ("rejected", _("Rejected")),
    ]

    membership = models.ForeignKey(
        Membership,
        on_delete=models.CASCADE,
        related_name="termination_requests",
        verbose_name=_("Membership"),
    )

    club = models.ForeignKey(
        Club,
        on_delete=models.CASCADE,
        verbose_name=_("Club"),
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        verbose_name=_("Status"),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At"),
    )

    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Reviewed At"),
    )

    def __str__(self):
        return _("Termination Request: %(user)s - %(club)s") % {
            "user": self.membership.user.name,
            "club": self.club.name
        }
