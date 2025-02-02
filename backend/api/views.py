from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from api.filters import IngredientFilter, RecipeFilter
from api.pagination import CustomPagination
from api.permissions import IsAuthorOrAdmin
from api.serializers import (
    IngredientSerializer,
    TagSerializer,
    RecipeGetSerializer,
    RecipePostSerializer,
    RecipeShortSerializer,
)
from foodgram import settings
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)


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
    search_fields = ['name']
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы с рецептами."""

    queryset = Recipe.objects.all()
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_permissions(self):
        if self.action in ('list', 'retrieve', 'get_link'):
            return (AllowAny(),)
        return (IsAuthenticated(), IsAuthorOrAdmin())

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
        url = f'https://{settings.ALLOWED_HOSTS[0]}/recipes/{pk}'
        return Response({'short-link': url}, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,),
    )
    def favorite(self, request, pk):
        """Метод для работы с избранными рецептами."""
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            Favorite.objects.create(recipe=recipe, user=request.user)
            serializer = RecipeShortSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        get_object_or_404(Favorite, recipe=recipe, user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,),
    )
    def shopping_cart(self, request, pk):
        """Метод для работы с рецептами в корзине."""
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            ShoppingCart.objects.create(recipe=recipe, user=request.user)
            serializer = RecipeShortSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        get_object_or_404(
            ShoppingCart,
            recipe=recipe,
            user=request.user,
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=(IsAuthenticated,),
    )
    def download_shopping_cart(self, request):
        """Метод для скачивания списка покупок."""
        shopping_cart = ShoppingCart.objects.filter(user=request.user)
        if len(shopping_cart) == 0:
            return Response(
                {'detail': 'Список покупок пуст!'},
                status=status.HTTP_204_NO_CONTENT,
            )
        recipe_ingredients = {}
        for item in shopping_cart:
            for recipe_ingredient in RecipeIngredient.objects.filter(
                recipe=item.recipe,
            ):
                ingredient = recipe_ingredient.ingredient
                name = ingredient.name
                unit = ingredient.measurement_unit
                amount = recipe_ingredient.amount
                if name in recipe_ingredients:
                    recipe_ingredients[name]['amount'] += amount
                else:
                    recipe_ingredients[name] = {
                        'amount': amount,
                        'unit': unit,
                    }
        content = 'Список покупок:\n'
        for name, data in recipe_ingredients.items():
            content += f"{name} - {data['amount']} {data['unit']}\n"
        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_cart.txt"'
        )
        return response
