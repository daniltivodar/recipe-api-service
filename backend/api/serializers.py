import base64

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.db.models import F
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers

from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    RecipeTag,
    ShoppingCart,
    Subscription,
    Tag,
)

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


class UserPostSerializer(UserCreateSerializer):
    """Сериализатор для создания нового пользователя."""

    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'password',
        )


class UserGetSerializer(UserSerializer):
    """Сериализатор для получения информации о пользователях."""

    avatar = Base64ImageField(required=False, allow_null=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'email',
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


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тегов."""

    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов."""

    class Meta:
        model = Ingredient
        fields = '__all__'


class RecipeGetSerializer(serializers.ModelSerializer):
    """Сериализатор для получения рецептов."""

    author = UserGetSerializer()
    tags = TagSerializer(many=True)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def filter_queryset_by_tags(self, queryset):
        """Фильтрует рецепты по тегам."""
        tag_slugs = self.context.get('request').query_params.getlist('tags')
        if tag_slugs:
            query = ()
            for slug in tag_slugs:
                query += slug
            return queryset.filter(query).distinct()
        return queryset

    def get_ingredients(self, obj):
        """Возвращает список ингредиентов рецепта с их количеством."""
        return obj.ingredients.values(
            'id',
            'name',
            'measurement_unit',
            amount=F('recipeingredient__amount'),
        )

    def get_recipe(self, obj, model):
        """Промежуточный метод для проверки состояний связей в моделях."""
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        return model.objects.filter(user=request.user, recipe=obj).exists()

    def get_is_favorited(self, obj):
        """Метод проверяет, добавлен ли рецепт в избранное."""
        return self.get_recipe(obj, Favorite)

    def get_is_in_shopping_cart(self, obj):
        """Метод проверяет, добавлен ли рецепт в корзину."""
        return self.get_recipe(obj, ShoppingCart)


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов в рецепте."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
    )
    amount = serializers.IntegerField(
        write_only=True,
        min_value=settings.MIN_INGREDIENTS_AMOUNT,
    )

    class Meta:
        model = RecipeIngredient
        fields = (
            'id',
            'amount',
        )


class RecipePostSerializer(serializers.ModelSerializer):
    """Сериализатор для создания рецептов."""

    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=True,
        allow_null=False,
        allow_empty=False,
    )
    ingredients = RecipeIngredientSerializer(
        many=True,
        required=True,
        allow_null=False,
        allow_empty=False,
    )
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())
    image = Base64ImageField(required=True)

    class Meta:
        model = Recipe
        fields = (
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
            'author',
        )

    def validate(self, data):
        tags = data.get('tags')
        if not tags:
            raise serializers.ValidationError(
                {'tags': 'Рецепт не может быть без тегов!'},
            )
        ingredients = data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError(
                {'tags': 'Рецепт не может быть без ингредиентов!'},
            )
        return data

    def add_tags_ingredients(self, recipe, tags, ingredients):
        """Замена старых тегов и ингредиентов на новые."""
        RecipeTag.objects.filter(recipe=recipe).delete()
        RecipeIngredient.objects.filter(recipe=recipe).delete()
        for tag in tags:
            RecipeTag.objects.create(recipe=recipe, tag=tag)
        for ingredient in ingredients:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient['id'],
                amount=ingredient['amount'],
            )

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        self.add_tags_ingredients(recipe, tags, ingredients)
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        self.add_tags_ingredients(instance, tags, ingredients)
        instance.save()
        return instance

    def to_representation(self, instance):
        context = {'request': self.context.get('request')}
        return RecipeGetSerializer(instance, context=context).data


class RecipeShortSerializer(serializers.ModelSerializer):
    """Сериализатор для краткого представления рецепта."""

    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )


class UserSubscriptionsSerializer(serializers.ModelSerializer):
    """Сериализатор для получения подписок пользователя."""

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
        limit_param = self.context['limit_param']
        if limit_param:
            recipes = recipes[: int(limit_param)]
        serializer = RecipeShortSerializer(recipes, many=True, read_only=True)
        return serializer.data

    def get_recipes_count(self, obj):
        """Метод возваращает кол-во рецептов автора."""
        return obj.recipes.count()


class SubscriptionSerializer(serializers.Serializer):
    """Сериализатор для обработки запросов на создание подписки."""

    def validate(self, data):
        request = self.context.get('request')
        action = self.context['action']
        sub = get_object_or_404(User, pk=self.context['user_pk'])
        if request.user == sub:
            raise serializers.ValidationError(
                'Нельзя подписаться на себя!',
            )
        subscription = request.user.subscriptions.filter(author=sub).first()
        if action == 'delete_sub' and not subscription:
            raise serializers.ValidationError(
                'Такой подписки не существует!',
            )
        if action == 'create_sub' and subscription:
            raise serializers.ValidationError(
                'Данная подписка уже существует!',
            )
        return data

    def create(self, validated_data):
        request = self.context.get('request')
        author = get_object_or_404(User, pk=self.context.get('user_pk'))
        subscription, created = Subscription.objects.get_or_create(
            user=request.user,
            author=author,
        )
        if not created:
            raise serializers.ValidationError(
                'Данная подписка уже существует!',
            )
        return UserSubscriptionsSerializer(
            author,
            context={'limit_param': self.context['limit_param']},
        ).data
