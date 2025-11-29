"""
Кастомные поля для сериализаторов API.
"""

import base64
import uuid

from django.core.files.base import ContentFile
from rest_framework import serializers


class Base64ImageField(serializers.ImageField):
    """
    Поле для работы с изображениями в формате Base64.

    Фронтенд отправляет изображения в формате:
    "data:image/png;base64,iVBORw0KGgoAAAANS..."

    Это поле декодирует base64 строку и сохраняет как файл.
    """

    def to_internal_value(self, data):
        """
        Преобразует base64 строку в файл изображения.

        Args:
            data: Строка в формате "data:image/...;base64,..."

        Returns:
            ContentFile с изображением

        Raises:
            ValidationError: Если формат данных неверный
        """
        # Если данные уже являются файлом, используем стандартную обработку
        if isinstance(data, str) and data.startswith("data:image"):
            # Формат: data:image/jpeg;base64,/9j/4AAQSkZJRg...
            try:
                # Разделяем на метаданные и данные
                format_info, imgstr = data.split(";base64,")

                # Получаем расширение файла из MIME типа
                # format_info = "data:image/jpeg"
                ext = format_info.split("/")[-1]

                # Декодируем base64 в байты
                decoded_data = base64.b64decode(imgstr)

                # Создаём уникальное имя файла
                file_name = f"{uuid.uuid4()}.{ext}"

                # Создаём ContentFile для Django
                data = ContentFile(decoded_data, name=file_name)

            except (ValueError, TypeError) as e:
                raise serializers.ValidationError(
                    "Неверный формат изображения. "
                    "Ожидается формат: data:image/<type>;base64,<data>"
                ) from e

        # Используем стандартную валидацию ImageField
        return super().to_internal_value(data)
