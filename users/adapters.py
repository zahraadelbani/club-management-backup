from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model
from allauth.core.exceptions import ImmediateHttpResponse
from django.shortcuts import redirect
from django.contrib import messages

User = get_user_model()

class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    """ Allow Google login only for existing users, prevent new signups """

    def is_open_for_signup(self, request, sociallogin):
        """ Allow signup ONLY if the user already exists in the database """
        email = sociallogin.account.extra_data.get("email")
        if not email:
            return False  # Block signup if email is missing
        return User.objects.filter(email=email).exists()  # Allow login only for existing users

    def pre_social_login(self, request, sociallogin):
        """ Redirect users to login if they are not found in the database """
        email = sociallogin.account.extra_data.get("email")
        user = User.objects.filter(email=email).first()

        if user:
            sociallogin.user = user  # Attach existing user
        else:
            messages.error(request, "Google login failed: Your email is not registered.")
            raise ImmediateHttpResponse(redirect("/accounts/login/"))  # Redirect with an error message
