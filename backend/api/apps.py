"""
Configuration for api application.
"""

from django.apps import AppConfig


class ApiConfig(AppConfig):
    """Конфигурация приложения api."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "api"
    verbose_name = "API"
