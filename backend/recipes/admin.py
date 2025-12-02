"""
Настройка админ-панели для приложения recipes.
"""

from django.contrib import admin
from django.db.models import Count

from .models import (
    Favorite, Ingredient, Recipe, RecipeIngredient, ShoppingCart
)


class RecipeIngredientInline(admin.TabularInline):
    """Inline для отображения ингредиентов в рецепте."""

    model = RecipeIngredient
    extra = 1
    min_num = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Настройка админ-панели для модели Recipe."""

    list_display = (
        "id",
        "name",
        "author",
        "get_favorites_count",
        "created",
    )
    list_filter = ("created",)
    search_fields = ("name", "author__username", "author__email")
    inlines = [RecipeIngredientInline]
    ordering = ("-created",)
    readonly_fields = ("created", "get_favorites_count")

    fieldsets = (
        (
            "Основная информация",
            {
                "fields": (
                    "author",
                    "name",
                    "image",
                    "text",
                    "cooking_time",
                )
            },
        ),
        (
            "Статистика",
            {"fields": ("created", "get_favorites_count")},
        ),
    )

    def get_queryset(self, request):
        """Оптимизация запросов с аннотацией количества добавлений в избранное."""
        queryset = super().get_queryset(request)
        return queryset.select_related("author").annotate(
            favorites_count=Count("favorites")
        )

    @admin.display(description="Добавлено в избранное")
    def get_favorites_count(self, obj):
        """Возвращает количество добавлений рецепта в избранное."""
        return (
            obj.favorites_count
            if hasattr(obj, "favorites_count")
            else obj.favorites.count()
        )


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Настройка админ-панели для модели Ingredient."""

    list_display = ("id", "name", "measurement_unit")
    list_filter = ("measurement_unit",)
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    """Настройка админ-панели для модели RecipeIngredient."""

    list_display = ("id", "recipe", "ingredient", "amount")
    list_filter = ("recipe", "ingredient")
    search_fields = ("recipe__name", "ingredient__name")
    ordering = ("recipe", "ingredient")

    def get_queryset(self, request):
        """Оптимизация запросов."""
        queryset = super().get_queryset(request)
        return queryset.select_related("recipe", "ingredient")


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Настройка админ-панели для модели Favorite."""

    list_display = ("id", "user", "recipe", "created")
    list_filter = ("created",)
    search_fields = ("user__username", "user__email", "recipe__name")
    ordering = ("-created",)

    def get_queryset(self, request):
        """Оптимизация запросов."""
        queryset = super().get_queryset(request)
        return queryset.select_related("user", "recipe")


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Настройка админ-панели для модели ShoppingCart."""

    list_display = ("id", "user", "recipe", "created")
    list_filter = ("created",)
    search_fields = ("user__username", "user__email", "recipe__name")
    ordering = ("-created",)

    def get_queryset(self, request):
        """Оптимизация запросов."""
        queryset = super().get_queryset(request)
        return queryset.select_related("user", "recipe")
