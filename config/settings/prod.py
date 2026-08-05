"""
Продакшн-настройки. Безопасность включена полностью.
Все секреты и хосты приходят из окружения — ничего не хардкодим.
"""
from .base import *  # noqa: F401,F403
from .base import env

DEBUG = False

# ALLOWED_HOSTS обязателен в проде — задаётся через окружение
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")

CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

# Файловый кэш общий для всех воркеров gunicorn (в одном контейнере они делят
# ФС). LocMemCache у каждого воркера свой → сброс кэша настроек не долетал до
# остальных, и изменения в админке «не применялись» до истечения TTL.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": "/tmp/django_cache",
    }
}

# --- Безопасность ---
# Редирект на HTTPS. За nginx учитываем заголовок X-Forwarded-Proto.
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Secure-cookie работают только по HTTPS. Пока сайт по HTTP (без домена),
# держим их выключенными вместе с SSL-редиректом — иначе CSRF-cookie не
# сохраняется и вход в панель падает с 403.
SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", default=SECURE_SSL_REDIRECT)
CSRF_COOKIE_SECURE = env.bool("CSRF_COOKIE_SECURE", default=SECURE_SSL_REDIRECT)

# HSTS — заставляем браузер ходить только по HTTPS (только когда включён HTTPS)
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=31536000 if SECURE_SSL_REDIRECT else 0)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# Логирование ошибок в stdout контейнера
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}
