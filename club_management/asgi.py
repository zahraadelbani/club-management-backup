import os
import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "club_management.settings")
django.setup()

# Import both routing modules
import messaging.routing
import voting.routing
import notifications.routing

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            messaging.routing.websocket_urlpatterns +
            voting.routing.websocket_urlpatterns  +
            notifications.routing.websocket_urlpatterns
        )
    ),
})
