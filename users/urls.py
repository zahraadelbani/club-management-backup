from django.urls import path
from . import views
from .views import profile_view,user_dashboard

app_name = "users" 

urlpatterns = [
    path("profile/", profile_view, name="profile"),
    path('udashboard/', user_dashboard, name='udashboard'),
    path('list/', views.list_users, name='list_users'),
    path('create/', views.create_user, name='create_user'),
    path('update/<int:user_id>/', views.update_user, name='update_user'),
    path('delete/<int:user_id>/', views.delete_user, name='delete_user'),
    path("dashboard/", views.user_dashboard, name="udashboard"),
    path("apply/<int:club_id>/", views.apply_to_club, name="apply_to_club"),
    path("check-status/", views.check_membership_status, name="check_membership_status"),
    path("cancel_application/<int:club_id>/", views.cancel_application, name="cancel_application"),
    path("announcements/", views.announcements_view, name="announcements"),
]
