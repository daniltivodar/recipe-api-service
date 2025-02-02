from django.contrib import admin

from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)

admin.site.empty_value_display = 'Не задано'


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

    list_display = ('name', 'author', 'amount_add_in_favorite')
    list_filter = ('tags',)
    search_fields = ('name', 'author')

    @admin.display(description='Кол-во добавлений в избранное')
    def amount_add_in_favorite(self, obj):
        return obj.users_favorite.count()


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


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    """Интерфейс админ-зоны ингредиентов в рецептах."""

    list_display = ('recipe', 'ingredient', 'amount')
    list_filter = ('recipe', 'ingredient')
    search_fields = ('recipe',)
    list_display_links = ('recipe',)
