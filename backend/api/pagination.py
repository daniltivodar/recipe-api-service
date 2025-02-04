from rest_framework.pagination import PageNumberPagination


class CustomPagination(PageNumberPagination):
    """Пагинация ответов API."""

    page_size_query_param = "limit"
