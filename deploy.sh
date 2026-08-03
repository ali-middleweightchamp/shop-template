#!/bin/sh
# Обновление боевого сайта: подтянуть код → пересобрать → поднять → миграции.
# Запуск на сервере:  ./deploy.sh
set -e
cd "$(dirname "$0")"

echo "→ Обновляю код из git..."
git pull --ff-only

echo "→ Пересобираю и поднимаю контейнеры..."
docker compose up -d --build

echo "→ Применяю миграции..."
docker compose exec -T web python manage.py migrate --noinput

echo "✓ Готово. Сайт обновлён."
