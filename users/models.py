from django.contrib.auth.models import AbstractUser
from django.db import models


# Create your models here.
class User(AbstractUser):
    email = models.EmailField(unique=True, help_text="Email пользователя")
    phone_number = models.CharField(max_length=15, blank=True, null=True, help_text="Номер телефона пользователя")
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True, help_text="Аватар пользователя")
    city = models.CharField(max_length=100, blank=True, null=True, help_text="Город пользователя")
    telegram_chat_id = models.BigIntegerField(
        unique=True,
        null=True,
        blank=True,
        help_text="ID чата пользователя в Telegram для отправки напоминаний",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = [
        "username",
    ]

    def __str__(self):
        return self.email
