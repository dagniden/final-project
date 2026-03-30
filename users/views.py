from drf_spectacular.utils import (OpenApiExample, OpenApiResponse,
                                   extend_schema, inline_serializer)
from rest_framework import generics
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import CharField, EmailField, Serializer
from rest_framework.views import APIView
from rest_framework_simplejwt.views import (TokenObtainPairView,
                                            TokenRefreshView)

from users.models import User
from users.serializers import (CustomTokenObtainPairSerializer,
                               UserRegistrationSerializer, UserSerializer)


class TokenRefreshRequestSerializer(Serializer):
    refresh = CharField()


class TokenRefreshResponseSerializer(Serializer):
    access = CharField()


# region API Docs
@extend_schema(
    tags=["Auth"],
    summary="Регистрация пользователя",
    description=(
        "Создает новую учетную запись пользователя. Эндпоинт публичный и возвращает базовые "
        "поля созданного пользователя без пароля."
    ),
    request=UserRegistrationSerializer,
    responses={
        201: UserSerializer,
        400: OpenApiResponse(description="Ошибка валидации регистрационных данных."),
    },
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
# endregion
class UserCreateAPIView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]


# region API Docs
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
# endregion
class CustomTokenObtainPairView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = CustomTokenObtainPairSerializer


# region API Docs
@extend_schema(
    tags=["Auth"],
    summary="Обновить access token",
    description="Принимает refresh token и возвращает новый access token.",
    request=TokenRefreshRequestSerializer,
    responses={
        200: TokenRefreshResponseSerializer,
        401: OpenApiResponse(description="Refresh token недействителен или истек."),
    },
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
# endregion
class CustomTokenRefreshView(TokenRefreshView):
    permission_classes = [AllowAny]


# region API Docs
@extend_schema(
    tags=["Users"],
    summary="Получить текущего пользователя",
    description="Возвращает профиль пользователя, от имени которого выполнен запрос.",
    responses={
        200: UserSerializer,
        401: OpenApiResponse(description="Пользователь не аутентифицирован."),
    },
)
# endregion
class UserMeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


# region API Docs
@extend_schema(
    tags=["Users"],
    summary="Получить список пользователей",
    description="Возвращает список всех пользователей системы. Доступно только сотрудникам библиотеки.",
    responses={
        200: UserSerializer(many=True),
        403: OpenApiResponse(description="Эндпоинт доступен только сотрудникам библиотеки."),
    },
)
# endregion
class UserListAPIView(generics.ListAPIView):
    queryset = User.objects.order_by("id")
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]


# region API Docs
@extend_schema(
    tags=["Users"],
    summary="Получить пользователя по id",
    description=(
        "Возвращает пользователя по идентификатору. Сотрудник может просматривать любую учетную "
        "запись, обычный пользователь только свою."
    ),
    responses={
        200: UserSerializer,
        401: OpenApiResponse(description="Пользователь не аутентифицирован."),
        403: OpenApiResponse(description="Недостаточно прав для просмотра чужой учетной записи."),
    },
)
# endregion
class UserDetailAPIView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        user = super().get_object()
        if self.request.user.is_staff or self.request.user == user:
            return user
        raise PermissionDenied("You do not have permission to perform this action.")
