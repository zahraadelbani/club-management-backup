from django import forms
from django.utils.translation import gettext_lazy as _
from voting.models import Election
from clubs.models import Announcement



class ElectionForm(forms.ModelForm):
    class Meta:
        model = Election
        fields = [
            "name", 
            "start_date", "end_date",
            "nomination_start", "nomination_end",
            "is_active"
        ]
        labels = {
            "name": _("Election Name"),
            "start_date": _("Start Date"),
            "end_date": _("End Date"),
            "nomination_start": _("Nomination Start"),
            "nomination_end": _("Nomination End"),
            "is_active": _("Is Active"),
        }
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'nomination_start': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'nomination_end': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['title', 'content']