# Refactored polls/forms.py with translations
from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Poll, Choice

class PollForm(forms.ModelForm):
    class Meta:
        model = Poll
        fields = ["question"]
        labels = {
            "question": _("Question"),
        }


class ChoiceForm(forms.ModelForm):
    class Meta:
        model = Choice
        fields = ["text"]
        labels = {
            "text": _("Choice Text"),
        }


class ChoiceCountForm(forms.Form):
    num_choices = forms.IntegerField(
        label=_("Number of Choices"),
        min_value=2,
        max_value=10,
        help_text=_("Enter how many choices this poll should have (between 2 and 10)."),
    )
