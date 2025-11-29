"""
Кастомная пагинация для API.
"""

from rest_framework.pagination import PageNumberPagination


class CustomPageNumberPagination(PageNumberPagination):
    """
    Кастомный пагинатор с параметром 'limit' вместо 'page_size'.

    Используется для соответствия спецификации API.
    """

    page_size = 6
    page_size_query_param = "limit"
    max_page_size = 100
