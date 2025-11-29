"""
Management команда для загрузки ингредиентов из JSON или CSV файла.

Использование:
    python manage.py load_ingredients
    python manage.py load_ingredients --file data/ingredients.csv
"""

import csv
import json
import os
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from recipes.models import Ingredient


class Command(BaseCommand):
    """
    Команда для загрузки ингредиентов в базу данных.

    Поддерживает форматы JSON и CSV.
    """

    help = "Загружает ингредиенты из JSON или CSV файла в базу данных"

    def add_arguments(self, parser):
        """Добавляет аргументы командной строки."""
        parser.add_argument(
            "--file",
            type=str,
            default=None,
            help="Путь к файлу с ингредиентами (JSON или CSV). По умолчанию: data/ingredients.json",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Очистить таблицу ингредиентов перед загрузкой",
        )

    def handle(self, *args, **options):
        """Основная логика команды."""
        # Определяем путь к файлу
        file_path = options.get("file")
        if not file_path:
            # Путь по умолчанию - /app/data/ingredients.json в контейнере
            file_path = "/app/data/ingredients.json"

        # Проверяем существование файла
        if not os.path.exists(file_path):
            raise CommandError(f"Файл не найден: {file_path}")

        # Очистка таблицы если указан флаг
        if options.get("clear"):
            count = Ingredient.objects.count()
            Ingredient.objects.all().delete()
            self.stdout.write(
                self.style.WARNING(f"Удалено {count} ингредиентов из базы данных")
            )

        # Определяем формат файла
        file_extension = os.path.splitext(file_path)[1].lower()

        if file_extension == ".json":
            self._load_from_json(file_path)
        elif file_extension == ".csv":
            self._load_from_csv(file_path)
        else:
            raise CommandError(
                f"Неподдерживаемый формат файла: {file_extension}. "
                "Поддерживаются только JSON и CSV."
            )

    def _load_from_json(self, file_path):
        """
        Загружает ингредиенты из JSON файла.

        Ожидаемый формат:
        [
            {"name": "название", "measurement_unit": "единица"},
            ...
        ]
        """
        self.stdout.write(f"Загрузка ингредиентов из JSON файла: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise CommandError(f"Ошибка чтения JSON файла: {e}")
        except Exception as e:
            raise CommandError(f"Ошибка открытия файла: {e}")

        if not isinstance(data, list):
            raise CommandError("JSON файл должен содержать список ингредиентов")

        # Подготовка списка для bulk_create
        ingredients_to_create = []
        created_count = 0
        skipped_count = 0

        for index, item in enumerate(data, start=1):
            if not isinstance(item, dict):
                self.stdout.write(
                    self.style.WARNING(
                        f"Строка {index}: пропущена (неверный формат данных)"
                    )
                )
                skipped_count += 1
                continue

            name = item.get("name")
            measurement_unit = item.get("measurement_unit")

            if not name or not measurement_unit:
                self.stdout.write(
                    self.style.WARNING(
                        f"Строка {index}: пропущена (отсутствуют обязательные поля)"
                    )
                )
                skipped_count += 1
                continue

            # Проверка на существование (для избежания дубликатов)
            if Ingredient.objects.filter(
                name=name, measurement_unit=measurement_unit
            ).exists():
                skipped_count += 1
                continue

            ingredients_to_create.append(
                Ingredient(name=name, measurement_unit=measurement_unit)
            )
            created_count += 1

            # Батчевое создание каждые 500 записей для оптимизации
            if len(ingredients_to_create) >= 500:
                Ingredient.objects.bulk_create(ingredients_to_create)
                self.stdout.write(f"Обработано {index} записей...")
                ingredients_to_create = []

        # Создаём оставшиеся записи
        if ingredients_to_create:
            Ingredient.objects.bulk_create(ingredients_to_create)

        self.stdout.write(
            self.style.SUCCESS(
                f"\nУспешно загружено {created_count} ингредиентов\n"
                f"Пропущено (дубликатов или ошибок): {skipped_count}"
            )
        )

    def _load_from_csv(self, file_path):
        """
        Загружает ингредиенты из CSV файла.

        Ожидаемый формат:
        название,единица измерения
        """
        self.stdout.write(f"Загрузка ингредиентов из CSV файла: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)

                ingredients_to_create = []
                created_count = 0
                skipped_count = 0

                for index, row in enumerate(reader, start=1):
                    if len(row) < 2:
                        self.stdout.write(
                            self.style.WARNING(
                                f"Строка {index}: пропущена (недостаточно данных)"
                            )
                        )
                        skipped_count += 1
                        continue

                    name = row[0].strip()
                    measurement_unit = row[1].strip()

                    if not name or not measurement_unit:
                        self.stdout.write(
                            self.style.WARNING(
                                f"Строка {index}: пропущена (пустые поля)"
                            )
                        )
                        skipped_count += 1
                        continue

                    # Проверка на существование
                    if Ingredient.objects.filter(
                        name=name, measurement_unit=measurement_unit
                    ).exists():
                        skipped_count += 1
                        continue

                    ingredients_to_create.append(
                        Ingredient(name=name, measurement_unit=measurement_unit)
                    )
                    created_count += 1

                    # Батчевое создание каждые 500 записей
                    if len(ingredients_to_create) >= 500:
                        Ingredient.objects.bulk_create(ingredients_to_create)
                        self.stdout.write(f"Обработано {index} записей...")
                        ingredients_to_create = []

                # Создаём оставшиеся записи
                if ingredients_to_create:
                    Ingredient.objects.bulk_create(ingredients_to_create)

        except Exception as e:
            raise CommandError(f"Ошибка чтения CSV файла: {e}")

        self.stdout.write(
            self.style.SUCCESS(
                f"\nУспешно загружено {created_count} ингредиентов\n"
                f"Пропущено (дубликатов или ошибок): {skipped_count}"
            )
        )
