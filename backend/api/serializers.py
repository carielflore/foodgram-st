"""
Сериализаторы для API приложения.
"""

import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from djoser.serializers import UserCreateSerializer, UserSerializer
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
)
from rest_framework import serializers
from users.models import Subscription

from .fields import Base64ImageField

User = get_user_model()


# ============================================================================
# User Serializers
# ============================================================================


class CustomUserSerializer(UserSerializer):
    """
    Сериализатор для отображения пользователя.

    Добавлено поле is_subscribed - подписан ли текущий пользователь на этого.
    """

    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "avatar",
        )

    def get_is_subscribed(self, obj):
        """
        Проверяет, подписан ли текущий пользователь на данного автора.

        Returns:
            bool: True если подписан, False если нет или пользователь не авторизован
        """
        request = self.context.get("request")
        if not request or request.user.is_anonymous:
            return False

        return Subscription.objects.filter(user=request.user, author=obj).exists()

    def get_avatar(self, obj):
        """
        Возвращает полный URL аватара или None.

        Returns:
            str or None: URL аватара или None
        """
        if obj.avatar:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None


class CustomUserCreateSerializer(UserCreateSerializer):
    """
    Сериализатор для регистрации нового пользователя.

    Все поля обязательны для заполнения.
    """

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "password",
        )
        extra_kwargs = {
            "password": {"write_only": True},
            "email": {"required": True},
            "username": {"required": True},
            "first_name": {"required": True},
            "last_name": {"required": True},
        }

    def validate_email(self, value):
        """Проверка уникальности email."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "Пользователь с таким email уже существует."
            )
        return value

    def validate_username(self, value):
        """Проверка уникальности username."""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                "Пользователь с таким username уже существует."
            )
        return value


class SetAvatarSerializer(serializers.ModelSerializer):
    """
    Сериализатор для установки аватара пользователя.

    Принимает изображение в формате Base64.
    """

    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ("avatar",)

    def validate_avatar(self, value):
        """Валидация аватара."""
        if not value:
            raise serializers.ValidationError("Необходимо загрузить изображение.")
        return value


class SetAvatarResponseSerializer(serializers.ModelSerializer):
    """
    Сериализатор для ответа после установки аватара.

    Возвращает только URL аватара.
    """

    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("avatar",)

    def get_avatar(self, obj):
        """Возвращает полный URL аватара."""
        if obj.avatar:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None


# ============================================================================
# Recipe Serializers
# ============================================================================


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиента."""

    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """
    Сериализатор для ингредиента в рецепте (для отображения).

    Включает полную информацию об ингредиенте.
    """

    id = serializers.ReadOnlyField(source="ingredient.id")
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(source="ingredient.measurement_unit")

    class Meta:
        model = RecipeIngredient
        fields = ("id", "name", "measurement_unit", "amount")


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для добавления ингредиента в рецепт (для создания/обновления).

    Принимает только id ингредиента и количество.
    """

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(), source="ingredient"
    )
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = RecipeIngredient
        fields = ("id", "amount")


class RecipeListSerializer(serializers.ModelSerializer):
    """
    Сериализатор для отображения рецепта в списке и детально.

    Включает всю информацию о рецепте с вычисляемыми полями.
    """

    author = CustomUserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        many=True, read_only=True, source="recipe_ingredients"
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            "id",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )

    def get_is_favorited(self, obj):
        """Проверяет, добавлен ли рецепт в избранное текущим пользователем."""
        request = self.context.get("request")
        if not request or request.user.is_anonymous:
            return False

        return Favorite.objects.filter(user=request.user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        """Проверяет, добавлен ли рецепт в список покупок текущим пользователем."""
        request = self.context.get("request")
        if not request or request.user.is_anonymous:
            return False

        return ShoppingCart.objects.filter(user=request.user, recipe=obj).exists()

    def get_image(self, obj):
        """Возвращает полный URL изображения."""
        if obj.image:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class RecipeCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания и обновления рецепта.

    Обрабатывает связи M2M для ингредиентов и тегов.
    """

    ingredients = RecipeIngredientCreateSerializer(many=True)
    image = Base64ImageField()
    author = CustomUserSerializer(read_only=True)
    cooking_time = serializers.IntegerField(min_value=1)

    class Meta:
        model = Recipe
        fields = (
            "id",
            "author",
            "ingredients",
            "name",
            "image",
            "text",
            "cooking_time",
        )

    def validate_ingredients(self, value):
        """
        Валидация ингредиентов.

        Проверяет:
        - Наличие хотя бы одного ингредиента
        - Отсутствие дубликатов
        """
        if not value:
            raise serializers.ValidationError(
                "Необходимо добавить хотя бы один ингредиент."
            )

        # Проверка на дубликаты
        ingredient_ids = [item["ingredient"].id for item in value]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError("Ингредиенты не должны повторяться.")

        return value

    def create_ingredients(self, recipe, ingredients_data):
        """
        Создаёт связи рецепта с ингредиентами.

        Args:
            recipe: Экземпляр рецепта
            ingredients_data: Список словарей с данными об ингредиентах
        """
        RecipeIngredient.objects.bulk_create(
            [
                RecipeIngredient(
                    recipe=recipe,
                    ingredient=ingredient_data["ingredient"],
                    amount=ingredient_data["amount"],
                )
                for ingredient_data in ingredients_data
            ]
        )

    def create(self, validated_data):
        """
        Создание рецепта с ингредиентами.

        Обрабатывает связи M2M отдельно от основной модели.
        """
        ingredients_data = validated_data.pop("ingredients")

        # Устанавливаем автора из контекста запроса
        validated_data["author"] = self.context["request"].user

        # Создаём рецепт
        recipe = Recipe.objects.create(**validated_data)

        # Добавляем ингредиенты
        self.create_ingredients(recipe, ingredients_data)

        return recipe

    def update(self, instance, validated_data):
        """
        Обновление рецепта с ингредиентами.

        Удаляет старые связи и создаёт новые.
        Согласно спецификации, ingredients обязательны даже при PATCH.
        """
        # Проверяем наличие обязательного поля ingredients
        if "ingredients" not in validated_data:
            raise serializers.ValidationError(
                {"ingredients": "Это поле обязательно при обновлении рецепта."}
            )

        ingredients_data = validated_data.pop("ingredients")

        # Обновляем основные поля
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Обновляем ингредиенты
        # Удаляем старые
        instance.recipe_ingredients.all().delete()
        # Создаём новые
        self.create_ingredients(instance, ingredients_data)

        return instance

    def to_representation(self, instance):
        """
        Для ответа используем RecipeListSerializer.

        Это обеспечивает единообразный формат ответа.
        """
        return RecipeListSerializer(instance, context=self.context).data


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    """
    Минимальный сериализатор рецепта.

    Используется для отображения в избранном, списке покупок и подписках.
    """

    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")

    def get_image(self, obj):
        """Возвращает полный URL изображения."""
        if obj.image:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class RecipeGetShortLinkSerializer(serializers.Serializer):
    """
    Сериализатор для короткой ссылки на рецепт.

    Возвращает сокращённую ссылку на рецепт.
    """

    def to_representation(self, instance):
        """Override to rename short_link to short-link in output."""
        ret = super().to_representation(instance)
        if "short_link" in ret:
            ret["short-link"] = ret.pop("short_link")
        return ret

    short_link = serializers.SerializerMethodField()

    def get_short_link(self, obj):
        """
        Генерирует короткую ссылку на рецепт.

        Использует base62 кодирование ID рецепта для создания короткого кода.
        """
        request = self.context.get("request")
        if not request:
            return None

        # Простая генерация короткой ссылки на основе ID
        # В production можно использовать более сложный алгоритм
        recipe_id = obj.id
        short_code = self._encode_base62(recipe_id)

        return request.build_absolute_uri(f"/s/{short_code}")

    @staticmethod
    def _encode_base62(num):
        """
        Кодирует число в base62.

        Args:
            num: Число для кодирования

        Returns:
            str: Закодированная строка
        """
        alphabet = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        if num == 0:
            return alphabet[0]

        result = []
        while num:
            num, rem = divmod(num, 62)
            result.append(alphabet[rem])

        return "".join(reversed(result))


class UserWithRecipesSerializer(CustomUserSerializer):
    """
    Расширенный сериализатор пользователя с рецептами.

    Используется для отображения подписок.
    Включает рецепты автора и их общее количество.
    """

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(CustomUserSerializer.Meta):
        fields = CustomUserSerializer.Meta.fields + ("recipes", "recipes_count")

    def get_recipes(self, obj):
        """
        Возвращает рецепты автора.

        Количество рецептов ограничивается параметром recipes_limit.
        """
        request = self.context.get("request")
        recipes_limit = None

        if request:
            recipes_limit = request.query_params.get("recipes_limit")

        recipes = obj.recipes.all()

        if recipes_limit:
            try:
                recipes = recipes[: int(recipes_limit)]
            except (ValueError, TypeError):
                pass

        return RecipeMinifiedSerializer(recipes, many=True, context=self.context).data

    def get_recipes_count(self, obj):
        """Возвращает общее количество рецептов автора."""
        return obj.recipes.count()
