from django.contrib import admin
from django.contrib.auth.models import Group
from django.utils.safestring import mark_safe

from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    RecipeShortUrl,
    ShoppingCart,
    Tag,
)

admin.site.empty_value_display = 'Не задано'


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    min_num = 1
    extra = 1


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Интерфейс админ-зоны тегов."""

    list_display = ('name', 'slug')
    list_filter = ('name',)
    search_fields = ('name',)
    list_display_links = ('name',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Интерфейс админ-зоны ингредиентов."""

    list_display = (
        'name',
        'measurement_unit',
    )
    list_filter = ('measurement_unit',)
    search_fields = ('name',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Интерфейс админ-зоны рецептов."""

    inlines = (RecipeIngredientInline,)
    list_display = (
        'name',
        'author',
        'amount_add_in_favorite',
        'image',
        'get_tags',
        'get_ingredients',
    )
    list_filter = ('tags',)
    search_fields = ('name', 'author')

    @admin.display(description='Кол-во добавлений в избранное')
    def amount_add_in_favorite(self, obj):
        return obj.users_favorite.count()

    @admin.display(description='Изображение')
    def image(self, obj):
        """Метод возвращает картинку."""
        return mark_safe(f'<img src={obj.image.url} width="80" height="60">')

    @admin.display(description='Теги')
    def get_tags(self, obj):
        """Метод возвращает список тегов."""
        return ', '.join([tag.name for tag in obj.tags.all()])

    @admin.display(description='Ингредиенты')
    def get_ingredients(self, obj):
        """Метод возвращает список ингредиентов."""
        return ', '.join(
            [ingredient.name for ingredient in obj.ingredients.all()],
        )


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Интерфейс админ-зоны избранного."""

    list_display = ('user', 'recipe')
    search_fields = ('user',)
    list_display_links = ('user',)


@admin.register(ShoppingCart)
class ShoppingCart(admin.ModelAdmin):
    """Интерфейс админ-зоны корзины."""

    list_display = ('user', 'recipe')
    search_fields = ('user',)
    list_display_links = ('user',)


@admin.register(RecipeShortUrl)
class RecipeShortUrlAdmin(admin.ModelAdmin):
    """Интерфейс админ-зоны коротких ссылок."""

    list_display = ('recipe', 'short_url')
    list_display_links = ('recipe',)


admin.site.unregister(Group)
