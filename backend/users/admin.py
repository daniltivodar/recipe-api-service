from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from users.models import Subscription

admin.site.empty_value_display = 'Не задано'


@admin.register(get_user_model())
class UserAdmin(BaseUserAdmin):
    """Интерфейс админ-зоны пользователей."""

    list_display = ('username', 'email')
    search_fields = ('username', 'email')
    list_display_links = ('username',)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Интерфейс админ-зоны подписок."""

    list_display = ('user', 'author')
    search_fields = ('user',)
    list_display_links = ('user',)
