from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Candidate, Position
from users.models import Membership
from django.utils.safestring import mark_safe

class SelfNominationForm(forms.ModelForm):
    class Meta:
        model = Candidate
        fields = ["position", "manifesto"]
        labels = {
            "position": _("Position"),
            "manifesto": _("Manifesto"),
        }
        help_texts = {
            "manifesto": _("Briefly explain why you're a good fit for the position."),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["position"].queryset = Position.objects.none()

from django.utils.safestring import mark_safe

class VotingForm(forms.Form):
    def __init__(self, *args, election=None, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        user_clubs = Membership.objects.filter(
            user=user, membership_type="member"
        ).values_list("club_id", flat=True)

        position_club_pairs = Candidate.objects.filter(
            election=election,
            approved=True,
            club__id__in=user_clubs
        ).values_list(
            "position__id",
            "position__name",
            "club__id",
            "club__name"
        ).distinct()

        for (pos_id, pos_name, club_id, club_name) in position_club_pairs:
            field_label = f"{pos_name} ({club_name})"
            candidates = Candidate.objects.filter(
                election=election,
                approved=True,
                position__id=pos_id,
                club__id=club_id
            )

            # ✅ define the field first
            field = forms.ModelChoiceField(
                queryset=candidates,
                label=field_label,
                widget=forms.RadioSelect,
                required=True
            )

            # ✅ define label formatter
            def candidate_label(obj):
                return {
                    "name": obj.user.name,
                    "image_url": obj.user.profile_picture.url if obj.user.profile_picture else '/static/images/default_profile.jpg',
                    "description": obj.manifesto[:150] if hasattr(obj, "manifesto") else "",
                }


            # ✅ assign label_from_instance
            field.label_from_instance = candidate_label

            field_name = f"pos{pos_id}_club{club_id}"
            self.fields[field_name] = field
