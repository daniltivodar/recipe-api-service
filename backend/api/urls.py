from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (
    IngredientViewSet,
    RecipeViewSet,
    TagViewSet,
    UserViewSet,
)

v1_router = DefaultRouter()

v1_router.register('ingredients', IngredientViewSet, basename='ingredient')
v1_router.register('recipes', RecipeViewSet, basename='recipe')
v1_router.register('tags', TagViewSet, basename='tag')
v1_router.register('users', UserViewSet, basename='user')


urlpatterns = [
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(v1_router.urls)),
]
