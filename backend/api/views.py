"""
Вьюсеты для API приложения.
"""

from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from users.models import Subscription

from .permissions import IsAuthorOrReadOnly
from .serializers import (
    CustomUserSerializer,
    IngredientSerializer,
    RecipeCreateSerializer,
    RecipeGetShortLinkSerializer,
    RecipeListSerializer,
    RecipeMinifiedSerializer,
    SetAvatarResponseSerializer,
    SetAvatarSerializer,
    UserWithRecipesSerializer,
)

User = get_user_model()


class CustomUserViewSet(DjoserUserViewSet):
    """
    Вьюсет для работы с пользователями.

    Расширяет стандартный Djoser UserViewSet дополнительными эндпоинтами:
    - /me/avatar/ - управление аватаром
    - /subscriptions/ - список подписок
    - /{id}/subscribe/ - подписка/отписка на автора
    """

    queryset = User.objects.all()
    serializer_class = CustomUserSerializer

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[IsAuthenticated],
    )
    def me(self, request):
        """
        Получить информацию о текущем пользователе.

        Переопределяет стандартное действие Djoser для явной проверки аутентификации.
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=["put", "delete"],
        url_path="me/avatar",
        permission_classes=[IsAuthenticated],
    )
    def avatar(self, request):
        """
        Управление аватаром текущего пользователя.

        PUT - установить новый аватар
        DELETE - удалить аватар
        """
        user = request.user

        if request.method == "PUT":
            serializer = SetAvatarSerializer(user, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            response_serializer = SetAvatarResponseSerializer(
                user, context={"request": request}
            )
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        if request.method == "DELETE":
            if user.avatar:
                user.avatar.delete(save=True)
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[IsAuthenticated],
    )
    def subscriptions(self, request):
        """
        Получить список подписок текущего пользователя.

        Возвращает пагинированный список авторов, на которых подписан пользователь.
        """
        user = request.user
        subscriptions = Subscription.objects.filter(user=user)
        authors = User.objects.filter(
            id__in=subscriptions.values_list("author_id", flat=True)
        )

        # Пагинация
        page = self.paginate_queryset(authors)
        if page is not None:
            serializer = UserWithRecipesSerializer(
                page, many=True, context={"request": request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = UserWithRecipesSerializer(
            authors, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[IsAuthenticated],
    )
    def subscribe(self, request, id=None):
        """
        Подписка/отписка на автора.

        POST - подписаться на автора
        DELETE - отписаться от автора
        """
        user = request.user
        author = self.get_object()

        # Проверка: нельзя подписаться на самого себя
        if user == author:
            return Response(
                {"errors": "Нельзя подписаться на самого себя."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if request.method == "POST":
            # Проверка существования подписки
            if Subscription.objects.filter(user=user, author=author).exists():
                return Response(
                    {"errors": "Вы уже подписаны на этого автора."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Создание подписки
            Subscription.objects.create(user=user, author=author)
            serializer = UserWithRecipesSerializer(author, context={"request": request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == "DELETE":
            # Проверка существования подписки
            subscription = Subscription.objects.filter(user=user, author=author)
            if not subscription.exists():
                return Response(
                    {"errors": "Вы не подписаны на этого автора."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Вьюсет для работы с ингредиентами.

    Только чтение (list, retrieve).
    Поддерживает поиск по названию (начало строки, без учета регистра).
    """

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    pagination_class = None  # Отключаем пагинацию для ингредиентов

    def get_queryset(self):
        """
        Фильтрация ингредиентов по имени.

        Поиск по вхождению в начало названия без учета регистра.
        """
        queryset = Ingredient.objects.all()
        name = self.request.query_params.get("name")

        if name:
            queryset = queryset.filter(name__istartswith=name)

        return queryset


class RecipeViewSet(viewsets.ModelViewSet):
    """
    Вьюсет для работы с рецептами.

    Полный CRUD + дополнительные эндпоинты:
    - /get-link/ - получить короткую ссылку
    - /favorite/ - добавить/удалить из избранного
    - /shopping_cart/ - добавить/удалить из списка покупок
    - /download_shopping_cart/ - скачать список покупок
    """

    queryset = Recipe.objects.all()
    permission_classes = [IsAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend]

    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от действия."""
        if self.action in ["create", "update", "partial_update"]:
            return RecipeCreateSerializer
        return RecipeListSerializer

    def get_queryset(self):
        """
        Оптимизация запросов и фильтрация.

        Фильтры:
        - author - ID автора
        - is_favorited - в избранном (только для авторизованных)
        - is_in_shopping_cart - в списке покупок (только для авторизованных)
        """
        queryset = Recipe.objects.select_related("author").prefetch_related(
            "ingredients", "recipe_ingredients__ingredient"
        )

        # Фильтр по автору
        author_id = self.request.query_params.get("author")
        if author_id:
            queryset = queryset.filter(author_id=author_id)

        # Фильтры для авторизованных пользователей
        if self.request.user.is_authenticated:
            is_favorited = self.request.query_params.get("is_favorited")
            if is_favorited == "1":
                queryset = queryset.filter(favorites__user=self.request.user)

            is_in_shopping_cart = self.request.query_params.get("is_in_shopping_cart")
            if is_in_shopping_cart == "1":
                queryset = queryset.filter(shopping_cart__user=self.request.user)

        return queryset.distinct()

    @action(detail=True, methods=["get"], url_path="get-link")
    def get_link(self, request, pk=None):
        """
        Получить короткую ссылку на рецепт.

        Возвращает сокращённую ссылку вида https://example.com/s/{code}
        """
        recipe = self.get_object()
        serializer = RecipeGetShortLinkSerializer(recipe, context={"request": request})
        return Response(serializer.data)

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        """
        Добавить/удалить рецепт в избранное.

        POST - добавить в избранное
        DELETE - удалить из избранного
        """
        recipe = self.get_object()
        user = request.user

        if request.method == "POST":
            if Favorite.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {"errors": "Рецепт уже добавлен в избранное."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            Favorite.objects.create(user=user, recipe=recipe)
            serializer = RecipeMinifiedSerializer(recipe, context={"request": request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == "DELETE":
            favorite = Favorite.objects.filter(user=user, recipe=recipe)
            if not favorite.exists():
                return Response(
                    {"errors": "Рецепт не найден в избранном."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[IsAuthenticated],
    )
    def shopping_cart(self, request, pk=None):
        """
        Добавить/удалить рецепт в список покупок.

        POST - добавить в список покупок
        DELETE - удалить из списка покупок
        """
        recipe = self.get_object()
        user = request.user

        if request.method == "POST":
            if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {"errors": "Рецепт уже добавлен в список покупок."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            ShoppingCart.objects.create(user=user, recipe=recipe)
            serializer = RecipeMinifiedSerializer(recipe, context={"request": request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == "DELETE":
            shopping_cart = ShoppingCart.objects.filter(user=user, recipe=recipe)
            if not shopping_cart.exists():
                return Response(
                    {"errors": "Рецепт не найден в списке покупок."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            shopping_cart.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[IsAuthenticated],
    )
    def download_shopping_cart(self, request):
        """
        Скачать список покупок в текстовом формате.

        Агрегирует ингредиенты из всех рецептов в списке покупок,
        суммирует количество одинаковых ингредиентов.
        """
        user = request.user

        # Получаем все рецепты из списка покупок
        shopping_cart = ShoppingCart.objects.filter(user=user)
        recipes = Recipe.objects.filter(id__in=shopping_cart.values("recipe_id"))

        # Агрегируем ингредиенты
        ingredients = (
            recipes.values(
                "recipe_ingredients__ingredient__name",
                "recipe_ingredients__ingredient__measurement_unit",
            )
            .annotate(total_amount=Sum("recipe_ingredients__amount"))
            .order_by("recipe_ingredients__ingredient__name")
        )

        # Формируем текстовый файл
        lines = ["Список покупок\n", "=" * 50, "\n\n"]

        for item in ingredients:
            name = item["recipe_ingredients__ingredient__name"]
            unit = item["recipe_ingredients__ingredient__measurement_unit"]
            amount = item["total_amount"]
            lines.append(f"{name} ({unit}) — {amount}\n")

        # Добавляем footer
        lines.append("\n" + "=" * 50)
        lines.append(f"\n\nВсего ингредиентов: {len(ingredients)}")

        content = "".join(lines)

        # Возвращаем как текстовый файл
        response = HttpResponse(content, content_type="text/plain; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="shopping_list.txt"'

        return response
