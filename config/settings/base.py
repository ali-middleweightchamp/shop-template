"""
Базовые настройки Django. Общие для dev и prod.
Значения читаются из окружения через django-environ (см. .env.example).
"""
from pathlib import Path

import environ

# BASE_DIR указывает на корень проекта (там, где manage.py)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DEBUG=(bool, False),
)
# Читаем .env, если он есть (в проде переменные приходят из окружения контейнера)
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY", default="dev-insecure-change-me")
DEBUG = env("DEBUG")

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

# Приложения
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "django.contrib.sites",
]

THIRD_PARTY_APPS = [
    "easy_thumbnails",
]

LOCAL_APPS = [
    "apps.shopsettings",
    "apps.catalog",
    "apps.importer",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # whitenoise отдаёт статику без nginx (удобно для dev и как fallback)
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    # LocaleMiddleware — двуязычность ru/uz, ставится после Session, до Common
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.template.context_processors.i18n",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                # Настройки магазина доступны во всех шаблонах как `shop`
                "apps.shopsettings.context_processors.shop_settings",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# База данных — PostgreSQL, параметры из DATABASE_URL
DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default="postgres://postgres:postgres@db:5432/shop",
    ),
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Локализация: язык по умолчанию — русский, доступен узбекский (латиница)
LANGUAGE_CODE = "ru"
LANGUAGES = [
    ("ru", "Русский"),
    ("uz", "O‘zbekcha"),
]
LOCALE_PATHS = [BASE_DIR / "locale"]

TIME_ZONE = "Asia/Tashkent"
USE_I18N = True
USE_TZ = True

# Статика
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static" / "dist"]
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Медиа (загружаемые картинки товаров)
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SITE_ID = 1

# easy-thumbnails: превью для списков товаров, оригиналы не отдаём
THUMBNAIL_ALIASES = {
    "": {
        "card": {"size": (400, 400), "crop": "smart"},
        "thumb": {"size": (120, 120), "crop": "smart"},
        "detail": {"size": (800, 800), "crop": False},
    },
}
