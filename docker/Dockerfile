# syntax=docker/dockerfile:1

# --- Стадия 1: сборка CSS через Tailwind CLI ---
FROM node:20-slim AS css
WORKDIR /build
COPY package.json package-lock.json* ./
RUN npm install
# Конфиг и исходники нужны для tree-shaking классов
COPY tailwind.config.js postcss.config.js ./
COPY static/src ./static/src
COPY templates ./templates
COPY apps ./apps
RUN npx tailwindcss -i ./static/src/input.css -o ./static/dist/css/app.css --minify

# --- Стадия 2: приложение Python ---
FROM python:3.12-slim AS app

# Не писать .pyc, не буферизовать stdout (логи сразу видны)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Системные зависимости: libpq для psycopg, jpeg/zlib для Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
        libjpeg62-turbo \
        zlib1g \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Зависимости — отдельным слоем для кэша
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Код приложения
COPY . .

# Забираем собранный CSS из первой стадии
COPY --from=css /build/static/dist ./static/dist

# collectstatic на этапе сборки образа (нужен манифест whitenoise)
ENV DJANGO_SETTINGS_MODULE=config.settings.prod \
    SECRET_KEY=build-time-dummy \
    ALLOWED_HOSTS=localhost \
    DATABASE_URL=postgres://u:p@db:5432/db
RUN python manage.py collectstatic --noinput

# Пользователь без root-прав
RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
