from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError
from django.db import models

from users import constants


class User(AbstractUser):
    """Кастомная модель пользователя."""

    username_validator = UnicodeUsernameValidator
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name')

    username = models.CharField(
        'Уникальный юзернейм',
        unique=True,
        max_length=constants.USER_MAX_CHAR,
        validators=(username_validator,),
    )
    email = models.EmailField(
        'Адрес электронной почты',
        unique=True,
        max_length=constants.EMAIL_MAX_CHAR,
    )
    first_name = models.CharField('Имя', max_length=constants.USER_MAX_CHAR)
    last_name = models.CharField(
        'Фамилия',
        max_length=constants.USER_MAX_CHAR,
    )
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
        return self.username[: constants.MAX_CHAR]


class Subscription(models.Model):
    """Модель подписок пользователя."""

    author = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name='author_subscriptions',
        verbose_name='Автор рецептов',
    )
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name='user_subscribers',
        verbose_name='Пользователь',
    )

    class Meta:
        ordering = ('author',)
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = (
            models.UniqueConstraint(
                fields=('author', 'user'),
                name='unique_sub_author',
            ),
        )

    def clean(self):
        if self.author == self.user:
            raise ValidationError('Вы не можете подписаться сами на себя!')

    def __str__(self):
        return f'{self.user} подписан на {self.author}'
