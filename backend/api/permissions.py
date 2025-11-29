"""
Кастомные права доступа для API.
"""

from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Разрешение, которое позволяет редактировать объект только его автору.

    Анонимные пользователи имеют доступ только на чтение.
    Авторизованные пользователи могут создавать объекты.
    Редактировать и удалять может только автор или администратор.
    """

    def has_permission(self, request, view):
        """
        Проверка прав на уровне запроса.

        Чтение доступно всем.
        Создание доступно только авторизованным.
        """
        return (
            request.method in permissions.SAFE_METHODS or request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        """
        Проверка прав на уровне объекта.

        Чтение доступно всем.
        Изменение и удаление только автору или администратору.
        """
        # Чтение разрешено всем
        if request.method in permissions.SAFE_METHODS:
            return True

        # Редактирование и удаление только автору или администратору
        return obj.author == request.user or request.user.is_staff


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Разрешение для администраторов.

    Чтение доступно всем.
    Изменение только администраторам.
    """

    def has_permission(self, request, view):
        """Проверка прав доступа."""
        return request.method in permissions.SAFE_METHODS or (
            request.user.is_authenticated and request.user.is_staff
        )


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Разрешение для владельца объекта.

    Чтение доступно всем.
    Изменение только владельцу (user) или администратору.
    """

    def has_object_permission(self, request, view, obj):
        """Проверка прав на уровне объекта."""
        # Чтение разрешено всем
        if request.method in permissions.SAFE_METHODS:
            return True

        # Редактирование только владельцу или администратору
        return obj.user == request.user or request.user.is_staff
