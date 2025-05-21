from allauth.account.adapter import DefaultAccountAdapter  
from django.contrib.auth import get_backends, login

class CustomAccountAdapter(DefaultAccountAdapter):  
    def login(self, request, user):
        remember = request.session.get('remember', False)  # Use session instead of request.POST

        # Explicitly set the authentication backend for AllAuth
        user.backend = 'allauth.account.auth_backends.AuthenticationBackend'  

        # Set session expiry based on "Remember Me" checkbox
        if remember:
            request.session.set_expiry(1209600)  # 2 weeks
        else:
            request.session.set_expiry(86400)  # 1 day

        login(request, user, backend=user.backend)  # Explicitly provide the backend
