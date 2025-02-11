from rest_framework.pagination import PageNumberPagination


class LimitPagination(PageNumberPagination):
    """Пагинация ответов API."""

    page_size_query_param = 'limit'
