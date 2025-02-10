from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from recipes import constants

User = get_user_model()


class FavoriteShoppingCart(models.Model):
    """Абастрактная модель для классов избранного и корзины."""

    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE,
        related_name='users_%(class)s',
        verbose_name='Название рецепта',
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='%(class)s',
        verbose_name='Пользователь',
    )

    class Meta:
        abstract = True

    def __str__(self):
        return (
            f'Рецепт {self.recipe} пользователя {self.user}, '
            f'добавлен в {self._meta.verbose_name}'
        )


class Tag(models.Model):
    """Модель тегов."""

    name = models.CharField(
        'Название',
        unique=True,
        max_length=constants.NAME_SLUG_TAG_MAX_CHAR,
    )
    slug = models.SlugField(
        'Уникальный слаг',
        unique=True,
        max_length=constants.NAME_SLUG_TAG_MAX_CHAR,
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель ингредиентов."""

    name = models.CharField(
        'Название',
        max_length=constants.NAME_INGREDIENT_MAX_CHAR,
    )
    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=constants.MEASUREMENT_UNIT_MAX_CHAR,
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = (
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_name_measurement_unit',
            ),
        )

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
        verbose_name='Теги',
    )
    image = models.ImageField('Фото рецепта', upload_to='media/')
    name = models.CharField(
        'Название',
        max_length=constants.NAME_SLUG_MAX_CHAR,
    )
    text = models.TextField('Описание')
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления (в минутах)',
        validators=[
            MinValueValidator(constants.MIN_COOKING_TIME),
            MaxValueValidator(constants.MAX_COOKING_TIME),
        ],
    )
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class RecipeShortUrl(models.Model):
    """Модель короткой ссылки."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )
    short_url = models.CharField(
        'Короткая ссылка',
        max_length=constants.SHORT_URL_MAX,
        unique=True,
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ('-recipe__pub_date',)
        verbose_name = 'Короткая ссылка'
        verbose_name_plural = 'Короткие ссылки'
        constraints = (
            models.UniqueConstraint(
                fields=('recipe', 'short_url'),
                name='unique_short_url',
            ),
        )

    def __str__(self):
        return self.short_url


class RecipeIngredient(models.Model):
    """Модель ингредиентов в рецептах."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Название рецепта',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Ингредиент',
    )
    amount = models.PositiveSmallIntegerField(
        'Кол-во ингредиента',
        validators=[
            MinValueValidator(constants.MIN_INGREDIENTS_AMOUNT),
            MaxValueValidator(constants.MAX_INGREDIENTS_AMOUNT),
        ],
    )

    class Meta:
        ordering = ('recipe', 'ingredient')
        verbose_name = 'Ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецепта'
        constraints = (
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='unique_ingredients',
            ),
        )

    def __str__(self):
        return f'{self.ingredient} в кол-ве {self.amount}'


class Favorite(FavoriteShoppingCart):
    """Модель избранных рецептов."""

    class Meta:
        ordering = ('recipe',)
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        constraints = (
            models.UniqueConstraint(
                fields=('recipe', 'user'),
                name='unique_favorite_recipe',
            ),
        )


class ShoppingCart(FavoriteShoppingCart):
    """Модель корзины покупок."""

    class Meta:
        ordering = ('recipe',)
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзина'
        constraints = (
            models.UniqueConstraint(
                fields=('recipe', 'user'),
                name='unique_shopping_cart_recipe',
            ),
        )
