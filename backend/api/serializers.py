import base64

from django.core.files.base import ContentFile
from django.db.models import F
from rest_framework import serializers

from foodgram import settings
from recipes.models import (
    Favorite, Ingredient, Recipe, RecipeIngredient,
    RecipeTag, ShoppingCart, Tag,
)
from users.serializers import UserGetSerializer



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

    def get_ingredients(self, obj):
        """Возвращает список ингредиентов рецепта с их количеством."""
        return obj.ingredients.values(
            'id',
            'name',
            'measurement_unit',
            amount=F('recipeingredient__amount'),
        )
    
    def get_is_favorited(self, obj):
        """Метод проверяет, добавлен ли рецепт в избранное."""
        if self.context.get('request').user.is_anonymous:
            return False
        return Favorite.objects.filter(
            recipe=obj, user=self.context.get('request').user,
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        """Метод проверяет, добавлен ли рецепт в корзину."""
        if self.context.get('request').user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(
            recipe=obj, user=self.context.get('request').user,
        ).exists()


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

    author = serializers.SlugRelatedField(
        slug_field='username', read_only=True,
    )
    image = Base64ImageField(required=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=True,
    )
    ingredients = RecipeIngredientSerializer(
        many=True,
        required=True,
    )

    class Meta:
        model = Recipe
        fields = (
            'name',
            'ingredients',
            'tags',
            'image',
            'text',
            'cooking_time',
            'author',
        )

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
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
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        RecipeTag.objects.filter(recipe=instance).delete()
        RecipeIngredient.objects.filter(recipe=instance).delete()
        for tag in tags:
            RecipeTag.objects.create(recipe=instance, tag=tag)
        for ingredient in ingredients:
            RecipeIngredient.objects.create(
                recipe=instance,
                ingredient=ingredient['id'],
                amount=ingredient['amount'],
            )
        instance.save()
        return instance

    def to_representation(self, instance):
        context = {'request': self.context.get('request')}
        return RecipeGetSerializer(instance, context=context).data


class RecipeShortSerializer(RecipeGetSerializer):
    """Сериализатор для краткого представления рецепта."""

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'ingredients',
            'author',
            'name',
            'image',
            'text',
            'cooking_time',
        )
