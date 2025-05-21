# club_management/urls.py

from django.conf import settings
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path, include
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.views.generic import TemplateView

# ✦ Import the stock WebAuthn views…
from django_otp_webauthn import views as webauthn_views
# ✦ …and your subclass that injects the backend before login
from users.views_auth import CustomCredentialAuthenticationCompleteView

from users.views import navbar
from users.views_auth import (
    custom_logout_view,
    login_view,
    redirect_after_login,
    signup_view,
)
from django.contrib.auth.decorators import login_required

urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),

    # WebAuthn registration (requires login)
    path(
        'webauthn/registration/begin/',
        login_required(webauthn_views.BeginCredentialRegistrationView.as_view()),
        name='credential-registration-begin',
    ),
    path(
        'webauthn/registration/complete/',
        login_required(webauthn_views.CompleteCredentialRegistrationView.as_view()),
        name='credential-registration-complete',
    ),

    # WebAuthn authentication (public)
    path(
        'webauthn/authentication/complete/',
        CustomCredentialAuthenticationCompleteView.as_view(),
        name='credential-authentication-complete',
    ),
    path(
        'webauthn/authentication/begin/',
        webauthn_views.BeginCredentialAuthenticationView.as_view(),
        name='credential-authentication-begin',
    ),
    # Override Allauth’s login/signup/logout
    path('accounts/login/', login_view, name='account_login'),
    path('accounts/signup/', signup_view, name='account_signup'),
    path('accounts/logout/', custom_logout_view, name='account_logout'),
    path('accounts/', include('allauth.urls')),

    # Post-login redirect logic
    path('redirect-after-login/', redirect_after_login, name='redirect_after_login'),
    # Root → login
    path('', lambda request: redirect('account_login')),

    # Password reset confirmation done view
    path(
        'custom-reset-done/',
        TemplateView.as_view(template_name="account/custom_reset_done.html"),
        name="custom_reset_done",
    ),
]

# Translated (i18n) URL patterns
urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    path('users/', include('users.urls')),
    path('activity-center-admin/', include('activity_center_admin.urls')),
    path('club-leader/', include('club_leader.urls')),
    path('club-member/', include('club_member.urls')),
    path('polls/', include('polls.urls')),
    path('navbar/', navbar, name='navbar'),
    path('clubs/', include('clubs.urls')),
    path('messaging/', include('messaging.urls', namespace="messaging")),
    path('chatbot/', include('chatbot.urls')),
    path('__reload__/', include('django_browser_reload.urls')),
    path('voting/', include('voting.urls', namespace="voting")),
    path('notifications/', include('notifications.urls')),
)

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
