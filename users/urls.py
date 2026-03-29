from django.urls import path

from users.apps import UsersConfig
from users.views import (CustomTokenObtainPairView, CustomTokenRefreshView,
                         UserCreateAPIView, UserDetailAPIView, UserListAPIView,
                         UserMeAPIView)

app_name = UsersConfig.name

urlpatterns = [
    path("auth/register", UserCreateAPIView.as_view(), name="register"),
    path("auth/login", CustomTokenObtainPairView.as_view(), name="login"),
    path("auth/refresh", CustomTokenRefreshView.as_view(), name="token_refresh"),
    path("users", UserListAPIView.as_view(), name="user_list"),
    path("users/me", UserMeAPIView.as_view(), name="user_me"),
    path("users/<int:pk>", UserDetailAPIView.as_view(), name="user_detail"),
]
