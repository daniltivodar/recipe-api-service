from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

User = get_user_model()


class Tag(models.Model):
    """Модель тегов."""

    name = models.CharField(
        'Название',
        unique=True,
        max_length=settings.NAME_SLUG_MAX_CHAR,
    )
    color = models.CharField(
        'Цвет в HEX',
        unique=True,
        null=True,
        max_length=settings.COLOR_MAX_CHAR,
    )
    slug = models.SlugField(
        'Уникальный слаг',
        unique=True,
        max_length=settings.NAME_SLUG_MAX_CHAR,
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель ингедиентов."""

    name = models.CharField(
        'Название',
        max_length=settings.NAME_SLUG_MAX_CHAR,
    )
    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=settings.NAME_SLUG_MAX_CHAR,
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель рецептов."""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор рецепта',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиенты',
    )
    tags = models.ManyToManyField(
        Tag,
        through='RecipeTag',
        verbose_name='Теги',
    )
    image = models.ImageField('Фото рецепта', upload_to='media/')
    name = models.CharField(
        'Название',
        max_length=settings.NAME_SLUG_MAX_CHAR,
    )
    text = models.TextField('Описание')
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления (в минутах)',
        validators=[MinValueValidator(settings.MIN_COOKING_TIME)],
    )
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """Модель ингедиентов в рецептах."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Название рецепта',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент',
    )
    amount = models.PositiveSmallIntegerField(
        'Кол-во игредиента',
        validators=[MinValueValidator(settings.MIN_INGREDIENTS_AMOUNT)],
    )

    class Meta:
        ordering = ('recipe', 'ingredient')
        verbose_name = 'Игредиент рецепта'
        verbose_name_plural = 'Игредиенты рецепта'
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='unique_ingredients',
            ),
        ]

    def __str__(self):
        return f'{self.ingredient} в кол-ве {self.amount}'


class RecipeTag(models.Model):
    """Модель тегов в рецепте."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_tags',
        verbose_name='Название рецепта',
    )
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, verbose_name='Тег')

    class Meta:
        ordering = ('recipe', 'tag')
        verbose_name = 'Тег рецепта'
        verbose_name_plural = 'Теги рецепта'
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'tag'),
                name='unique_recipe_tags',
            ),
        ]

    def __str__(self):
        return f'{self.tag} рецепта {self.recipe}'


class Favorite(models.Model):
    """Модель избранных рецептов."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='users_favorite',
        verbose_name='Название рецепта',
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь',
    )

    class Meta:
        ordering = ('recipe',)
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'user'),
                name='unique_favorite_recipe',
            ),
        ]

    def __str__(self):
        return f'Избранный рецепт {self.recipe} пользователя {self.user}'


class ShoppingCart(models.Model):
    """Модель корзины покупок."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='users_shopping_cart',
        verbose_name='Название рецепта',
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Пользователь',
    )

    class Meta:
        ordering = ('recipe',)
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзина'
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'user'),
                name='unique_shopping_cart_recipe',
            ),
        ]

    def __str__(self):
        return f'Рецепт {self.recipe} в корзине пользователя {self.user}'


class Subscription(models.Model):
    """Модель подписок пользователя."""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name='Автор рецептов',
    )
    user = models.ForeignKey(
        User,
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
