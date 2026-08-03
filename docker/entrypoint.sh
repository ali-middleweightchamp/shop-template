#!/bin/sh
# Запускается при старте контейнера web: миграции + сбор статики в общий том,
# затем передаёт управление основной команде (gunicorn).
set -e

echo "Применяю миграции..."
python manage.py migrate --noinput

echo "Собираю статику..."
python manage.py collectstatic --noinput

# Создаём/обновляем владельца-сотрудника из OWNER_* (если заданы в .env).
# Идемпотентно — безопасно при каждом старте.
echo "Проверяю владельца магазина..."
python manage.py ensure_owner

exec "$@"
