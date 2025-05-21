# notifications/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('api/unread/', views.unread_notifications, name='unread_notifications'),
    path("api/mark-all-read/", views.mark_all_read, name="mark_all_read"),
    path("api/mark-read/<int:notif_id>/", views.mark_notification_read, name="mark_notification_read"),
]

