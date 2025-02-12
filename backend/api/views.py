from django.contrib.auth import get_user_model
from django.db.models import Count, Exists, OuterRef, Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import short_url

from api.filters import IngredientFilter, RecipeFilter
from api.pagination import LimitPagination
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (
    FavoriteSerializer,
    IngredientSerializer,
    RecipeGetSerializer,
    RecipePostSerializer,
    ShoppingCartSerializer,
    SubscribeSerializer,
    TagSerializer,
    UserGetSerializer,
    UserSubscriptionSerializer,
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
from users.models import Subscription

User = get_user_model()


class UserViewSet(UserViewSet):
    """Вьюсет для работы с пользователями."""

    queryset = User.objects.all()
    serializer_class = UserGetSerializer
    pagination_class = LimitPagination

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
    )
    def me(self, request):
        """Метод показывает профиль текущего пользователя."""
        serializer = UserGetSerializer(
            request.user,
            context={'request': request},
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=('put',),
        url_path='me/avatar',
        permission_classes=(IsAuthenticated,),
    )
    def avatar(self, request):
        """Метод для работы с аватаром пользователя."""
        user = get_object_or_404(User, username=request.user.username)
        serializer = UserGetSerializer(
            user,
            partial=True,
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @avatar.mapping.delete
    def delete_avatar(self, request):
        """Метод удаления аватара."""
        request.user.avatar.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, permission_classes=(IsAuthenticated,))
    def subscriptions(self, request):
        """Метод возвращает подписки пользователя."""
        users = (
            User.objects.filter(
                subscriptions_to_author__user=request.user,
            )
            .annotate(recipes_count=Count('recipes'))
            .order_by('username')
        )
        paginated_queryset = self.paginate_queryset(users)
        serializer = UserSubscriptionSerializer(
            paginated_queryset,
            many=True,
            context={'request': request},
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=('post',),
        permission_classes=(IsAuthenticated,),
    )
    def subscribe(self, request, id):
        """Метод подписки и отписки на авторов."""
        serializer = SubscribeSerializer(
            data={'author': id},
            context={'request': self.request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(user=self.request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def delete_subscribe(self, request, id):
        if Subscription.objects.filter(
            author=get_object_or_404(User, id=id),
            user=self.request.user,
        ).delete():
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)


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

    pagination_class = LimitPagination
    permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_queryset(self):
        favorited_recipes = Favorite.objects.filter(
            recipe=OuterRef('pk'),
            user=self.request.user.id,
        )
        cart_recipes = ShoppingCart.objects.filter(
            recipe=OuterRef('pk'),
            user=self.request.user.id,
        )
        queryset = Recipe.objects.select_related(
            'author',
        ).all().prefetch_related('tags', 'ingredients')
        if self.request.user.is_authenticated:
            return (
                queryset.annotate(
                    is_favorited=Exists(favorited_recipes),
                    is_in_shopping_cart=Exists(cart_recipes),
                )
            )
        return queryset

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
    def get_shopping_cart_list(ingredients):
        content = 'Список покупок:\n'
        for ingredient in ingredients:
            content += (
                f'{ingredient["ingredient__name"]} - '
                f'{ingredient["total_amount"]} '
                f'{ingredient["ingredient__measurement_unit"]}\n'
            )
        return content

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
        content = self.get_shopping_cart_list(ingredients)
        response = FileResponse(content, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_cart.txt"'
        )
        return response
