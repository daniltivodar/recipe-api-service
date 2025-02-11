from django.shortcuts import redirect
import short_url


def short_redirect_view(request, short_link):
    """Редиректит на страницу рецепта по короткой ссылке."""
    pk = short_url.decode_url(short_link)
    return redirect(f'/recipes/{pk}/')
