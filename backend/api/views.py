from django.db.models import Exists, OuterRef, Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import short_url

from api.filters import IngredientFilter, RecipeFilter
from api.pagination import ApiPagination
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (
    FavoriteSerializer,
    IngredientSerializer,
    RecipeGetSerializer,
    RecipePostSerializer,
    ShoppingCartSerializer,
    TagSerializer,
)
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    RecipeShortUrl,
    ShoppingCart,
    Tag,
)


def short_redirect_view(request, short_link):
    """Редиректит на страницу рецепта по короткой ссылке."""
    pk = short_url.decode_url(short_link)
    return redirect(f'/recipes/{pk}/')


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для работы с тегами."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для работы с ингредиентами."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    filterset_class = IngredientFilter
    search_fields = ('name',)
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы с рецептами."""

    pagination_class = ApiPagination
    permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_queryset(self):
        favorited_recipes = Favorite.objects.filter(recipe=OuterRef('pk'))
        cart_recipes = ShoppingCart.objects.filter(recipe=OuterRef('pk'))
        return Recipe.objects.all().annotate(
            is_favorited=Exists(favorited_recipes),
            is_in_shopping_cart=Exists(cart_recipes),
        )

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeGetSerializer
        return RecipePostSerializer

    @action(
        detail=True,
        url_path='get-link',
    )
    def get_link(self, request, pk):
        """Возвращает ссылку рецепта."""
        recipe = get_object_or_404(Recipe, pk=pk)
        short_link = short_url.encode_url(recipe.id)
        RecipeShortUrl.objects.create(recipe=recipe, short_url=short_link)
        recipe.save()
        return Response(
            {'short-link': reverse('short_url', args=(short_link,))},
            status=status.HTTP_201_CREATED,
        )

    def add_favorite_shopping_cart(self, serializer, pk):
        """Метод добавления рецепта в избранное или корзину."""
        serializer = serializer(
            data={'recipe': pk},
            context={'request': self.request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(user=self.request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_favorite_shopping_cart(self, model, pk):
        """Метод удаления рецепта в избранном или корзине."""
        if model.objects.filter(
            recipe=get_object_or_404(Recipe, pk=pk),
            user=self.request.user,
        ).delete():
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=('post',),
        permission_classes=(IsAuthenticated,),
    )
    def favorite(self, request, pk):
        """Метод для работы с избранными рецептами."""
        return self.add_favorite_shopping_cart(FavoriteSerializer, pk)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk):
        """Метод удаления избранного."""
        return self.delete_favorite_shopping_cart(Favorite, pk)

    @action(
        detail=True,
        methods=('post',),
        permission_classes=(IsAuthenticated,),
    )
    def shopping_cart(self, request, pk):
        """Метод для работы с рецептами в корзине."""
        return self.add_favorite_shopping_cart(ShoppingCartSerializer, pk)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk):
        """Метод удаления корзины."""
        return self.delete_favorite_shopping_cart(ShoppingCart, pk)

    @staticmethod
    def get_string():
        return 'Список покупок:\n'

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
    )
    def download_shopping_cart(self, request):
        """Метод для скачивания списка покупок."""
        ingredients = (
            RecipeIngredient.objects.filter(
                recipe__users_shoppingcart__user=request.user,
            )
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(total_amount=Sum('amount'))
            .order_by(
                'ingredient__name',
            )
        )
        content = self.get_string()
        for ingredient in ingredients:
            content += (
                f"{ingredient['ingredient__name']} - "
                f"{ingredient['total_amount']} "
                f"{ingredient['ingredient__measurement_unit']}\n"
            )
        response = FileResponse(content, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_cart.txt"'
        )
        return response
