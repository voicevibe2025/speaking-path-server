"""
Authentication URL patterns for VoiceVibe
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    RegisterView,
    LoginView,
    LogoutView,
    UserProfileView,
    VerifyTokenView,
    CustomTokenObtainPairView,
    password_reset_request,
    password_reset_confirm,
    password_reset_confirm_page,
    GoogleLoginView,
)

app_name = 'authentication'

urlpatterns = [
    # Registration and Login
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('login/google/', GoogleLoginView.as_view(), name='login_google'),
    path('logout/', LogoutView.as_view(), name='logout'),

    # JWT Token endpoints
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', VerifyTokenView.as_view(), name='token_verify'),

    # User Profile
    path('profile/', UserProfileView.as_view(), name='profile'),

    # Password Reset
    path('password-reset/', password_reset_request, name='password_reset'),
    path('password-reset-confirm/', password_reset_confirm, name='password_reset_confirm'),
    # Simple HTML page for human-friendly reset via email link
    path('password-reset/confirm/', password_reset_confirm_page, name='password_reset_confirm_page'),
]
