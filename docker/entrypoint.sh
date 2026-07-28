#!/bin/sh
# Запускается при старте контейнера web: миграции + сбор статики в общий том,
# затем передаёт управление основной команде (gunicorn).
set -e

echo "Применяю миграции..."
python manage.py migrate --noinput

echo "Собираю статику..."
python manage.py collectstatic --noinput

exec "$@"
