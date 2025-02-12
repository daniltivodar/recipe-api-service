from django.contrib.auth import get_user_model
from django.db.models import F
from djoser.serializers import UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.constants import MAX_INGREDIENTS_AMOUNT, MIN_INGREDIENTS_AMOUNT
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from users.models import Subscription

User = get_user_model()


class UserGetSerializer(UserSerializer):
    """Сериализатор для получения информации о пользователях."""

    avatar = Base64ImageField(required=False, allow_null=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        model = User
        fields = UserSerializer.Meta.fields + (
            'avatar',
            'is_subscribed',
        )

    def get_is_subscribed(self, obj):
        """Метод определяет статус подписки на автора."""
        user = self.context.get('request').user
        return (
            obj.subscriptions_to_author.filter(user=user.id).exists()
            and user.is_authenticated
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


class UserSubscriptionSerializer(UserGetSerializer):
    """Сериализатор для получения подписок пользователя."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(default=0)

    class Meta(UserGetSerializer.Meta):
        fields = UserGetSerializer.Meta.fields + (
            'recipes',
            'recipes_count',
        )

    def get_recipes(self, obj):
        """Получение рецептов автора."""
        request = self.context['request']
        recipes = obj.recipes.all()
        recipes_limit = request.query_params.get('recipes_limit')
        if recipes_limit:
            try:
                recipes = recipes[: int(recipes_limit)]
            except ValueError:
                raise serializers.ValidationError('Лимит должен быть числом!')
        return SimpleRecipeSerializer(
            recipes,
            many=True,
            read_only=True,
            context=self.context,
        ).data


class SubscribeSerializer(serializers.ModelSerializer):
    """Сериализатор подписывания на авторов."""

    class Meta:
        model = Subscription
        fields = ('user', 'author')
        read_only_fields = ('user',)

    def validate(self, attrs):
        if Subscription.objects.filter(
            user=self.context['request'].user,
            author=attrs['author'],
        ).exists():
            raise serializers.ValidationError('Вы уже подписались на автора!')
        return attrs

    def to_representation(self, instance):
        return UserGetSerializer(
            instance.author,
            context=self.context,
        ).data


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
    is_favorited = serializers.BooleanField(default=0)
    is_in_shopping_cart = serializers.BooleanField(default=0)
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
            amount=F('recipe_ingredients__amount'),
        )


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов в рецепте."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
    )
    amount = serializers.IntegerField(
        write_only=True,
        min_value=MIN_INGREDIENTS_AMOUNT,
        max_value=MAX_INGREDIENTS_AMOUNT,
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
        slug_field='username',
        read_only=True,
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

    def save_ingredients(self, instance, ingredients_list):
        RecipeIngredient.objects.bulk_create(
            [
                RecipeIngredient(
                    recipe=instance,
                    ingredient=ingredient['id'],
                    amount=ingredient['amount'],
                )
                for ingredient in ingredients_list
            ],
        )

    def create(self, validated_data):
        tags_list = validated_data.pop('tags')
        ingredients_list = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_list)
        self.save_ingredients(recipe, ingredients_list)
        return recipe

    def update(self, instance, validated_data):
        tags_list = validated_data.pop('tags')
        ingredients_list = validated_data.pop('ingredients')
        instance.recipe_ingredients.all().delete()
        instance.tags.set(tags_list)
        self.save_ingredients(instance, ingredients_list)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return RecipeGetSerializer(instance, context=self.context).data


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


class RecipeFavoriteCartSerializer(serializers.ModelSerializer):
    """Абстрактный сериализатор для избранного и корзины."""

    class Meta:
        model = None
        fields = ('user', 'recipe')
        read_only_fields = ('user',)

    def validate(self, attrs):
        if self.Meta.model.objects.filter(
            user=self.context['request'].user,
            recipe=attrs['recipe'],
        ).exists():
            raise serializers.ValidationError(
                f'Рецепт уже добавлен в '
                f'{self.Meta.model._meta.verbose_name.title()}!',
            )
        return attrs

    def to_representation(self, instance):
        return RecipeShortSerializer(
            instance.recipe,
            context=self.context,
        ).data


class FavoriteSerializer(RecipeFavoriteCartSerializer):
    """Сериализатор избранных рецептов."""

    class Meta(RecipeFavoriteCartSerializer.Meta):
        model = Favorite


class ShoppingCartSerializer(RecipeFavoriteCartSerializer):
    """Сериализатор рецептов в корзине."""

    class Meta(RecipeFavoriteCartSerializer.Meta):
        model = ShoppingCart
