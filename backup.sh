#!/bin/sh
# Бэкап базы (Postgres) и медиа (загруженные фото) в папку backups/.
# Запуск на сервере:  ./backup.sh   (можно повесить в cron, напр. раз в сутки)
set -e
cd "$(dirname "$0")"

# Подхватываем POSTGRES_* из .env
set -a
[ -f .env ] && . ./.env
set +a

STAMP=$(date +%Y-%m-%d_%H%M)
mkdir -p backups

echo "→ Дамп базы данных..."
docker compose exec -T db pg_dump -U "${POSTGRES_USER:-postgres}" "${POSTGRES_DB:-shop}" \
  | gzip > "backups/db_$STAMP.sql.gz"

echo "→ Архив медиа (фото товаров и категорий)..."
docker compose exec -T web tar czf - -C /app/media . > "backups/media_$STAMP.tgz"

# Чистим бэкапы старше 30 дней
find backups -name 'db_*.sql.gz' -mtime +30 -delete 2>/dev/null || true
find backups -name 'media_*.tgz' -mtime +30 -delete 2>/dev/null || true

echo "✓ Бэкап готов: backups/db_$STAMP.sql.gz + backups/media_$STAMP.tgz"
