import socket
from django.db import models
from django.utils.translation import gettext_lazy as _
from users.models import Membership
from django.core.files.base import ContentFile
from io import BytesIO
import qrcode
from django.urls import reverse
from django.conf import settings
from django.contrib.sites.models import Site


from users.models import User

def get_lan_ip():
    """Get the LAN IP address of the current machine."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
    # Doesn't have to be reachable
        s.connect(("10.255.255.255", 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = "127.0.0.1"
    finally:
        s.close()
    return IP

class Club(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, verbose_name=_("Name"))
    description = models.TextField(verbose_name=_("Description"))
    quota = models.PositiveIntegerField(default=0, verbose_name=_("Quota"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    logo = models.ImageField(upload_to='club_logos/', blank=True, null=True)
    background_image = models.ImageField(upload_to='club_backgrounds/', blank=True, null=True)

    def __str__(self):
        return self.name

    def leader(self):
        leader_membership = self.memberships.filter(membership_type="leader").select_related("user").first()
        return leader_membership.user if leader_membership else None

    def members(self):
        return [m.user for m in self.memberships.filter(membership_type="member").select_related("user")]

    def get_leader(self):
        return self.memberships.filter(membership_type="leader").first()

    def get_member_count(self):
        return self.memberships.filter(membership_type="member").count()

    def is_user_leader(self, user):
        return self.memberships.filter(user=user, membership_type="leader").exists()

    def has_quota(self):
        return self.get_member_count() < self.quota
    
    def get_members(self):
        from users.models import User
        return User.objects.filter(
        memberships__club=self,
        memberships__membership_type="member"
    )

class Event(models.Model):
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
    ]

    club = models.ForeignKey("clubs.Club", on_delete=models.CASCADE, related_name="events", verbose_name=_("Club"), null=True, blank=True)
    title = models.CharField(max_length=255, verbose_name=_("Title"))
    event_date = models.DateTimeField(verbose_name=_("Event Date"))
    participants = models.TextField(verbose_name=_("Participants"))
    image = models.ImageField(upload_to='event_images/', blank=True, null=True, verbose_name=_("Image"))
    needs = models.TextField(blank=True, null=True, verbose_name=_("Needs"))
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name=_("Total Cost"))
    transportation_request = models.BooleanField(default=False, verbose_name=_("Transportation Request"))
    supporting_documents = models.FileField(upload_to='event_docs/', blank=True, null=True, verbose_name=_("Supporting Documents"))
    created_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Created By"))
    approval_status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending', verbose_name=_("Approval Status"))
    rescheduled = models.BooleanField(default=False, verbose_name=_("Rescheduled"))
    qr_code = models.ImageField(upload_to='event_qrcodes/', blank=True, null=True, verbose_name=_("QR Code"))
    location_name = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Location Name"))
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True, verbose_name=_("Latitude"))
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True, verbose_name=_("Longitude"))

    def __str__(self):
        return str(self.title)
    
    def display_status(self):
        if self.approval_status == "pending" and self.rescheduled:
            return _("Pending (Meeting Scheduled)")
        return self.get_approval_status_display()

    def generate_qr_code(self):
        from io import BytesIO
        from django.core.files.base import ContentFile
        from django.urls import reverse
        import qrcode

        # Use LAN IP dynamically
        ip = get_lan_ip()
        qr_url = f"http://{ip}:8000{reverse('club_member:qr_attendance', args=[self.id])}"

        qr = qrcode.make(qr_url)
        buffer = BytesIO()
        qr.save(buffer, format='PNG')
        filename = f"event_{self.id}_qr.png"
        self.qr_code.save(filename, ContentFile(buffer.getvalue()), save=False)


    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if not is_new:
            original_event = Event.objects.filter(pk=self.pk).first()
            if original_event and original_event.approval_status != self.approval_status:
                if original_event.approval_status in ["approved", "rejected"]:
                    self.approval_status = "pending"

        super().save(*args, **kwargs)

        if not self.qr_code:
            self.generate_qr_code()
            super().save(update_fields=["qr_code"])



class RescheduleRequest(models.Model):
    event = models.OneToOneField(Event, on_delete=models.CASCADE, verbose_name=_("Event"))
    club_leader = models.ForeignKey('users.User', on_delete=models.CASCADE, verbose_name=_("Club Leader"))
    requested_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Requested At"))
    status = models.CharField(
        max_length=10,
        choices=[('pending', _('Pending')), ('approved', _('Approved'))],
        default='pending',
        verbose_name=_("Status")
    )

    def __str__(self):
        return str(_("Reschedule Request for {title}").format(title=self.event.title))



class Meeting(models.Model):
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name="meetings", verbose_name=_("Club"))
    date_time = models.DateTimeField(verbose_name=_("Date and Time"))
    agenda = models.TextField(verbose_name=_("Agenda"))

    def __str__(self):
        return str(_("Meeting with {club} on {date}").format(
        club=self.club.name,
        date=self.date_time.strftime("%b %d, %Y %I:%M %p")
    ))



class Announcement(models.Model):
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name="announcements", verbose_name=_("Club"), null=True, blank=True)
    title = models.CharField(max_length=255, verbose_name=_("Title"))
    content = models.TextField(verbose_name=_("Content"))
    visible = models.BooleanField(default=True, verbose_name=_("Visible"))
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))

    def __str__(self):
        return f"{self.title} ({'Visible' if self.visible else 'Hidden'})"

class ClubDocument(models.Model):
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name="documents", verbose_name=_("Club"))
    title = models.CharField(max_length=255, verbose_name=_("Title"))
    file = models.FileField(upload_to="club_documents/", verbose_name=_("File"))
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Uploaded At"))

    def __str__(self):
        return f"{self.title} ({self.club.name})"

class EventAttendance(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendances')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='attendances')
    is_attending = models.BooleanField(default=False, verbose_name=_("Will Attend"))
    checked_in = models.BooleanField(default=False, verbose_name=_("Checked In"))
    responded_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Responded At"))
    checked_in_at = models.DateTimeField(blank=True, null=True, verbose_name=_("Checked In At"))

    class Meta:
        unique_together = ('user', 'event')

    def __str__(self):
        return f"{self.user.name} - {self.event.title} - RSVP: {self.is_attending} - Checked in: {self.checked_in}"
