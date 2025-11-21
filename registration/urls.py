from django.urls import path
from .views import SignUpView, ProfileUpdate, EmailUpdate
from django.contrib import admin
from registration import views
from personas.views import check_profile


urlpatterns = [
    path('check_profile/', check_profile, name='check_profile'),
    path("login/", views.login_view, name="login"),
    path("logout/", views.cerrar_sesion, name="logout"),
    path('signup/', SignUpView.as_view(), name="signup"),
    path('profile/', ProfileUpdate.as_view(), name="profile"),  
    path('profile/email/', EmailUpdate.as_view(), name="profile_email"),       
    path('profile_edit/', views.profile_edit, name='profile_edit'),  
    ]
