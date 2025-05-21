from django.urls import path
from . import views
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from club_member.views import event_detail

app_name = "clubs"

urlpatterns = [
    path("<int:club_id>/", views.club_detail, name="club_detail"),
    path('events/<int:event_id>/', event_detail, name='event_detail'),
    path('events/check-in/', views.check_in_view, name='check_in_api'),
    path('events/scan/', login_required(TemplateView.as_view(template_name="events/event_checkin.html")), name='event_checkin_page'),
]
