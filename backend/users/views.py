from django.contrib.auth import get_user_model
from django.db.models import Count
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.pagination import ApiPagination
from users.models import Subscription
from api.serializers import (
    SubscribeSerializer,
    UserGetSerializer,
    UserSubscriptionSerializer,
)

User = get_user_model()


class UserViewSet(UserViewSet):
    """Вьюсет для работы с пользователями."""

    queryset = User.objects.all()
    serializer_class = UserGetSerializer
    pagination_class = ApiPagination

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
        users = User.objects.filter(
            author_subscribers__user=request.user,
        ).annotate(recipes_count=Count('recipes'))
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
