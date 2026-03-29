from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema, inline_serializer
from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.serializers import CharField, EmailField, Serializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from users.serializers import CustomTokenObtainPairSerializer, UserSerializer


class TokenRefreshRequestSerializer(Serializer):
    refresh = CharField()


class TokenRefreshResponseSerializer(Serializer):
    access = CharField()


@extend_schema(
    tags=["Auth"],
    summary="Регистрация пользователя",
    description="Создает нового пользователя и возвращает его базовые данные.",
    request=UserSerializer,
    responses={201: UserSerializer},
    examples=[
        OpenApiExample(
            "Пример регистрации",
            value={
                "username": "ivan",
                "email": "ivan@example.com",
                "password": "SecurePass123!",
            },
            request_only=True,
        )
    ],
)
class UserCreateAPIView(generics.CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [AllowAny]


@extend_schema(
    tags=["Auth"],
    summary="Получить JWT токены",
    description="Аутентификация по email и паролю. Возвращает access и refresh токены.",
    request=inline_serializer(
        name="TokenObtainRequest",
        fields={
            "email": EmailField(),
            "password": CharField(),
        },
    ),
    responses={
        200: inline_serializer(
            name="TokenObtainResponse",
            fields={
                "refresh": CharField(),
                "access": CharField(),
            },
        ),
        401: OpenApiResponse(description="Неверные учетные данные."),
    },
    examples=[
        OpenApiExample(
            "Пример логина",
            value={
                "email": "ivan@example.com",
                "password": "SecurePass123!",
            },
            request_only=True,
        )
    ],
)
class CustomTokenObtainPairView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = CustomTokenObtainPairSerializer


@extend_schema(
    tags=["Auth"],
    summary="Обновить access token",
    description="Принимает refresh token и возвращает новый access token.",
    request=TokenRefreshRequestSerializer,
    responses={200: TokenRefreshResponseSerializer},
    examples=[
        OpenApiExample(
            "Пример refresh",
            value={
                "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            },
            request_only=True,
        )
    ],
)
class CustomTokenRefreshView(TokenRefreshView):
    permission_classes = [AllowAny]
