from django.urls import path
from feedback.views import submit_feedback
from . import views

app_name = "club_member"

urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
    path("join/", views.join_club, name="join_club"),
    path("leave/<int:club_id>/", views.leave_club, name="leave_club"),
    path("events/", views.view_events, name="view_events"),
    path("calendar/", views.event_calendar_member, name="event_calendar"),
    path("get-events/", views.get_events_member, name="get_events_member"),
    path("remind/<int:event_id>/", views.remind_me, name="remind_me"),
    path("member-announcements/", views.member_announcements, name="member_announcements"),
    path("contact/", views.contact, name="contact"),
    path("feedback/", submit_feedback, name="submit_feedback"),
    path("documents/", views.view_documents, name="documents"),
    path("cancel-termination-request/<int:request_id>/", views.cancel_termination_request, name="cancel_termination_request"),
    path("faq/", views.faq_user_member, name="faq_user_member"),
    path("events/<int:event_id>/", views.event_detail, name="event_detail"),
    path("event/<int:event_id>/attend/", views.mark_attendance, name="qr_attendance"),
    path("event/<int:event_id>/qr/", views.qr_attendance, name="qr_attendance"),
]
