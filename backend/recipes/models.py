"""
Модели для работы с рецептами, ингредиентами и тегами.
"""

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

# Константы для валидации
MIN_COOKING_TIME = 1
MAX_COOKING_TIME = 32000
MIN_INGREDIENT_AMOUNT = 1
MAX_INGREDIENT_AMOUNT = 32000


class Ingredient(models.Model):
    """
    Модель ингредиента.

    Предустановленный список ингредиентов с единицами измерения
    """

    name = models.CharField(
        "Название",
        max_length=128,
        help_text="Название ингредиента.",
    )

    measurement_unit = models.CharField(
        "Единица измерения",
        max_length=64,
        help_text="Единица измерения (г, кг, мл, шт и т.д.).",
    )

    class Meta:
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["name", "measurement_unit"],
                name="unique_ingredient",
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.measurement_unit})"


class Recipe(models.Model):
    """
    Модель рецепта.

    Основная модель для хранения рецептов пользователей.
    """

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recipes",
        verbose_name="Автор",
        help_text="Автор рецепта.",
    )

    name = models.CharField(
        "Название",
        max_length=256,
        help_text="Название рецепта.",
    )

    image = models.ImageField(
        "Изображение",
        upload_to="recipes/images/",
        help_text="Фото готового блюда.",
    )

    text = models.TextField(
        "Описание",
        help_text="Текстовое описание рецепта.",
    )

    ingredients = models.ManyToManyField(
        Ingredient,
        through="RecipeIngredient",
        related_name="recipes",
        verbose_name="Ингредиенты",
        help_text="Ингредиенты для приготовления блюда.",
    )

    cooking_time = models.PositiveSmallIntegerField(
        "Время приготовления",
        validators=[
            MinValueValidator(
                MIN_COOKING_TIME, message="Минимальное время \
                    приготовления - 1 минута"
            ),
            MaxValueValidator(
                MAX_COOKING_TIME,
                message="Максимальное время приготовления - 32000 минут",
            ),
        ],
        help_text="Время приготовления в минутах.",
    )

    created = models.DateTimeField(
        "Дата публикации",
        auto_now_add=True,
        help_text="Дата и время создания рецепта.",
    )

    class Meta:
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"
        ordering = ["-created"]

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """
    Промежуточная модель для связи рецепта и ингредиента.

    Содержит количество ингредиента в рецепте.
    """

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="recipe_ingredients",
        verbose_name="Рецепт",
    )

    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name="ingredient_recipes",
        verbose_name="Ингредиент",
    )

    amount = models.PositiveSmallIntegerField(
        "Количество",
        validators=[
            MinValueValidator(
                MIN_INGREDIENT_AMOUNT, message="Минимальное количество - 1"
            ),
            MaxValueValidator(
                MAX_INGREDIENT_AMOUNT, message="Максимальное количество \
                    - 32000"
            ),
        ],
        help_text="Количество ингредиента.",
    )

    class Meta:
        verbose_name = "Ингредиент в рецепте"
        verbose_name_plural = "Ингредиенты в рецептах"
        ordering = ["recipe", "ingredient"]
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "ingredient"],
                name="unique_recipe_ingredient",
            )
        ]

    def __str__(self):
        return f"{self.ingredient.name} в {self.recipe.name} - \
            {self.amount} {self.ingredient.measurement_unit}"


class Favorite(models.Model):
    """
    Модель избранных рецептов пользователя.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="favorites",
        verbose_name="Пользователь",
    )

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="favorites",
        verbose_name="Рецепт",
    )

    created = models.DateTimeField(
        "Дата добавления",
        auto_now_add=True,
    )

    class Meta:
        verbose_name = "Избранное"
        verbose_name_plural = "Избранное"
        ordering = ["-created"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"],
                name="unique_favorite",
            )
        ]

    def __str__(self):
        return f"{self.user.username} добавил в избранное {self.recipe.name}"


class ShoppingCart(models.Model):
    """
    Модель списка покупок пользователя.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="shopping_cart",
        verbose_name="Пользователь",
    )

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="shopping_cart",
        verbose_name="Рецепт",
    )

    created = models.DateTimeField(
        "Дата добавления",
        auto_now_add=True,
    )

    class Meta:
        verbose_name = "Список покупок"
        verbose_name_plural = "Списки покупок"
        ordering = ["-created"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"],
                name="unique_shopping_cart",
            )
        ]

    def __str__(self):
        return f"{self.user.username} добавил в покупки {self.recipe.name}"
