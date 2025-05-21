from django.db import models
from django.utils.translation import gettext_lazy as _
from clubs.models import Club
from users.models import User

class Feedback(models.Model):
    """Stores feedback and complaints from club members."""
    
    CATEGORY_CHOICES = [
        ('complaint', _('Complaint')),
        ('suggestion', _('Suggestion')),
    ]

    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('reviewed', _('Reviewed')),
    ]

    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name="feedbacks")
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    content = models.TextField(verbose_name=_("Content"))
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, verbose_name=_("Category"))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name=_("Status"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))

    def is_anonymous(self):
        return self.category == 'complaint'

    def display_user(self):
        return self.submitted_by.name if self.submitted_by and not self.is_anonymous() else _("Anonymous")

    def save(self, *args, **kwargs):
        # Automatically anonymize complaints
        if self.category == 'complaint':
            self.submitted_by = None
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{_(self.category.title())} - {self.display_user()}"
