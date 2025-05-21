from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from users.models import User  # Make sure you import your user model

def create_notification(user=None, user_id=None, title="", message="", url=""):
    if user is None and user_id is not None:
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return  # Skip if user doesn't exist

    if user is None:
        return  # No user to notify

    from .models import Notification
    notification = Notification.objects.create(
        user=user,
        title=title,
        message=message,
        url=url,
    )

    # Real-time push via WebSocket
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"user_{user.id}_notifications",
        {
            "type": "send_notification",
            "notification": {
                "id": notification.id,
                "title": title,
                "message": message,
                "url": url,
                "timestamp": notification.timestamp.strftime("%Y-%m-%d %H:%M"),
            },
        },
    )
