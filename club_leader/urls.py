from django.urls import path
from .views import club_leader_dashboard, faq_leader
from club_member.views import view_events
from . import views

app_name = 'club_leader'

urlpatterns = [
    path("dashboard/", views.club_leader_dashboard, name="dashboard"),
    path("termination-request/approve/<int:request_id>/", views.approve_termination_request, name="approve_termination"),
    path("termination-request/reject/<int:request_id>/", views.reject_termination_request, name="reject_termination"),
    path("analytics/", views.club_analytics, name="club_analytics"),
    path('upload-document/', views.upload_document, name='upload_document'),
    path('delete-document/<int:pk>/', views.delete_document, name='delete_document'),
    path('documents/', views.list_documents, name='list_documents'),
    path("announcements/", views.list_announcements, name="list_announcements"),
    path("announcements/create/", views.create_announcement, name="create_announcement"),
    path("announcements/edit/<int:pk>/", views.edit_announcement, name="edit_announcement"), 
    path("announcements/toggle/<int:pk>/", views.toggle_visibility, name="toggle_visibility"),  
    path("announcements/delete/<int:pk>/", views.delete_announcement, name="delete_announcement"),

    path("event-request/", views.submit_event_request, name="submit_event_request"),
    #path("event-request/reschedule/<int:event_id>/", views.request_reschedule, name="request_reschedule"),
    #path("event-request/reschedule/approve/<int:reschedule_id>/", views.approve_reschedule, name="approve_reschedule"),
    path('calendar/', views.event_calendar, name='calendar'),
    path('submit-event/', views.submit_event_request, name='submit_event_request'),
    path('get-events/', views.get_events, name='get_events'), 
    path('event/edit/<int:event_id>/', views.edit_event, name='edit_event'),
    path("club-members/", views.club_members, name="club_members"),
    path('members/remove/<int:member_id>/', views.remove_member, name='remove_member'),
    path('review-feedback/<int:feedback_id>/', views.review_feedback, name='review_feedback'),
    path('feedback/', views.club_feedback_list, name='feedback_list'),
    path('events/all/', views.list_all_events, name='list_all_events'), 
    path("update-request/<int:membership_id>/<str:action>/", views.update_membership_status, name="update_membership_status"),
    path('faq-leader/', faq_leader, name='faq_leader'),
    path("events/<int:event_id>/update-image/", views.update_event_image, name="update_event_image"),
    path('events/<int:event_id>/view/', views.view_event, name='view_event'),


]
