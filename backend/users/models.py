from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models

from users.validators import ban_name_me


class User(AbstractUser):
    """Кастомная модель пользователя."""

    username_validator = UnicodeUsernameValidator

    username = models.CharField(
        'Уникальный юзернейм',
        unique=True,
        max_length=settings.USER_MAX_CHAR,
        validators=[username_validator, ban_name_me],
    )
    email = models.EmailField(
        'Адрес электронной почты',
        unique=True,
        max_length=settings.EMAIL_MAX_CHAR,
    )
    first_name = models.CharField('Имя', max_length=settings.USER_MAX_CHAR)
    last_name = models.CharField('Фамилия', max_length=settings.USER_MAX_CHAR)
    password = models.CharField('Пароль', max_length=settings.USER_MAX_CHAR)
    avatar = models.ImageField(
        'Аватар пользователя',
        blank=True,
        null=True,
        upload_to='avatars',
    )

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Subscription(models.Model):
    """Модель подписок пользователя."""

    author = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name='Автор рецептов',
    )
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Пользователь',
    )

    class Meta:
        ordering = ('author',)
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=('author', 'user'),
                name='unique_sub_author',
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F('author')),
                name='no_self_following',
            ),
        ]

    def __str__(self):
        return f'{self.user} подписан на {self.author}'
