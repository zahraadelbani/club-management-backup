from django import forms
from .models import Club, Event
from django.utils.translation import gettext_lazy as _

class ClubForm(forms.ModelForm):
    class Meta:
        model = Club
        fields = ['name', 'description', 'quota', 'logo', 'background_image']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm'
            }),
            'description': forms.Textarea(attrs={
                'class': 'block w-full rounded-lg border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white text-base p-4 min-h-[150px] resize-y',
                'rows': '6',
                'placeholder': 'Enter a detailed description of the club...'
            }),
            'quota': forms.NumberInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm'
            }),
        }


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            'title', 'event_date', 'participants',
            'image', 'needs', 'total_cost', 'transportation_request',
            'supporting_documents', 'location_name', 'latitude', 'longitude',
        ]
        labels = {
            
            'title': _("Event Title"),
            'event_date': _("Event Date"),
            'participants': _("Participants"),
            'image': _("Image"),
            'needs': _("Event Needs"),
            'total_cost': _("Estimated Cost"),
            'transportation_request': _("Transportation"),
            'supporting_documents': _("Supporting Documents"),
            'location_name': _("Location Name"),
            'latitude': _("Latitude"),
            'longitude': _("Longitude"),
        }
        widgets = {
            'event_date': forms.DateInput(attrs={'type': 'date'}),
            'needs': forms.Textarea(attrs={'rows': 3}),
            'total_cost': forms.NumberInput(attrs={'min': 0, 'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image'].required = False
        self.fields['supporting_documents'].required = False
        self.fields['transportation_request'].required = False
        self.fields['location_name'].required = False
        self.fields['latitude'].required = False
        self.fields['longitude'].required = False
