import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers

from recipes.models import Recipe

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    """Декодирование изображений, переданных в формате Base64."""

    def to_internal_value(self, data):
        """Преобразует входные данные в объект изображения."""
        if isinstance(data, str) and data.startswith('data:image'):
            try:
                format, imgstr = data.split(';base64,')
                ext = format.split('/')[-1]
                data = ContentFile(
                    base64.b64decode(imgstr), name=f'temp.{ext}',
                )
            except (ValueError, IndexError, base64.binascii.Error) as error:
                raise serializers.ValidationError(
                    'Неверный формат Base64 изображения!',
                ) from error
        return super().to_internal_value(data)


class UserGetSerializer(UserSerializer):
    """Сериализатор для получения информации о пользователях."""

    avatar = Base64ImageField(required=False, allow_null=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'avatar',
            'is_subscribed',
        )

    def get_is_subscribed(self, obj):
        """Метод определяет статус подписки на автора."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.subscribers.filter(user=request.user).exists()
        return False

class UserPostSerializer(UserCreateSerializer):
    """Сериализатор для создания нового пользователя."""

    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
        )


class SimpleRecipeSerializer(serializers.ModelSerializer):
    """Простой сериализатор для отображения рецептов."""

    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'text',
            'cooking_time',
        )


class UserSubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для получения подписок пользователя."""

    DEFAULT_RECIPES_LIMIT = 3

    avatar = Base64ImageField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    is_subscribed = serializers.BooleanField(default=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'avatar',
        )

    def get_recipes(self, obj):
        """Получение рецептов автора."""
        recipes = obj.recipes.all()
        recipes_limit = self.context.get(
            'recipes_limit', self.DEFAULT_RECIPES_LIMIT,
        )
        if recipes_limit:
            recipes = recipes[:int(recipes_limit)]
        serializer = SimpleRecipeSerializer(recipes, many=True, read_only=True)
        return serializer.data

    def get_recipes_count(self, obj):
        """Метод возваращает кол-во рецептов автора."""
        return obj.recipes.count()
