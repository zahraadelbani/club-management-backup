from allauth.account.forms import SignupForm
from django import forms
from django.utils.translation import gettext_lazy as _
from .models import User
from allauth.account.forms import ResetPasswordForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib import messages

User = get_user_model()

class CustomSignupForm(SignupForm):
    name = forms.CharField(
        max_length=255,
        required=True,
        label=_("Full Name")
    )
    student_id = forms.CharField(
        max_length=8,
        required=False,
        label=_("Student ID")
    )

    def clean_student_id(self):
        student_id = self.cleaned_data.get("student_id")
        if student_id:
            if not student_id.isdigit() or len(student_id) != 8:
                raise forms.ValidationError(_("Invalid Student ID. It must be exactly 8 digits (numbers only)."))
            if User.objects.filter(student_id=student_id).exists():
                raise forms.ValidationError(_("This Student ID is already registered."))
        return student_id

    def save(self, request):
        user = super().save(request)
        user.name = self.cleaned_data["name"]
        user.student_id = self.cleaned_data.get("student_id", None)
        user.save()
        return user


class ProfileUpdateForm(forms.ModelForm):
    contact = forms.CharField(
        max_length=20, 
        required=False,
        label="Contact Number",
        widget=forms.TextInput(attrs={'placeholder': 'Enter your phone number'})
    )

    class Meta:
        model = User
        fields = ['profile_picture', 'contact']  # ⚡ Remove 'name'
    labels = {
            'contact': _("Contact Number"),
            'profile_picture': _("Profile Picture"),
        }
    def clean_contact(self):
        contact = self.cleaned_data.get("contact")
        if contact:
            import re
            if not re.match(r'^\+?\d{7,15}$', contact):
                raise forms.ValidationError("Enter a valid contact number (7–15 digits, optionally starting with +).")
        return contact
        

    def save(self, commit=True):
        user = super().save(commit=False)
        new_picture = self.cleaned_data.get("profile_picture")

        if new_picture and new_picture != user.profile_picture:
            if user.profile_picture and hasattr(user.profile_picture, 'path'):
                user.profile_picture.delete(save=False)
            user.profile_picture = new_picture

        if commit:
            user.save()
        return user


# users/forms.py

import logging
from allauth.account.forms import ResetPasswordForm
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from datetime import timedelta

User = get_user_model()
logger = logging.getLogger(__name__)

class CustomPasswordResetForm(ResetPasswordForm):
    def clean_email(self):
        email = self.cleaned_data['email'].strip()
        user_qs = User.objects.filter(email__iexact=email)

        if not user_qs.exists():
            raise ValidationError(_("This email is not registered."))

        user = user_qs.first()
        if not user.is_active:
            raise ValidationError(_("This account is inactive. Please contact support."))

        self._users = [user]
        logger.info(f"Password reset requested for: {email}")
        return email
    @property
    def users(self):
        return self._users

    def save(self, request):
        ip = request.META.get('REMOTE_ADDR', 'unknown')
        key = f"password_reset_rate_{ip}"

        if cache.get(key):
            raise ValidationError(_("You must wait a bit before requesting another password reset."))

        cache.set(key, True, timeout=60)

        messages.success(request, _("If your email exists, a password reset link has been sent."))

        return super().save(request)
