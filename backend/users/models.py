"""
Модели для работы с пользователями.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Расширенная модель пользователя.

    Добавлены поля:
    - email (обязательное, уникальное)
    - first_name (обязательное)
    - last_name (обязательное)
    - avatar (опциональное)
    """

    email = models.EmailField(
        "Адрес электронной почты",
        max_length=254,
        unique=True,
        help_text="Обязательное поле. Должно быть уникальным.",
    )

    first_name = models.CharField(
        "Имя",
        max_length=150,
        help_text="Обязательное поле.",
    )

    last_name = models.CharField(
        "Фамилия",
        max_length=150,
        help_text="Обязательное поле.",
    )

    avatar = models.ImageField(
        "Аватар",
        upload_to="users/avatars/",
        blank=True,
        null=True,
        help_text="Изображение профиля пользователя.",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ["id"]

    def __str__(self):
        return self.username


class Subscription(models.Model):
    """
    Модель подписки пользователя на автора.

    Пользователь (user) подписывается на автора (author).
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="subscriptions",
        verbose_name="Подписчик",
        help_text="Пользователь, который подписывается.",
    )

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="subscribers",
        verbose_name="Автор",
        help_text="Автор, на которого подписываются.",
    )

    created = models.DateTimeField(
        "Дата подписки",
        auto_now_add=True,
    )

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        ordering = ["-created"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "author"],
                name="unique_subscription",
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F("author")),
                name="prevent_self_subscription",
            ),
        ]

    def __str__(self):
        return f"{self.user.username} подписан на {self.author.username}"
