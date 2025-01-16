from django.contrib import admin
from django.contrib.auth import get_user_model

admin.site.empty_value_display = 'Не задано'


@admin.register(get_user_model())
class UserAdmin(admin.ModelAdmin):
    """Интерфейс админ-зоны пользователей."""

    list_display = ('username', 'email')
    search_fields = ('username', 'email')
    list_display_links = ('username',)
