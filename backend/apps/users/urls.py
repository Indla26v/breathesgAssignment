from django.urls import path
from apps.users.views import (
    CookieTokenObtainPairView,
    CookieTokenRefreshView,
    LogoutView,
    UserMeView
)

urlpatterns = [
    path('token/', CookieTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', CookieTokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('me/', UserMeView.as_view(), name='user_me'),
]
