from django import forms
from django.utils.translation import gettext_lazy as _
from clubs.models import Announcement, ClubDocument, Event

class EventRequestForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            'title', 'event_date', 'participants', 'image', 'needs',
            'total_cost', 'transportation_request', 'supporting_documents',
            'location_name', 'latitude', 'longitude'
        ]
        labels = {
            'title': _("Event Title"),
            'event_date': _("Date & Time"),
            'participants': _("Participants"),
            'image': _("Upload Image"),
            'needs': _("Needs"),
            'total_cost': _("Total Cost"),
            'transportation_request': _("Transportation Request"),
            'supporting_documents': _("Supporting Documents"),
            'location_name': _("Location Name"),
            'latitude': _("Latitude"),
            'longitude': _("Longitude"),
        }
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': _('Enter event title')}),
            'event_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'placeholder': _('YYYY-MM-DD HH:MM')}),
            'participants': forms.Textarea(attrs={'rows': 3, 'placeholder': _('List of participants or roles')}),
            'needs': forms.Textarea(attrs={'rows': 5, 'placeholder': _('List materials, support, or other needs')}),
            'total_cost': forms.NumberInput(attrs={'placeholder': _('Total estimated cost')}),
            'location_name': forms.TextInput(attrs={'placeholder': _('E.g., School Auditorium or Google Place Name')}),
            'latitude': forms.NumberInput(attrs={'step': 'any'}),
            'longitude': forms.NumberInput(attrs={'step': 'any'}),
        }

    def save(self, commit=True):
        event = super().save(commit=False)
        if event.pk:  
            event.approval_status = 'pending'
        if commit:
            event.save()
        return event


class ClubDocumentForm(forms.ModelForm):
    class Meta:
        model = ClubDocument
        fields = ['title', 'file']
        labels = {
            'title': _("Document Title"),
            'file': _("Upload File"),
        }
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': _('Enter document title')}),
        }


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ["title", "content", "visible"]
        labels = {
            "title": _("Announcement Title"),
            "content": _("Content"),
            "visible": _("Visible to Members"),
        }
        widgets = {
            "title": forms.TextInput(attrs={'placeholder': _('Enter announcement title')}),
            "content": forms.Textarea(attrs={"rows": 5, "placeholder": _('Write the announcement content here...')}),
        }
