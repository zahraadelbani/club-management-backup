# Refactored polls/urls.py
from django.urls import path
from . import views

app_name = "polls"

urlpatterns = [
    path("", views.poll_list, name="poll_list"),
    path("poll/<int:poll_id>/", views.view_poll, name="view_poll"),
    path("poll/<int:poll_id>/PollVote/", views.Pollvote, name="vote"),
    path("poll/create/", views.create_poll, name="create_poll"),
    path("poll/<int:poll_id>/update/", views.update_poll, name="update_poll"),
    path('select-num-choices/', views.select_num_choices, name='select_num_choices'),
]
