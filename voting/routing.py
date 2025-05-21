from django.urls import path
from .consumers import LiveResultsConsumer  # ✅ use LiveResultsConsumer

websocket_urlpatterns = [
    path("ws/election/<int:election_id>/", LiveResultsConsumer.as_asgi()),
]
