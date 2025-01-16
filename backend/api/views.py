from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from api.filters import IngredientFilter, RecipeFilter
from api.pagination import CustomPagination
from api.permissions import IsAuthorOrAdmin
from api.serializers import (
    IngredientSerializer,
    RecipeGetSerializer,
    RecipePostSerializer,
    RecipeShortSerializer,
    SubscriptionSerializer,
    TagSerializer,
    UserGetSerializer,
    UserSubscriptionsSerializer,
)
from foodgram import settings
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Subscription,
    Tag,
)

User = get_user_model()


class UserViewSet(UserViewSet):
    """Вьюсет для работы с пользователями."""

    queryset = User.objects.all()
    pagination_class = CustomPagination
    serializer_class = UserGetSerializer

    @action(
        detail=False,
        methods=['get'],
        permission_classes=(IsAuthenticated,),
    )
    def me(self, request):
        """Метод показывает профиль текущего пользователя."""
        serializer = UserGetSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=False,
        url_path='me/avatar',
        methods=['put', 'delete'],
        permission_classes=(IsAuthenticated,),
    )
    def avatar(self, request):
        """Метод для работы с аватаром пользователя."""
        if request.method == 'PUT':
            user = get_object_or_404(User, pk=request.user.pk)
            serializer = UserGetSerializer(
                user,
                data=request.data,
                partial=True,
                context={'request': request},
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                {'avatar': serializer.data.get('avatar')},
                status=status.HTTP_200_OK,
            )
        User.objects.filter(pk=request.user.pk).update(avatar=None)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, permission_classes=(IsAuthenticated,))
    def subscriptions(self, request):
        """Метод возвращает подписки пользователя."""
        users = User.objects.filter(subscribers__user=request.user)
        limit_param = request.query_params.get('recipes_limit')
        paginated_queryset = self.paginate_queryset(users)
        serializer = UserSubscriptionsSerializer(
            paginated_queryset,
            context={'limit_param': limit_param},
            many=True,
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=['post', 'delete'],
        pagination_class=(IsAuthenticated,),
    )
    def subscribe(self, request, id):
        """Метод подписки и отписки на авторов."""
        if request.method == "POST":
            limit_param = request.query_params.get('recipes_limit')
            serializer = SubscriptionSerializer(
                data=request.data,
                context={
                    'request': request,
                    'user_pk': id,
                    'limit_param': limit_param,
                    'action': 'create_sub',
                },
            )
            serializer.is_valid(raise_exception=True)
            subs = serializer.save(pk=id)
            return Response(subs, status=status.HTTP_200_OK)
        serializer = SubscriptionSerializer(
            data=request.data,
            context={
                'request': request,
                'user_pk': id,
                'action': 'delete_sub',
            },
        )
        serializer.is_valid(raise_exception=True)
        get_object_or_404(
            Subscription,
            user=request.user,
            author=get_object_or_404(User, id=id),
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


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
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = CustomPagination

    def get_permissions(self):
        if self.action in ('list', 'retrieve', 'get_link'):
            return (AllowAny(),)
        return (IsAuthenticated(), IsAuthorOrAdmin())

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeGetSerializer
        return RecipePostSerializer

    @action(detail=True, url_path='get-link')
    def get_link(self, request, pk):
        """Возвращает ссылку рецепта."""
        url = f'https://{settings.ALLOWED_HOSTS[0]}/recipes/{pk}'
        return Response({'link': url}, status=status.HTTP_200_OK)

    def add_to(self, model, user, pk):
        """Метод для добавления связи в моделях."""
        if model.objects.filter(user=user, recipe__pk=pk).exists():
            return Response(
                {'errors': 'Рецепт уже добавлен!'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        recipe = get_object_or_404(Recipe, pk=pk)
        model.objects.create(user=user, recipe=recipe)
        serializer = RecipeShortSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_from(self, model, user, pk):
        """Метод для удаления связи в моделях."""
        obj = model.objects.filter(user=user, recipe__pk=pk)
        if obj.exists():
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'errors': 'Рецепт уже добавлен!'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(
        detail=True,
        permission_classes=(IsAuthenticated,),
        methods=['post', 'delete'],
    )
    def favorite(self, request, pk):
        """Метод для работы с корзиной покупок."""
        if request.method == 'POST':
            return self.add_to(Favorite, request.user, pk)
        return self.delete_from(Favorite, request.user, pk)

    @action(
        detail=True,
        permission_classes=(IsAuthenticated,),
        methods=['post', 'delete'],
    )
    def shopping_cart(self, request, pk):
        """Метод для работы с корзиной покупок."""
        if request.method == 'POST':
            return self.add_to(ShoppingCart, request.user, pk)
        return self.delete_from(ShoppingCart, request.user, pk)

    @action(
        detail=False,
        permission_classes=(IsAuthenticated,),
        methods=['get'],
    )
    def download_shopping_cart(self, request):
        """Метод для создания и скачивания списка покупок."""
        shopping_cart = ShoppingCart.objects.filter(user=request.user)
        if not shopping_cart.exists():
            return Response(
                {'detail': 'Список покупок пуст!'},
                status=status.HTTP_404_NOT_FOUND,
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
