from django.urls import path
from .views_auth import login_view, signup_view, custom_logout_view

urlpatterns = [
    path('signup/', signup_view, name='account_signup'),
    path('logout/', custom_logout_view, name='account_logout'),
    path('login/', login_view, name='account_login'),

]
