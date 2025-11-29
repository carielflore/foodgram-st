"""
URL configuration for API application.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CustomUserViewSet,
    IngredientViewSet,
    RecipeViewSet,
)

app_name = "api"

# Создаём роутер для автоматической генерации URL
router = DefaultRouter()

# Регистрируем вьюсеты
router.register(r"users", CustomUserViewSet, basename="users")
router.register(r"ingredients", IngredientViewSet, basename="ingredients")
router.register(r"recipes", RecipeViewSet, basename="recipes")

urlpatterns = [
    # Подключаем роутер
    path("", include(router.urls)),
    # Djoser endpoints для аутентификации
    path("auth/", include("djoser.urls.authtoken")),
]
