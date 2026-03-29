from django.urls import path

from users.apps import UsersConfig
from users.views import CustomTokenObtainPairView, CustomTokenRefreshView, UserCreateAPIView

app_name = UsersConfig.name

urlpatterns = [
    path("users/register/", UserCreateAPIView.as_view(), name="register"),
    path("users/login/", CustomTokenObtainPairView.as_view(), name="login"),
    path("users/token/refresh/", CustomTokenRefreshView.as_view(), name="token_refresh"),
]
