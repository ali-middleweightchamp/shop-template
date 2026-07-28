"""Настройки для локальной разработки."""
from .base import *  # noqa: F401,F403

DEBUG = True

ALLOWED_HOSTS = ["*"]

# В dev письма и отладка — без лишней возни
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Django Debug: показываем SQL при необходимости через runserver
INTERNAL_IPS = ["127.0.0.1"]
