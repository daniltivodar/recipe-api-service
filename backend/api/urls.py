from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api import views


v1_router = DefaultRouter()

v1_router.register(
    'ingredients',
    views.IngredientViewSet,
    basename='ingredient',
)
v1_router.register('recipes', views.RecipeViewSet, basename='recipe')
v1_router.register('tags', views.TagViewSet, basename='tag')
v1_router.register('users', views.UserViewSet, basename='user')

urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(v1_router.urls)),
]
