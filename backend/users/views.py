from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.pagination import CustomPagination
from users.models import Subscription
from users.serializers import UserGetSerializer, UserSubscriptionSerializer

User = get_user_model()


class UserViewSet(UserViewSet):
    """Вьюсет для работы с пользователями."""

    queryset = User.objects.all()
    serializer_class = UserGetSerializer
    pagination_class = CustomPagination

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
        methods=['put', 'delete'],
        url_path='me/avatar',
        permission_classes=(IsAuthenticated,),
    )
    def avatar(self, request):
        """Метод для работы с аватаром пользователя."""
        if request.method == 'PUT':
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
        User.objects.filter(
            username=request.user.username,
        ).update(avatar=None)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, permission_classes=(IsAuthenticated,))
    def subscriptions(self, request):
        """Метод возвращает подписки пользователя."""
        users = User.objects.filter(subscribers__user=request.user)
        recipes_limit = request.query_params.get('recipes_limit')
        paginated_queryset = self.paginate_queryset(users)
        serializer = UserSubscriptionSerializer(
            paginated_queryset,
            many=True,
            context={'recipes_limit': recipes_limit},
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,),
    )
    def subscribe(self, request, id):
        """Метод подписки и отписки на авторов."""
        author = get_object_or_404(User, id=id)
        if request.method == 'POST':
            Subscription.objects.create(user=request.user, author=author)
            serializer = UserSubscriptionSerializer(author)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        get_object_or_404(
            Subscription,
            user=request.user,
            author=author,
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
