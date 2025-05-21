from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .models import Notification

@login_required
def unread_notifications(request):
    notifs = Notification.objects.filter(user=request.user, is_read=False).order_by('-timestamp')[:20]
    data = [
        {
            "id": n.id,
            "title": n.title,
            "message": n.message,
            "url": n.url,
            "timestamp": n.timestamp.strftime("%Y-%m-%d %H:%M"),
        }
        for n in notifs
    ]
    return JsonResponse(data, safe=False)

@login_required
def mark_all_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({"status": "ok"})

@login_required
def mark_notification_read(request, notif_id):
    notification = get_object_or_404(Notification, id=notif_id, user=request.user)
    notification.is_read = True
    notification.save()
    return JsonResponse({"status": "ok"})