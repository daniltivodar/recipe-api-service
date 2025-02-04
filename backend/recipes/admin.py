from django.contrib import admin

from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeTag,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)

admin.site.empty_value_display = 'Не задано'


class RecipeTagInline(admin.TabularInline):
    model = RecipeTag
    min_num = 1
    extra = 1


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    min_num = 1
    extra = 1


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Интерфейс админ-зоны тегов."""

    inlines = (RecipeTagInline,)
    list_display = ('name', 'slug')
    list_filter = ('name',)
    search_fields = ('name',)
    list_display_links = ('name',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Интерфейс админ-зоны ингредиентов."""

    inlines = (RecipeIngredientInline,)
    list_display = (
        'name',
        'measurement_unit',
    )
    list_filter = ('measurement_unit',)
    search_fields = ('name',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Интерфейс админ-зоны рецептов."""

    inlines = (RecipeTagInline, RecipeIngredientInline)
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
