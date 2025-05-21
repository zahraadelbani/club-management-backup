from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    def create_user(self, email, name, password=None, **extra_fields):
        if not email:
            raise ValueError(_("The Email field must be set"))
        email = self.normalize_email(email)
        user = self.model(email=email, name=name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, password=None, **extra_fields):
        extra_fields.setdefault("is_admin", True)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, name, password, **extra_fields)


class User(AbstractBaseUser):
    ROLE_CHOICES = [
        ("user", _("User")),
        ("club_member", _("Club Member")),
        ("club_leader", _("Club Leader")),
        ("activity_center_admin", _("Activity Center Admin")),
    ]

    STATUS_CHOICES = [
        ("active", _("Active")),
        ("inactive", _("Inactive")),
    ]

    id = models.AutoField(primary_key=True)
    student_id = models.CharField(max_length=20, unique=True, null=True, blank=True, verbose_name=_("Student ID"))
    profile_picture = models.ImageField(upload_to="profile_pictures/", default="profile_pictures/default.jpg", verbose_name=_("Profile Picture"))
    name = models.CharField(max_length=255, verbose_name=_("Name"))
    email = models.EmailField(unique=True, verbose_name=_("Email"))
    is_active = models.CharField(max_length=10, choices=STATUS_CHOICES, default="active", verbose_name=_("Status"))
    has_voted = models.BooleanField(default=False, verbose_name=_("Has Voted"))
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default="user", verbose_name=_("Role"))
    contact = models.CharField(max_length=20, null=True, blank=True)
    is_admin = models.BooleanField(default=False, verbose_name=_("Is Admin"))
    is_staff = models.BooleanField(default=False, verbose_name=_("Is Staff"))
    is_superuser = models.BooleanField(default=False, verbose_name=_("Is Superuser"))

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    def __str__(self):
        return f"{self.name} ({self.email})"

    def has_perm(self, perm, obj=None):
        return self.is_admin or self.is_superuser

    def has_module_perms(self, app_label):
        return self.is_admin or self.is_superuser

    def get_role(self):
        return self.role.lower()
    
    def get_full_name(self):
        return self.name
    
    def get_short_name(self):
        return self.name.split()[0] if self.name else self.email

class Membership(models.Model):
    MEMBERSHIP_TYPE_CHOICES = [
        ("pending", _("Pending")),
        ("member", _("Member")),
        ("leader", _("Leader")),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="memberships", verbose_name=_("User"))
    club = models.ForeignKey('clubs.Club', on_delete=models.CASCADE, related_name="memberships", null=True, verbose_name=_("Club"))
    membership_type = models.CharField(max_length=10, choices=MEMBERSHIP_TYPE_CHOICES, default="pending", verbose_name=_("Membership Type"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))

    class Meta:
        unique_together = ("user", "club")
        verbose_name = _("Membership")
        verbose_name_plural = _("Memberships")

    def __str__(self):
        return f"{self.user.name} - {self.club.name} ({self.membership_type})"

    def clean(self):
        user_memberships = self.user.memberships.exclude(id=self.id)

        # Count all existing memberships (regardless of type)
        total_memberships = user_memberships.count()

        # Count existing leader memberships
        leader_memberships = user_memberships.filter(membership_type="leader").count()

        # Include this new membership in the counts
        future_total = total_memberships + 1
        future_leader = leader_memberships + (1 if self.membership_type == "leader" else 0)

        if future_total > 3:
            raise ValidationError(_("A user cannot have more than 3 total memberships (including pending ones)."))

        if future_leader > 1:
            raise ValidationError(_("A user cannot be a leader of more than one club."))

    def save(self, *args, **kwargs):
        self.clean()  # validate before saving
        super().save(*args, **kwargs)
