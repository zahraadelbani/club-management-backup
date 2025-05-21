import os
from pathlib import Path
from dotenv import load_dotenv
from django.contrib.messages import constants as messages
from decouple import config

# Load environment variables from .env file
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: Use environment variables for secrets
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "fallback-secret-key")

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")


# Disable DEBUG in production
DEBUG = True  # Set False only in production

# Allowed Hosts
#ALLOWED_HOSTS = ["localhost", "127.0.0.1", "192.168.50.120"]
# ALLOWED_HOSTS for development: accept all IPs including phones on same LAN
# WARNING: Never use ["*"] in production – restrict to actual domain/IP
ALLOWED_HOSTS = ["*"]

# Base URL for QR code generation (update if your IP changes)
QR_BASE_URL = "http://192.168.50.120:8000"


# Application definition
INSTALLED_APPS = [  
    'django.contrib.sites',  # Required for Django AllAuth
    'daphne', 
    'channels',
    'voting',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',

    # Django AllAuth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',

    # Your apps
    'users',
    'clubs',
    #'events',
    'messaging',
    'polls',
    'feedback',
    #'announcements',
    'analytics',
    'activity_center_admin',
    'club_leader',
    #'rector',
    'club_member',
    #'rest_framework',
    'reminders',
    'chatbot',
    'notifications',
    
    #tailwind
    'tailwind',
    'theme',
    'django_browser_reload',
    'django_otp',
    'django_otp.plugins.otp_static',
    'django_otp.plugins.otp_totp',
    'django_otp_webauthn',
    
]

#tailwind
TAILWIND_APP_NAME = 'theme'
INTERNAL_IPS = [
    "127.0.0.1",
]
NPM_BIN_PATH = "C:/Program Files/nodejs/npm.cmd"



# Set up ASGI application
ASGI_APPLICATION = "club_management.asgi.application"
WSGI_APPLICATION = 'club_management.wsgi.application'


# Redis for WebSocket communication
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],
        },
    },
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',  # ✅ Added here
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    
    #tailwind
     "django_browser_reload.middleware.BrowserReloadMiddleware",
     "django_otp.middleware.OTPMiddleware", 
     
]

#email integration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'  # Replace with your SMTP provider if different
EMAIL_PORT = 587
EMAIL_USE_TLS = True 

import environ

env = environ.Env()
environ.Env.read_env()

EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')


# Set your custom user model
AUTH_USER_MODEL = "users.User"

# Tell Django-Allauth to STOP using username
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_AUTO_LOGIN = False  # Prevents auto-login after signup
SOCIALACCOUNT_ENABLED = True


AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

SITE_ID = int(os.getenv("SITE_ID", 12))  
SITE_URL = "http://localhost:8000"  # or https://yourdomain.com in production


ACCOUNT_LOGOUT_REDIRECT_URL = '/accounts/login/'
ACCOUNT_SIGNUP_REDIRECT_URL = '/accounts/login/'  
#LOGIN_REDIRECT_URL = 'dashboard'
#LOGIN_REDIRECT_URL = 'navbar'

LOGOUT_REDIRECT_URL = '/accounts/login/'
ACCOUNT_AUTHENTICATED_LOGIN_REDIRECTS = False 

# Redirect after login
LOGIN_REDIRECT_URL = '/redirect-after-login/'  # Temporary redirect for handling role-based redirection

# Redirect after social login (Google, etc.)
ACCOUNT_AUTHENTICATED_LOGIN_REDIRECTS = True
ACCOUNT_SIGNUP_REDIRECT_URL = '/redirect-after-login/'  # Ensures Google users are redirected properly
ACCOUNT_EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL = '/redirect-after-login/'


SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
        'OAUTH_PKCE_ENABLED': True,
    }
}



ACCOUNT_EMAIL_VERIFICATION = "none" 
SOCIALACCOUNT_AUTO_SIGNUP = False
SOCIALACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL = "/dashboard/"
SOCIALACCOUNT_ADAPTER = "users.adapters.MySocialAccountAdapter"

ACCOUNT_ADAPTER = "users.account_adapter.CustomAccountAdapter"

# Default session expiration (24 hours)
SESSION_COOKIE_AGE = 86400  # 24 hours in seconds

# Ensure session persists for 24 hours unless "Remember Me" is checked
SESSION_EXPIRE_AT_BROWSER_CLOSE = False  # Keeps session active until expiration

# Do not reset expiration time on every request
SESSION_SAVE_EVERY_REQUEST = False  # Ensures session expires exactly after 24 hours


# Remove SSL/HTTPS configurations
# These were causing the "only supports HTTP" issue
# SECURE_SSL_REDIRECT = False
# SESSION_COOKIE_SECURE = False
# CSRF_COOKIE_SECURE = False
# SECURE_HSTS_SECONDS = 0
# SECURE_HSTS_INCLUDE_SUBDOMAINS = False
# SECURE_HSTS_PRELOAD = False
# X_FRAME_OPTIONS = "DENY"

# Fix how AllAuth displays users
ACCOUNT_USER_DISPLAY = lambda user: user.name

ACCOUNT_FORMS = {
    "signup": "users.forms.CustomSignupForm",
    "reset_password": "users.forms.CustomPasswordResetForm",
}
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}


ACCOUNT_PASSWORD_RESET_REDIRECT_URL = '/custom-reset-done/'
ACCOUNT_PASSWORD_RESET_DONE_URL = '/accounts/password/reset/key/done/'


# Root URL configuration
ROOT_URLCONF = 'club_management.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],  # Corrected path
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'users.context_processors.membership_roles',
            ],
        },
    },
]



# Directory where Django will search for additional static files
#STATICFILES_DIRS = [
 #   os.path.join(BASE_DIR, 'static'),
#] 

# Directory where Django collects all static files (useful in production)
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')


# Database Configuration
import dj_database_url
DATABASES = {
    'default': dj_database_url.config(conn_max_age=600)
}


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'   # Default language is English

LANGUAGES = [
    ('en', 'English'),
    ('fa', 'Persian'),
    ('tr', 'Turkish'),
    ('ru', 'Russian'),
    ('fr', 'French'),
    ('ar', 'Arabic'),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',  # For translations
]

TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# MEDIA & STATIC FILES
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]  # ✅ Corrected
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = '/media/'
#MEDIA_ROOT = BASE_DIR / "media"  # ✅ Corrected
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

SECRET_ENCRYPTION_KEY="FON3BAOVsXCjzwhiBXUeVL7ms7qV8xqC_14QX5aO1DE="

MESSAGE_TAGS = {
    messages.DEBUG: 'debug',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'error',
}

# settings.py

# Relying Party ID must be the host only (no scheme or port)
OTP_WEBAUTHN_RP_ID = "localhost"

# Allowed origins must include the exact scheme://host:port
OTP_WEBAUTHN_ALLOWED_ORIGINS = [
  "http://localhost:8000",
]
# Human-readable name shown in the browser prompt
OTP_WEBAUTHN_RP_NAME = "Club Management System"

# If you’re using HTTPS locally, use https://localhost:8000 instead
# CSRF_TRUSTED_ORIGINS is needed if you switch to HTTPS
CSRF_TRUSTED_ORIGINS = [
  "http://localhost:8000",
]
# Pick whichever backend you want WebAuthn to log users in with:
OTP_WEBAUTHN_AUTHENTICATION_BACKEND = "django.contrib.auth.backends.ModelBackend"
