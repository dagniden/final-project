from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from users.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "city",
            "telegram_chat_id",
        )
        read_only_fields = ("id", "telegram_chat_id")
        extra_kwargs = {
            "username": {"help_text": "Уникальное имя пользователя в системе."},
            "email": {"help_text": "Email пользователя. Используется как логин."},
            "first_name": {"help_text": "Имя пользователя."},
            "last_name": {"help_text": "Фамилия пользователя."},
            "phone_number": {"help_text": "Контактный номер телефона пользователя."},
            "city": {"help_text": "Город пользователя."},
            "telegram_chat_id": {
                "help_text": "Telegram chat id для отправки напоминаний о возврате.",
            },
        }


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        help_text="Пароль пользователя в открытом виде. В ответе не возвращается.",
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = ("id", "username", "email", "password", "first_name", "last_name")
        read_only_fields = ("id",)
        extra_kwargs = {
            "username": {"help_text": "Уникальное имя пользователя."},
            "email": {"help_text": "Email пользователя. Используется для входа."},
            "first_name": {"help_text": "Имя пользователя, если требуется."},
            "last_name": {"help_text": "Фамилия пользователя, если требуется."},
        }

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """JWT-аутентификация по email вместо username."""

    username_field = User.USERNAME_FIELD

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["user_id"] = user.id
        token["email"] = user.email
        return token
