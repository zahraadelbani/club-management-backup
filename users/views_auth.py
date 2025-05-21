from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils.translation import gettext as _
from django.db.models import Q
from clubs.models import Announcement
from users.forms import CustomSignupForm
from django.contrib.auth.decorators import login_required
from users.models import Membership
from django.urls import reverse

def login_view(request):
    general_announcements = Announcement.objects.filter(
        visible=True,
        club__isnull=True
    ).filter(
        Q(created_by__role__iexact="activity_center_admin") | Q(created_by__isnull=True)
    ).order_by("-created_at")[:4]

    if request.method == "POST":
        email = request.POST.get('login')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, _("Login successful!"))

            if user.is_superuser:
                return redirect("users:list_users")
            if user.get_role() == "activity_center_admin":
                return redirect("activity_center_admin:dashboard")
            elif Membership.objects.filter(user=user, membership_type="leader").exists():
                return redirect("club_leader:dashboard")
            elif Membership.objects.filter(user=user, membership_type="member").exists():
                return redirect("club_member:dashboard")
            elif user.get_role() == "user":
                return redirect("users:udashboard")

            messages.error(request, _("You are not assigned to any club."))
            return redirect("users:profile")

        else:
            messages.error(request, _("Invalid email or password."))

    return render(request, 'account/login.html', {
        "SOCIALACCOUNT_ENABLED": True,
        "signup_url": reverse("account_signup"),
        "general_announcements": general_announcements,
    })

def signup_view(request):
    if request.method == "POST":
        form = CustomSignupForm(request.POST)
        if form.is_valid():
            form.save(request)
            messages.success(request, _("Sign-up successful! Please log in."))
            return redirect("account_login")
    else:
        form = CustomSignupForm()

    return render(request, "account/signup.html", {"form": form})


def custom_logout_view(request):
    """Logs out the user and redirects to login page."""
    logout(request)
    return redirect('account_login')


@login_required
def redirect_after_login(request):
    user = request.user

    if user.is_superuser:
        return redirect("users:list_users")

    if user.get_role() == "activity_center_admin":
        return redirect("activity_center_admin:dashboard")

    elif Membership.objects.filter(user=user, membership_type="leader").exists():
        return redirect("club_leader:dashboard")

    elif Membership.objects.filter(user=user, membership_type="member").exists():
        return redirect("club_member:dashboard")

    elif user.get_role() == "user":
        return redirect("users:udashboard")

    messages.error(request, _("You are not assigned to any club."))
    return redirect("users:profile")

from django.conf import settings
from django_otp_webauthn.views import CompleteCredentialAuthenticationView
from django.contrib.auth import login as auth_login

class CustomCredentialAuthenticationCompleteView(CompleteCredentialAuthenticationView):
    """
    Ensures user.backend is set before calling Django login.
    Handles the case where device.user may be AnonymousUser.
    """
    def complete_auth(self, device):
        user = getattr(device, 'user', None)
        if user and not getattr(user, "is_anonymous", True):
            user.backend = settings.AUTHENTICATION_BACKENDS[0]
            # Directly log in the user with explicit backend argument
            auth_login(self.request, user, backend=settings.AUTHENTICATION_BACKENDS[0])
        else:
            # Defensive: fallback (optional)
            raise Exception("WebAuthn authentication failed: No valid user object.")
        # Continue with normal flow (may redirect or return response as needed)
        return super().complete_auth(device)







